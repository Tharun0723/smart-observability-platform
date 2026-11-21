from sqlalchemy.orm import Session

from app.models import Incident


def get_related_incidents(
    db: Session,
    tenant_id: int,
    incident_id: int,
    limit: int = 50,
):
    """Find incidents sharing the same correlation key and tenant."""

    incident = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id,
            Incident.tenant_id == tenant_id,
        )
        .first()
    )

    if incident is None:
        return None

    if not incident.correlation_key:
        return []

    return (
        db.query(Incident)
        .filter(
            Incident.tenant_id == tenant_id,
            Incident.correlation_key == incident.correlation_key,
            Incident.id != incident.id,
        )
        .order_by(
            Incident.last_seen_at.desc(),
            Incident.id.desc(),
        )
        .limit(limit)
        .all()
    )