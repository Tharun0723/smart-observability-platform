from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import (
    generate_collector_secret,
    hash_collector_secret,
    verify_collector_secret,
)
from app.models import Collector, Tenant


def provision_collector(
    db: Session,
    tenant_id: int,
    name: str,
) -> tuple[Collector, str]:
    """
    Register a collector and return its record and one-time secret.

    Only the secret hash is stored in the database.
    """

    name = name.strip()

    if not name:
        raise ValueError("Collector name cannot be empty")

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if tenant is None:
        raise ValueError("Tenant not found")

    secret = generate_collector_secret()

    collector = Collector(
        tenant_id=tenant_id,
        name=name,
        secret_hash=hash_collector_secret(secret),
        is_active=True,
    )

    try:
        db.add(collector)
        db.commit()
        db.refresh(collector)
    except Exception:
        db.rollback()
        raise

    # Show the plaintext secret to the caller only at provisioning time.
    return collector, secret


def authenticate_collector(
    db: Session,
    secret: str,
) -> Collector | None:
    """
    Authenticate a collector using its secret.

    Returns the active collector, or None if authentication fails.
    """

    if not isinstance(secret, str) or not secret:
        return None

    secret_hash = hash_collector_secret(secret)

    collector = (
        db.query(Collector)
        .filter(Collector.secret_hash == secret_hash)
        .first()
    )

    if collector is None or not collector.is_active:
        return None

    if not verify_collector_secret(secret, collector.secret_hash):
        return None

    collector.last_seen_at = func.now()
    db.commit()
    db.refresh(collector)

    return collector 
def get_tenant_collector(
    db: Session,
    tenant_id: int,
    collector_id: int,
) -> Collector | None:
    """Find a collector only within its owning tenant."""

    return (
        db.query(Collector)
        .filter(
            Collector.id == collector_id,
            Collector.tenant_id == tenant_id,
        )
        .first()
    )


def revoke_collector(
    db: Session,
    tenant_id: int,
    collector_id: int,
) -> Collector:
    """Disable a collector so its secret can no longer authenticate."""

    collector = get_tenant_collector(
        db, tenant_id, collector_id
    )

    if collector is None:
        raise ValueError("Collector not found")

    collector.is_active = False

    try:
        db.commit()
        db.refresh(collector)
    except Exception:
        db.rollback()
        raise

    return collector


def activate_collector(
    db: Session,
    tenant_id: int,
    collector_id: int,
) -> Collector:
    """Reactivate an existing collector."""

    collector = get_tenant_collector(
        db, tenant_id, collector_id
    )

    if collector is None:
        raise ValueError("Collector not found")

    if not collector.secret_hash:
        raise ValueError(
            "Collector must have a secret before activation"
        )

    collector.is_active = True

    try:
        db.commit()
        db.refresh(collector)
    except Exception:
        db.rollback()
        raise

    return collector


def rotate_collector_secret(
    db: Session,
    tenant_id: int,
    collector_id: int,
) -> tuple[Collector, str]:
    """
    Generate and store a new collector secret.

    The original secret immediately becomes invalid.
    An inactive collector remains inactive until explicitly activated.
    """

    collector = get_tenant_collector(
        db, tenant_id, collector_id
    )

    if collector is None:
        raise ValueError("Collector not found")

    new_secret = generate_collector_secret()

    collector.secret_hash = hash_collector_secret(new_secret)

    # Require the collector to authenticate again with its new secret.
    collector.last_seen_at = None

    try:
        db.commit()
        db.refresh(collector)
    except Exception:
        db.rollback()
        raise

    return collector, new_secret