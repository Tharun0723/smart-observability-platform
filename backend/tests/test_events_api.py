import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.models import Tenant, Event
from app.services.collector_auth import provision_collector


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)


def create_test_collector(db_session):
    tenant = Tenant(name="Event Test Company")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    collector, secret = provision_collector(
        db_session,
        tenant.id,
        "Event Test Collector",
    )

    return tenant, collector, secret


def test_ingest_valid_events(client, db_session):
    tenant, collector, secret = create_test_collector(db_session)

    response = client.post(
        "/api/v1/events",
        headers={"X-Collector-Secret": secret},
        json={
            "events": [
                {
                    "event_type": "security_alert",
                    "severity": "high",
                    "source": "windows_firewall",
                    "title": "Suspicious connection detected",
                    "summary": "Repeated connection attempts detected",
                    "occurred_at": "2026-11-21T01:00:00Z",
                },
                {
                    "event_type": "application_error",
                    "severity": "medium",
                    "source": "payment_service",
                    "title": "Application request failed",
                    "summary": "An application request returned an error",
                    "occurred_at": "2026-11-21T01:05:00Z",
                },
            ]
        },
    )

    assert response.status_code == 201
    assert response.json()["accepted"] == 2
    assert response.json()["collector_id"] == collector.id
    assert response.json()["tenant_id"] == tenant.id

    saved_events = db_session.query(Event).filter(
        Event.collector_id == collector.id
    ).all()

    assert len(saved_events) == 2
    assert all(event.tenant_id == tenant.id for event in saved_events)


def test_event_ingestion_does_not_trust_request_tenant_id(
    client,
    db_session,
):
    tenant, collector, secret = create_test_collector(db_session)

    response = client.post(
        "/api/v1/events",
        headers={"X-Collector-Secret": secret},
        json={
            "tenant_id": 9999,
            "events": [
                {
                    "event_type": "security_alert",
                    "severity": "high",
                    "title": "Test security event",
                    "occurred_at": "2026-11-21T01:00:00Z",
                }
            ],
        },
    )

    assert response.status_code == 201

    saved_event = db_session.query(Event).first()

    assert saved_event.tenant_id == tenant.id
    assert saved_event.tenant_id != 9999


def test_event_ingestion_rejects_missing_secret(client):
    response = client.post(
        "/api/v1/events",
        json={
            "events": [
                {
                    "event_type": "security_alert",
                    "severity": "high",
                    "title": "Test event",
                    "occurred_at": "2026-11-21T01:00:00Z",
                }
            ]
        },
    )

    assert response.status_code == 401


def test_event_ingestion_rejects_invalid_timestamp(
    client,
    db_session,
):
    _, _, secret = create_test_collector(db_session)

    response = client.post(
        "/api/v1/events",
        headers={"X-Collector-Secret": secret},
        json={
            "events": [
                {
                    "event_type": "security_alert",
                    "severity": "high",
                    "title": "Test event",
                    "occurred_at": "2026-11-21T01:00:00",
                }
            ]
        },
    )

    assert response.status_code == 422


def test_event_ingestion_rejects_invalid_severity(
    client,
    db_session,
):
    _, _, secret = create_test_collector(db_session)

    response = client.post(
        "/api/v1/events",
        headers={"X-Collector-Secret": secret},
        json={
            "events": [
                {
                    "event_type": "security_alert",
                    "severity": "extreme",
                    "title": "Test event",
                    "occurred_at": "2026-11-21T01:00:00Z",
                }
            ]
        },
    )

    assert response.status_code == 422