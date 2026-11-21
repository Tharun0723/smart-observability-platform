import pytest

from app.models import Tenant, Collector
from app.services.collector_auth import (
    provision_collector,
    authenticate_collector,
)


def create_test_tenant(db_session):
    tenant = Tenant(name="Test Company")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def test_provision_collector(db_session):
    tenant = create_test_tenant(db_session)

    collector, secret = provision_collector(
        db_session,
        tenant.id,
        "Test Collector",
    )

    assert collector.id is not None
    assert collector.tenant_id == tenant.id
    assert collector.name == "Test Collector"
    assert collector.is_active is True

    # The database stores a hash, not the original secret.
    assert collector.secret_hash != secret
    assert len(collector.secret_hash) == 64


def test_provision_collector_rejects_unknown_tenant(db_session):
    with pytest.raises(ValueError, match="Tenant not found"):
        provision_collector(
            db_session,
            9999,
            "Unknown Tenant Collector",
        )


def test_provision_collector_rejects_empty_name(db_session):
    tenant = create_test_tenant(db_session)

    with pytest.raises(ValueError, match="Collector name cannot be empty"):
        provision_collector(db_session, tenant.id, "   ")


def test_authenticate_valid_collector(db_session):
    tenant = create_test_tenant(db_session)

    collector, secret = provision_collector(
        db_session,
        tenant.id,
        "Authentication Test Collector",
    )

    authenticated = authenticate_collector(db_session, secret)

    assert authenticated is not None
    assert authenticated.id == collector.id
    assert authenticated.last_seen_at is not None


def test_authenticate_invalid_secret(db_session):
    authenticated = authenticate_collector(
        db_session,
        "this-is-not-a-valid-secret",
    )

    assert authenticated is None


def test_inactive_collector_cannot_authenticate(db_session):
    tenant = create_test_tenant(db_session)

    collector, secret = provision_collector(
        db_session,
        tenant.id,
        "Inactive Collector",
    )

    collector.is_active = False
    db_session.commit()

    authenticated = authenticate_collector(db_session, secret)

    assert authenticated is None