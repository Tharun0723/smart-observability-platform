import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.core.config import settings
from app.models import Tenant


@pytest.fixture
def admin_client(db_session, monkeypatch):
    monkeypatch.setattr(settings, "admin_api_key", "test-admin-key")

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)


def test_create_tenant_with_valid_admin_key(admin_client):
    response = admin_client.post(
        "/api/v1/admin/tenants",
        headers={"X-Admin-API-Key": "test-admin-key"},
        json={"name": "CICADA Test Company"},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "CICADA Test Company"
    assert "id" in response.json()


def test_create_tenant_without_admin_key(admin_client):
    response = admin_client.post(
        "/api/v1/admin/tenants",
        json={"name": "Unauthorized Company"},
    )

    assert response.status_code == 401


def test_create_tenant_with_wrong_admin_key(admin_client):
    response = admin_client.post(
        "/api/v1/admin/tenants",
        headers={"X-Admin-API-Key": "wrong-key"},
        json={"name": "Unauthorized Company"},
    )

    assert response.status_code == 401


def test_list_tenants_with_valid_admin_key(admin_client, db_session):
    db_session.add(Tenant(name="Existing Test Company"))
    db_session.commit()

    response = admin_client.get(
        "/api/v1/admin/tenants",
        headers={"X-Admin-API-Key": "test-admin-key"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Existing Test Company"


def test_list_tenants_without_admin_key(admin_client):
    response = admin_client.get("/api/v1/admin/tenants")

    assert response.status_code == 401
