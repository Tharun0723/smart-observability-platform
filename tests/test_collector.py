
import pytest
import uuid

from collector.processing.validator import validate_metrics
from collector.privacy.privacy_filter import (
    filter_approved_metrics,
    redact_sensitive_text
)
from collector.storage.sqlite_buffer import (
    initialize_database,
    store_event,
    get_pending_events,
    mark_event_sent,
    increment_retry
)
from collector.transport.sender import validate_outbound_payload


# ==========================================
# 1. METRIC VALIDATION TESTS
# ==========================================

def test_valid_metrics():
    metrics = {
        "cpu_percent": 45.5,
        "memory_percent": 70.2,
        "disk_percent": 60.0
    }

    assert validate_metrics(metrics) == metrics


def test_invalid_cpu_value():
    with pytest.raises(ValueError):
        validate_metrics({"cpu_percent": 150})


def test_unapproved_field():
    with pytest.raises(ValueError):
        validate_metrics({"password": "secret123"})


# ==========================================
# 2. PRIVACY FILTER TESTS
# ==========================================

def test_privacy_filter():
    metrics = {
        "cpu_percent": 45.5,
        "password": "secret123",
        "api_key": "abc123"
    }

    result = filter_approved_metrics(metrics)

    assert "cpu_percent" in result
    assert "password" not in result
    assert "api_key" not in result


def test_secret_redaction():
    text = "password=demo123 user=test@example.com"

    result = redact_sensitive_text(text)

    assert "demo123" not in result
    assert "test@example.com" not in result
    assert "[REDACTED_SECRET]" in result
    assert "[REDACTED_EMAIL]" in result


# ==========================================
# 3. SQLITE STORAGE TESTS
# ==========================================

def test_sqlite_initialization():
    initialize_database()


def test_sqlite_store_and_retrieve():
    initialize_database()

    event_id = f"pytest-store-{uuid.uuid4()}"

    store_event(
        event_id,
        {"cpu_percent": 50}
    )

    events = get_pending_events()

    assert any(
        event["event_id"] == event_id
        for event in events
    )


def test_sqlite_duplicate_protection():
    initialize_database()

    event_id = f"pytest-duplicate-{uuid.uuid4()}"

    store_event(
        event_id,
        {"cpu_percent": 50}
    )

    store_event(
        event_id,
        {"cpu_percent": 50}
    )

    events = get_pending_events()

    matching_events = [
        event for event in events
        if event["event_id"] == event_id
    ]

    assert len(matching_events) == 1


def test_sqlite_retry_counter():
    initialize_database()

    event_id = f"pytest-retry-{uuid.uuid4()}"

    store_event(
        event_id,
        {"cpu_percent": 40}
    )

    assert increment_retry(event_id) is True

    events = get_pending_events()

    event = next(
        e for e in events
        if e["event_id"] == event_id
    )

    assert event["retry_count"] == 1


def test_sqlite_mark_event_sent():
    initialize_database()

    event_id = f"pytest-sent-{uuid.uuid4()}"

    store_event(
        event_id,
        {"cpu_percent": 30}
    )

    assert mark_event_sent(event_id) is True

    events = get_pending_events()

    assert not any(
        e["event_id"] == event_id
        for e in events
    )


# ==========================================
# 4. SECURE SENDER TESTS
# ==========================================

def test_sender_accepts_approved_metrics():
    payload = {
        "cpu_percent": 45.5,
        "memory_percent": 70.2,
        "disk_percent": 60.0
    }

    assert validate_outbound_payload(payload) == payload


def test_sender_rejects_password():
    payload = {
        "cpu_percent": 45.5,
        "password": "secret123"
    }

    with pytest.raises(ValueError):
        validate_outbound_payload(payload)


def test_sender_rejects_invalid_cpu():
    payload = {
        "cpu_percent": 150
    }

    with pytest.raises(ValueError):
        validate_outbound_payload(payload)