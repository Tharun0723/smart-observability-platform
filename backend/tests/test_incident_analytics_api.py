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
    recommendation="Investigate the affected resource",
    correlation_key="server-01",
    occurrence_count=1,
):
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    incident = Incident(
        tenant_id=tenant_id,
        fingerprint=fingerprint,
        title=f"Test incident {fingerprint}",
        description="Incident analytics test",
        source="aiops",
        severity=severity,
        priority=priority,
        status=status,
        affected_resource="server-01",
        correlation_key=correlation_key,
        recommendation=recommendation,
        first_seen_at=now,
        last_seen_at=now,
        occurrence_count=occurrence_count,
    )

    db_session.add(incident)
    db_session.commit()
    db_session.refresh(incident)

    return incident


def headers():
    return {"X-Admin-API-Key": "test-admin-key"}


def test_update_incident_recommendation(admin_client, db_session):
    tenant = create_tenant(
        db_session,
        "Recommendation Test Company",
    )

    incident = create_incident(
        db_session,
        tenant.id,
        "recommendation-001",
    )

    response = admin_client.patch(
        f"/api/v1/admin/tenants/{tenant.id}/incidents/{incident.id}/recommendation",
        headers=headers(),
        json={
            "recommendation": "Restart the affected application service"
        },
    )

    assert response.status_code == 200
    assert response.json()["recommendation"] == (
        "Restart the affected application service"
    )


def test_clear_incident_recommendation(admin_client, db_session):
    tenant = create_tenant(
        db_session,
        "Clear Recommendation Company",
    )

    incident = create_incident(
        db_session,
        tenant.id,
        "recommendation-002",
    )

    response = admin_client.patch(
        f"/api/v1/admin/tenants/{tenant.id}/incidents/{incident.id}/recommendation",
        headers=headers(),
        json={"recommendation": None},
    )

    assert response.status_code == 200
    assert response.json()["recommendation"] is None


def test_recommendation_update_cannot_cross_tenants(
    admin_client,
    db_session,
):
    tenant_a = create_tenant(db_session, "Recommendation Company A")
    tenant_b = create_tenant(db_session, "Recommendation Company B")

    incident = create_incident(
        db_session,
        tenant_a.id,
        "private-recommendation-001",
    )

    response = admin_client.patch(
        f"/api/v1/admin/tenants/{tenant_b.id}/incidents/{incident.id}/recommendation",
        headers=headers(),
        json={"recommendation": "Unauthorized change"},
    )

    assert response.status_code == 404

    db_session.refresh(incident)
    assert incident.recommendation == "Investigate the affected resource"


def test_incident_analytics_counts_correctly(admin_client, db_session):
    tenant = create_tenant(
        db_session,
        "Incident Analytics Company",
    )

    create_incident(
        db_session,
        tenant.id,
        "analytics-001",
        severity="high",
        priority="high",
        status="open",
        occurrence_count=3,
        correlation_key="server-01",
    )

    create_incident(
        db_session,
        tenant.id,
        "analytics-002",
        severity="critical",
        priority="critical",
        status="acknowledged",
        correlation_key="server-01",
    )

    create_incident(
        db_session,
        tenant.id,
        "analytics-003",
        severity="medium",
        priority="low",
        status="resolved",
        correlation_key=None,
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/incidents/summary",
        headers=headers(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tenant_id"] == tenant.id
    assert data["total_incidents"] == 3
    assert data["repeated_incidents"] == 1
    assert data["correlated_incidents"] == 2

    severity = {
        item["severity"]: item["count"]
        for item in data["by_severity"]
    }

    assert severity["high"] == 1
    assert severity["critical"] == 1
    assert severity["medium"] == 1

    statuses = {
        item["status"]: item["count"]
        for item in data["by_status"]
    }

    assert statuses["open"] == 1
    assert statuses["acknowledged"] == 1
    assert statuses["resolved"] == 1


def test_incident_analytics_is_tenant_separated(
    admin_client,
    db_session,
):
    tenant_a = create_tenant(db_session, "Analytics Company A")
    tenant_b = create_tenant(db_session, "Analytics Company B")

    create_incident(
        db_session,
        tenant_a.id,
        "analytics-A",
        severity="low",
    )

    create_incident(
        db_session,
        tenant_b.id,
        "analytics-B1",
        severity="critical",
    )

    create_incident(
        db_session,
        tenant_b.id,
        "analytics-B2",
        severity="critical",
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant_a.id}/incidents/summary",
        headers=headers(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_incidents"] == 1
    assert data["by_severity"][-1]["count"] == 0


def test_incident_analytics_requires_admin_key(
    admin_client,
    db_session,
):
    tenant = create_tenant(
        db_session,
        "Protected Analytics Company",
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/incidents/summary"
    )

    assert response.status_code == 401


def test_incident_analytics_rejects_unknown_tenant(admin_client):
    response = admin_client.get(
        "/api/v1/admin/tenants/9999/incidents/summary",
        headers=headers(),
    )

    assert response.status_code == 404