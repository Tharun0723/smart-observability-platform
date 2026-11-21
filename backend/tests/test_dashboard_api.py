from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.core.config import settings
from app.models import Tenant, Metric, Event
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


def create_test_tenant(db_session, name):
    tenant = Tenant(name=name)
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def create_test_collector(db_session, tenant_id, name, last_seen):
    collector, secret = provision_collector(
        db_session,
        tenant_id,
        name,
    )

    collector.last_seen_at = last_seen
    db_session.commit()
    db_session.refresh(collector)

    return collector


def add_test_metric(
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
    return metric


def add_test_event(
    db_session,
    tenant_id,
    collector_id,
    severity,
    title,
    occurred_at,
):
    event = Event(
        tenant_id=tenant_id,
        collector_id=collector_id,
        event_type="security_alert",
        severity=severity,
        source="dashboard_test",
        title=title,
        summary="Dashboard test event",
        occurred_at=occurred_at,
    )

    db_session.add(event)
    db_session.commit()
    return event


def test_dashboard_overview_calculates_health_and_events(
    admin_client,
    db_session,
):
    now = datetime.now(timezone.utc)

    tenant = create_test_tenant(
        db_session,
        "Dashboard Test Company",
    )

    healthy = create_test_collector(
        db_session, tenant.id, "Healthy Collector", now
    )

    warning = create_test_collector(
        db_session, tenant.id, "Warning Collector", now
    )

    critical = create_test_collector(
        db_session, tenant.id, "Critical Collector", now
    )

    offline = create_test_collector(
        db_session,
        tenant.id,
        "Offline Collector",
        now - timedelta(minutes=10),
    )

    # Healthy device: all readings below 75%.
    add_test_metric(
        db_session, tenant.id, healthy.id,
        "cpu_usage_percent", 40, now
    )
    add_test_metric(
        db_session, tenant.id, healthy.id,
        "memory_usage_percent", 60, now
    )

    # Warning device: CPU is at least 75%.
    add_test_metric(
        db_session, tenant.id, warning.id,
        "cpu_usage_percent", 80, now
    )

    # Critical device: disk usage is at least 90%.
    add_test_metric(
        db_session, tenant.id, critical.id,
        "disk_usage_percent", 95, now
    )

    # Offline devices remain offline even if they have older readings.
    add_test_metric(
        db_session, tenant.id, offline.id,
        "cpu_usage_percent", 99, now - timedelta(minutes=10)
    )

    add_test_event(
        db_session, tenant.id, healthy.id,
        "critical", "Critical test event", now
    )

    add_test_event(
        db_session, tenant.id, warning.id,
        "high", "High test event", now
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/dashboard",
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_devices"] == 4
    assert data["active_collectors"] == 4
    assert data["inactive_collectors"] == 0

    assert data["healthy_devices"] == 1
    assert data["warning_devices"] == 1
    assert data["critical_devices"] == 1
    assert data["offline_devices"] == 1

    assert data["total_events"] == 2
    assert data["critical_events"] == 1

    assert len(data["latest_metrics"]) >= 3


def test_dashboard_classifies_missing_health_metrics_as_warning(
    admin_client,
    db_session,
):
    now = datetime.now(timezone.utc)

    tenant = create_test_tenant(
        db_session,
        "Missing Metrics Company",
    )

    create_test_collector(
        db_session,
        tenant.id,
        "Collector Without Metrics",
        now,
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/dashboard",
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_devices"] == 1
    assert data["warning_devices"] == 1
    assert data["healthy_devices"] == 0


def test_dashboard_is_tenant_separated(admin_client, db_session):
    now = datetime.now(timezone.utc)

    tenant_a = create_test_tenant(db_session, "Dashboard Company A")
    tenant_b = create_test_tenant(db_session, "Dashboard Company B")

    collector_a = create_test_collector(
        db_session, tenant_a.id, "Collector A", now
    )

    collector_b = create_test_collector(
        db_session, tenant_b.id, "Collector B", now
    )

    add_test_metric(
        db_session, tenant_a.id, collector_a.id,
        "cpu_usage_percent", 30, now
    )

    add_test_metric(
        db_session, tenant_b.id, collector_b.id,
        "cpu_usage_percent", 99, now
    )

    add_test_event(
        db_session, tenant_b.id, collector_b.id,
        "critical", "Company B Critical Alert", now
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant_a.id}/dashboard",
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_devices"] == 1
    assert data["total_events"] == 0
    assert data["critical_events"] == 0
    assert all(
        metric["collector_id"] == collector_a.id
        for metric in data["latest_metrics"]
    )


def test_dashboard_rejects_missing_admin_key(admin_client, db_session):
    tenant = create_test_tenant(
        db_session,
        "Protected Dashboard Company",
    )

    response = admin_client.get(
        f"/api/v1/admin/tenants/{tenant.id}/dashboard"
    )

    assert response.status_code == 401


def test_dashboard_rejects_unknown_tenant(admin_client):
    response = admin_client.get(
        "/api/v1/admin/tenants/9999/dashboard",
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 404