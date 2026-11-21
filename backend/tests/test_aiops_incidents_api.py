import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db.database import get_db
from app.models import Tenant, Incident


@pytest.fixture
def aiops_client(db_session, monkeypatch):
    # Use a fake test key. Never use the real private key in tests.
    monkeypatch.setattr(
        settings,
        "aiops_api_key",
        "test-aiops-integration-key",
    )

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)


def create_tenant(db_session, name="AIOps Test Company"):
    tenant = Tenant(name=name)
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def incident_payload(fingerprint="cpu-high-server-01"):
    return {
        "fingerprint": fingerprint,
        "title": "High CPU usage detected",
        "description": "CPU usage remained above the configured threshold",
        "source": "aiops_anomaly_engine",
        "severity": "high",
        "priority": "high",
        "affected_resource": "server-01",
        "correlation_key": "cpu-server-01",
        "recommendation": "Investigate processes consuming CPU",
        "occurred_at": "2026-11-21T01:30:00Z",
    }


def aiops_headers():
    return {
        "X-AIOps-API-Key": "test-aiops-integration-key"
    }


def test_aiops_creates_new_incident(aiops_client, db_session):
    tenant = create_tenant(db_session)

    response = aiops_client.post(
        f"/api/v1/aiops/tenants/{tenant.id}/incidents",
        headers=aiops_headers(),
        json=incident_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["created"] is True
    assert data["incident"]["tenant_id"] == tenant.id
    assert data["incident"]["fingerprint"] == "cpu-high-server-01"
    assert data["incident"]["status"] == "open"
    assert data["incident"]["occurrence_count"] == 1

    saved_incident = db_session.query(Incident).filter(
        Incident.tenant_id == tenant.id
    ).first()

    assert saved_incident is not None


def test_aiops_updates_duplicate_incident(
    aiops_client,
    db_session,
):
    tenant = create_tenant(db_session)

    url = f"/api/v1/aiops/tenants/{tenant.id}/incidents"

    first_response = aiops_client.post(
        url,
        headers=aiops_headers(),
        json=incident_payload(),
    )

    assert first_response.status_code == 201

    first_id = first_response.json()["incident"]["id"]

    # Simulate an incident that an operator has already resolved.
    incident = db_session.query(Incident).filter(
        Incident.id == first_id
    ).first()

    incident.status = "resolved"
    db_session.commit()

    # The same fingerprint arrives again.
    repeated_payload = incident_payload()
    repeated_payload["severity"] = "critical"
    repeated_payload["priority"] = "critical"
    repeated_payload["occurred_at"] = "2026-11-21T02:00:00Z"

    second_response = aiops_client.post(
        url,
        headers=aiops_headers(),
        json=repeated_payload,
    )

    assert second_response.status_code == 201

    data = second_response.json()

    assert data["created"] is False
    assert data["incident"]["id"] == first_id
    assert data["incident"]["occurrence_count"] == 2
    assert data["incident"]["status"] == "open"
    assert data["incident"]["severity"] == "critical"


def test_aiops_rejects_missing_api_key(aiops_client, db_session):
    tenant = create_tenant(db_session)

    response = aiops_client.post(
        f"/api/v1/aiops/tenants/{tenant.id}/incidents",
        json=incident_payload(),
    )

    assert response.status_code == 401


def test_aiops_rejects_invalid_api_key(aiops_client, db_session):
    tenant = create_tenant(db_session)

    response = aiops_client.post(
        f"/api/v1/aiops/tenants/{tenant.id}/incidents",
        headers={"X-AIOps-API-Key": "wrong-key"},
        json=incident_payload(),
    )

    assert response.status_code == 401


def test_aiops_rejects_unknown_tenant(aiops_client):
    response = aiops_client.post(
        "/api/v1/aiops/tenants/9999/incidents",
        headers=aiops_headers(),
        json=incident_payload(),
    )

    assert response.status_code == 404


def test_same_fingerprint_can_exist_for_different_tenants(
    aiops_client,
    db_session,
):
    tenant_a = create_tenant(db_session, "Company A")
    tenant_b = create_tenant(db_session, "Company B")

    payload = incident_payload("shared-fingerprint")

    response_a = aiops_client.post(
        f"/api/v1/aiops/tenants/{tenant_a.id}/incidents",
        headers=aiops_headers(),
        json=payload,
    )

    response_b = aiops_client.post(
        f"/api/v1/aiops/tenants/{tenant_b.id}/incidents",
        headers=aiops_headers(),
        json=payload,
    )

    assert response_a.status_code == 201
    assert response_b.status_code == 201

    assert response_a.json()["created"] is True
    assert response_b.json()["created"] is True

    assert (
        response_a.json()["incident"]["id"]
        != response_b.json()["incident"]["id"]
    )