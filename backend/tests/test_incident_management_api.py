from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.core.config import settings
from app.models import Tenant, Incident


@pytest.fixture
def admin_client(db_session, monkeypatch):
    monkeypatch.setattr(
        settings,
        "admin_api_key",
        "test-admin-key",
    )

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)


def create_tenant(db_session, name):
    tenant = Tenant(name=name)
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def create_incident(
    db_session,
    tenant_id,
    fingerprint,
    severity="high",
    priority="high",
    status="open",
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    incident = Incident(
        tenant_id=tenant_id,
        fingerprint=fingerprint,
        title="High CPU usage detected",
        description="CPU usage exceeded the threshold",
        source="aiops_anomaly_engine",
        severity=severity,
        priority=priority,
        status=status,
        affected_resource="server-01",
        correlation_key="cpu-server-01",
        recommendation="Investigate CPU-consuming processes",
        first_seen_at=now,
        last_seen_at=now,
        occurrence_count=1,
    )

    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    return incident


def admin_headers():
    return {"X-Admin-API-Key": "test-admin-key"}


def test_list_tenant_incidents(admin_client, db_session):
    tenant = create_tenant(db_session, "Incident List Company")

    create_incident(db_session, tenant.id, "incident-001")
    create_incident(
        db_session,
        tenant.id,
        "incident-002",
        severity="critical",
        priority="critical",
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/incidents",
        headers=admin_headers(),
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_filter_incidents_by_severity(admin_client, db_session):
    tenant = create_tenant(db_session, "Severity Filter Company")

    create_incident(
        db_session, tenant.id, "high-001", severity="high"
    )
    create_incident(
        db_session, tenant.id, "critical-001", severity="critical"
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/incidents",
        params={"severity": "critical"},
        headers=admin_headers(),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["severity"] == "critical"


def test_filter_incidents_by_status(admin_client, db_session):
    tenant = create_tenant(db_session, "Status Filter Company")

    create_incident(
        db_session, tenant.id, "open-001", status="open"
    )
    create_incident(
        db_session, tenant.id, "resolved-001", status="resolved"
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/incidents",
        params={"status": "resolved"},
        headers=admin_headers(),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "resolved"


def test_update_incident_status(admin_client, db_session):
    tenant = create_tenant(db_session, "Status Update Company")

    incident = create_incident(
        db_session, tenant.id, "status-update-001"
    )

    response = admin_client.patch(
        f"/api/v1/admin/tenants/{tenant.id}/incidents/{incident.id}/status",
        headers=admin_headers(),
        json={"status": "acknowledged"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "acknowledged"


def test_incident_cannot_be_updated_through_another_tenant(
    admin_client,
    db_session,
):
    tenant_a = create_tenant(db_session, "Incident Company A")
    tenant_b = create_tenant(db_session, "Incident Company B")

    incident = create_incident(
        db_session,
        tenant_a.id,
        "private-incident-001",
    )

    response = admin_client.patch(
        f"/api/v1/admin/tenants/{tenant_b.id}/incidents/{incident.id}/status",
        headers=admin_headers(),
        json={"status": "resolved"},
    )

    assert response.status_code == 404

    db_session.refresh(incident)
    assert incident.status == "open"


def test_incident_management_requires_admin_key(
    admin_client,
    db_session,
):
    tenant = create_tenant(db_session, "Protected Incident Company")

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/incidents"
    )

    assert response.status_code == 401


def test_incident_listing_rejects_unknown_tenant(admin_client):
    response = admin_client.get(
        "/api/v1/admin/tenants/9999/incidents",
        headers=admin_headers(),
    )

    assert response.status_code == 404