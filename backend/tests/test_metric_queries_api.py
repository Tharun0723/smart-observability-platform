from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.core.config import settings
from app.models import Tenant, Metric
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


def create_tenant_and_collector(db_session, name):
    tenant = Tenant(name=name)
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    collector, secret = provision_collector(
        db_session,
        tenant.id,
        f"{name} Collector",
    )

    return tenant, collector


def add_metric(
    db_session,
    tenant_id,
    collector_id,
    metric_name,
    value,
    recorded_at,
):
    metric = Metric(
        tenant_id=tenant_id,
        collector_id=collector_id,
        metric_name=metric_name,
        value=value,
        unit="percent",
        recorded_at=recorded_at,
    )

    db_session.add(metric)
    db_session.commit()
    db_session.refresh(metric)

    return metric


def test_metric_history_is_tenant_separated(admin_client, db_session):
    tenant_a, collector_a = create_tenant_and_collector(
        db_session, "Company A"
    )

    tenant_b, collector_b = create_tenant_and_collector(
        db_session, "Company B"
    )

    timestamp = datetime(2026, 11, 20, 17, 30, tzinfo=timezone.utc)

    add_metric(
        db_session, tenant_a.id, collector_a.id,
        "cpu_usage_percent", 45, timestamp
    )

    add_metric(
        db_session, tenant_b.id, collector_b.id,
        "cpu_usage_percent", 90, timestamp
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant_a.id}/metrics",
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["tenant_id"] == tenant_a.id
    assert response.json()[0]["value"] == 45


def test_metric_summary_calculations(admin_client, db_session):
    tenant, collector = create_tenant_and_collector(
        db_session, "Summary Company"
    )

    add_metric(
        db_session, tenant.id, collector.id,
        "cpu_usage_percent", 20,
        datetime(2026, 11, 20, 17, 0, tzinfo=timezone.utc)
    )

    add_metric(
        db_session, tenant.id, collector.id,
        "cpu_usage_percent", 40,
        datetime(2026, 11, 20, 18, 0, tzinfo=timezone.utc)
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/metrics/summary",
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 200

    summary = response.json()["metrics"][0]

    assert summary["metric_name"] == "cpu_usage_percent"
    assert summary["count"] == 2
    assert summary["average"] == 30
    assert summary["minimum"] == 20
    assert summary["maximum"] == 40


def test_metric_history_filters_by_name(admin_client, db_session):
    tenant, collector = create_tenant_and_collector(
        db_session, "Filter Company"
    )

    timestamp = datetime(2026, 11, 20, 17, 30, tzinfo=timezone.utc)

    add_metric(
        db_session, tenant.id, collector.id,
        "cpu_usage_percent", 50, timestamp
    )

    add_metric(
        db_session, tenant.id, collector.id,
        "memory_usage_percent", 70, timestamp
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/metrics",
        params={"metric_name": "cpu_usage_percent"},
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["metric_name"] == "cpu_usage_percent"


def test_metric_history_rejects_missing_admin_key(admin_client, db_session):
    tenant, _ = create_tenant_and_collector(
        db_session, "Protected Company"
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/metrics"
    )

    assert response.status_code == 401


def test_metric_history_rejects_unknown_tenant(admin_client):
    response = admin_client.get(
        "/api/v1/admin/tenants/9999/metrics",
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 404