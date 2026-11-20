import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.models import Tenant, Metric
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
    tenant = Tenant(name="Telemetry Test Company")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    collector, secret = provision_collector(
        db_session,
        tenant.id,
        "Telemetry Test Collector",
    )

    return tenant, collector, secret


def test_ingest_valid_metrics(client, db_session):
    tenant, collector, secret = create_test_collector(db_session)

    response = client.post(
        "/api/v1/metrics",
        headers={"X-Collector-Secret": secret},
        json={
            "metrics": [
                {
                    "metric_name": "cpu_usage_percent",
                    "value": 45.5,
                    "unit": "percent",
                    "recorded_at": "2026-11-20T17:30:00Z",
                },
                {
                    "metric_name": "memory_usage_percent",
                    "value": 67.2,
                    "unit": "percent",
                    "recorded_at": "2026-11-20T17:30:00Z",
                },
            ]
        },
    )

    assert response.status_code == 201
    assert response.json()["accepted"] == 2
    assert response.json()["collector_id"] == collector.id
    assert response.json()["tenant_id"] == tenant.id

    saved_metrics = db_session.query(Metric).filter(
        Metric.collector_id == collector.id
    ).all()

    assert len(saved_metrics) == 2
    assert all(item.tenant_id == tenant.id for item in saved_metrics)


def test_ingestion_does_not_trust_request_tenant_id(client, db_session):
    tenant, collector, secret = create_test_collector(db_session)

    response = client.post(
        "/api/v1/metrics",
        headers={"X-Collector-Secret": secret},
        json={
            "tenant_id": 9999,
            "metrics": [
                {
                    "metric_name": "cpu_usage_percent",
                    "value": 50,
                    "unit": "percent",
                    "recorded_at": "2026-11-20T17:30:00Z",
                }
            ],
        },
    )

    assert response.status_code == 201

    saved_metric = db_session.query(Metric).first()

    assert saved_metric.tenant_id == tenant.id
    assert saved_metric.tenant_id != 9999


def test_ingestion_rejects_missing_collector_secret(client):
    response = client.post(
        "/api/v1/metrics",
        json={
            "metrics": [
                {
                    "metric_name": "cpu_usage_percent",
                    "value": 50,
                    "unit": "percent",
                    "recorded_at": "2026-11-20T17:30:00Z",
                }
            ]
        },
    )

    assert response.status_code == 401


def test_ingestion_rejects_invalid_timestamp(client, db_session):
    _, _, secret = create_test_collector(db_session)

    response = client.post(
        "/api/v1/metrics",
        headers={"X-Collector-Secret": secret},
        json={
            "metrics": [
                {
                    "metric_name": "cpu_usage_percent",
                    "value": 50,
                    "unit": "percent",
                    "recorded_at": "2026-11-20T17:30:00",
                }
            ]
        },
    )

    assert response.status_code == 422