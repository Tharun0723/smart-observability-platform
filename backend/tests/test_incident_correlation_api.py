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
    correlation_key,
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    incident = Incident(
        tenant_id=tenant_id,
        fingerprint=fingerprint,
        title=f"Incident {fingerprint}",
        description="Correlation test",
        source="aiops",
        severity="high",
        priority="high",
        status="open",
        correlation_key=correlation_key,
        recommendation="Investigate the affected resource",
        first_seen_at=now,
        last_seen_at=now,
        occurrence_count=1,
    )

    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    return incident


def headers():
    return {"X-Admin-API-Key": "test-admin-key"}


def test_find_related_incidents(admin_client, db_session):
    tenant = create_tenant(db_session, "Correlation Company")

    first = create_incident(
        db_session, tenant.id, "incident-001", "server-01"
    )

    second = create_incident(
        db_session, tenant.id, "incident-002", "server-01"
    )

    create_incident(
        db_session, tenant.id, "incident-003", "server-02"
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/incidents/{first.id}/related",
        headers=headers(),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == second.id


def test_correlation_does_not_cross_tenants(admin_client, db_session):
    tenant_a = create_tenant(db_session, "Correlation Company A")
    tenant_b = create_tenant(db_session, "Correlation Company B")

    first = create_incident(
        db_session, tenant_a.id, "incident-A", "shared-key"
    )

    create_incident(
        db_session, tenant_b.id, "incident-B", "shared-key"
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant_a.id}/incidents/{first.id}/related",
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_incident_without_correlation_key_returns_empty_list(
    admin_client,
    db_session,
):
    tenant = create_tenant(db_session, "No Correlation Company")

    incident = create_incident(
        db_session, tenant.id, "incident-no-key", None
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/incidents/{incident.id}/related",
        headers=headers(),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_correlation_rejects_unknown_incident(admin_client):
    response = admin_client.get(
        "/api/v1/admin/tenants/9999/incidents/9999/related",
        headers=headers(),
    )

    assert response.status_code == 404