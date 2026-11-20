import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.core.config import settings
from app.models import Tenant
from app.services.collector_auth import (
    provision_collector,
    authenticate_collector,
)


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


def create_test_collector(db_session):
    tenant = Tenant(name="Collector Lifecycle Company")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    collector, secret = provision_collector(
        db_session,
        tenant.id,
        "Lifecycle Test Collector",
    )

    return tenant, collector, secret


def admin_headers():
    return {"X-Admin-API-Key": "test-admin-key"}


def test_revoke_collector(admin_client, db_session):
    tenant, collector, secret = create_test_collector(db_session)

    response = admin_client.delete(
        f"/api/v1/admin/tenants/{tenant.id}/collectors/{collector.id}",
        headers=admin_headers(),
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # A revoked collector must no longer authenticate.
    assert authenticate_collector(db_session, secret) is None


def test_reactivate_collector(admin_client, db_session):
    tenant, collector, secret = create_test_collector(db_session)

    admin_client.delete(
        f"/api/v1/admin/tenants/{tenant.id}/collectors/{collector.id}",
        headers=admin_headers(),
    )

    response = admin_client.post(
        f"/api/v1/admin/tenants/{tenant.id}/collectors/{collector.id}/activate",
        headers=admin_headers(),
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is True

    assert authenticate_collector(db_session, secret) is not None


def test_rotate_collector_secret(admin_client, db_session):
    tenant, collector, old_secret = create_test_collector(db_session)

    response = admin_client.post(
        f"/api/v1/admin/tenants/{tenant.id}/collectors/{collector.id}/rotate-secret",
        headers=admin_headers(),
    )

    assert response.status_code == 200

    new_secret = response.json()["collector_secret"]

    assert new_secret
    assert new_secret != old_secret

    # Old secret must stop working.
    assert authenticate_collector(db_session, old_secret) is None

    # New secret must work.
    authenticated = authenticate_collector(db_session, new_secret)

    assert authenticated is not None
    assert authenticated.id == collector.id


def test_rotate_inactive_collector_stays_inactive(
    admin_client,
    db_session,
):
    tenant, collector, old_secret = create_test_collector(db_session)

    admin_client.delete(
        f"/api/v1/admin/tenants/{tenant.id}/collectors/{collector.id}",
        headers=admin_headers(),
    )

    response = admin_client.post(
        f"/api/v1/admin/tenants/{tenant.id}/collectors/{collector.id}/rotate-secret",
        headers=admin_headers(),
    )

    assert response.status_code == 200

    new_secret = response.json()["collector_secret"]

    assert response.json()["id"] == collector.id
    assert authenticate_collector(db_session, old_secret) is None
    assert authenticate_collector(db_session, new_secret) is None

    activation = admin_client.post(
        f"/api/v1/admin/tenants/{tenant.id}/collectors/{collector.id}/activate",
        headers=admin_headers(),
    )

    assert activation.status_code == 200
    assert authenticate_collector(db_session, new_secret) is not None


def test_collector_cannot_be_revoked_through_another_tenant(
    admin_client,
    db_session,
):
    tenant, collector, secret = create_test_collector(db_session)

    other_tenant = Tenant(name="Different Company")
    db_session.add(other_tenant)
    db_session.commit()
    db_session.refresh(other_tenant)

    response = admin_client.delete(
        f"/api/v1/admin/tenants/{other_tenant.id}/collectors/{collector.id}",
        headers=admin_headers(),
    )

    assert response.status_code == 404
    assert authenticate_collector(db_session, secret) is not None


def test_collector_rotation_requires_admin_key(
    admin_client,
    db_session,
):
    tenant, collector, secret = create_test_collector(db_session)

    response = admin_client.post(
        f"/api/v1/admin/tenants/{tenant.id}/collectors/{collector.id}/rotate-secret"
    )

    assert response.status_code == 401

    # Unauthorized request must not change the old secret.
    assert authenticate_collector(db_session, secret) is not None