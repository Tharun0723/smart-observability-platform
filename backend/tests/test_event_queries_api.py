from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.core.config import settings
from app.models import Tenant, Event
from app.services.collector_auth import provision_collector


@pytest.fixture
def admin_client(db_session, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "test-admin-key")

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)


def create_test_collector(db_session, company_name):
    tenant = Tenant(name=company_name)
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    collector, secret = provision_collector(
        db_session,
        tenant.id,
        f"{company_name} Collector",
    )

    return tenant, collector


def add_event(
    db_session,
    tenant_id,
    collector_id,
    event_type,
    severity,
    title,
    occurred_at,
):
    event = Event(
        tenant_id=tenant_id,
        collector_id=collector_id,
        event_type=event_type,
        severity=severity,
        title=title,
        source="test_source",
        summary="Test event metadata",
        occurred_at=occurred_at,
    )

    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    return event


def test_event_history_is_tenant_separated(admin_client, db_session):
    tenant_a, collector_a = create_test_collector(
        db_session, "Event Company A"
    )

    tenant_b, collector_b = create_test_collector(
        db_session, "Event Company B"
    )

    timestamp = datetime(
        2026, 11, 21, 1, 0, tzinfo=timezone.utc
    )

    add_event(
        db_session,
        tenant_a.id,
        collector_a.id,
        "security_alert",
        "high",
        "Company A Alert",
        timestamp,
    )

    add_event(
        db_session,
        tenant_b.id,
        collector_b.id,
        "security_alert",
        "critical",
        "Company B Alert",
        timestamp,
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant_a.id}/events",
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["tenant_id"] == tenant_a.id
    assert response.json()[0]["title"] == "Company A Alert"


def test_event_history_filters_by_severity(admin_client, db_session):
    tenant, collector = create_test_collector(
        db_session, "Severity Test Company"
    )

    timestamp = datetime(
        2026, 11, 21, 1, 0, tzinfo=timezone.utc
    )

    add_event(
        db_session, tenant.id, collector.id,
        "security_alert", "high", "High Alert", timestamp
    )

    add_event(
        db_session, tenant.id, collector.id,
        "security_alert", "low", "Low Alert", timestamp
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/events",
        params={"severity": "high"},
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["severity"] == "high"


def test_event_history_filters_by_type(admin_client, db_session):
    tenant, collector = create_test_collector(
        db_session, "Event Type Company"
    )

    timestamp = datetime(
        2026, 11, 21, 1, 0, tzinfo=timezone.utc
    )

    add_event(
        db_session, tenant.id, collector.id,
        "security_alert", "high", "Security Alert", timestamp
    )

    add_event(
        db_session, tenant.id, collector.id,
        "application_error", "medium", "Application Error", timestamp
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/events",
        params={"event_type": "application_error"},
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["event_type"] == "application_error"


def test_event_summary_counts_by_severity(admin_client, db_session):
    tenant, collector = create_test_collector(
        db_session, "Event Summary Company"
    )

    timestamp = datetime(
        2026, 11, 21, 1, 0, tzinfo=timezone.utc
    )

    add_event(
        db_session, tenant.id, collector.id,
        "security_alert", "high", "Alert One", timestamp
    )

    add_event(
        db_session, tenant.id, collector.id,
        "security_alert", "high", "Alert Two", timestamp
    )

    add_event(
        db_session, tenant.id, collector.id,
        "application_error", "medium", "App Error", timestamp
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/events/summary",
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tenant_id"] == tenant.id
    assert data["total_events"] == 3

    counts = {
        item["severity"]: item["count"]
        for item in data["by_severity"]
    }

    assert counts["high"] == 2
    assert counts["medium"] == 1


def test_event_history_requires_admin_key(admin_client, db_session):
    tenant, _ = create_test_collector(
        db_session, "Protected Event Company"
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/events"
    )

    assert response.status_code == 401


def test_event_history_rejects_unknown_tenant(admin_client):
    response = admin_client.get(
        "/api/v1/admin/tenants/9999/events",
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 404