import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.models import Tenant
from app.services.collector_auth import provision_collector


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)


def create_tenant(db_session):
    tenant = Tenant(name="API Test Company")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def test_collector_api_accepts_valid_secret(client, db_session):
    tenant = create_tenant(db_session)

    collector, secret = provision_collector(
        db_session,
        tenant.id,
        "API Test Collector",
    )

    response = client.get(
        "/api/v1/collectors/me",
        headers={"X-Collector-Secret": secret},
    )

    assert response.status_code == 200
    assert response.json()["collector_id"] == collector.id
    assert response.json()["tenant_id"] == tenant.id
    assert response.json()["name"] == "API Test Collector"


def test_collector_api_rejects_missing_secret(client):
    response = client.get("/api/v1/collectors/me")

    assert response.status_code == 401


def test_collector_api_rejects_invalid_secret(client):
    response = client.get(
        "/api/v1/collectors/me",
        headers={"X-Collector-Secret": "wrong-secret"},
    )

    assert response.status_code == 401