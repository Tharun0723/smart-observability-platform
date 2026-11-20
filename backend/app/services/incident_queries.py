from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Incident


def normalize_datetime(value: datetime | None):
    """Normalize timezone-aware timestamps for SQLite."""

    if value is None:
        return None

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Datetime must include a timezone")

    return value.astimezone(timezone.utc).replace(tzinfo=None)


def get_tenant_incidents(
    db: Session,
    tenant_id: int,
    severity: str | None = None,
    priority: str | None = None,
    incident_status: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Incident]:
    """Retrieve filtered incidents belonging to one tenant."""

    query = db.query(Incident).filter(
        Incident.tenant_id == tenant_id
    )

    if severity:
        query = query.filter(Incident.severity == severity)

    if priority:
        query = query.filter(Incident.priority == priority)

    if incident_status:
        query = query.filter(Incident.status == incident_status)

    start_time = normalize_datetime(start_time)
    end_time = normalize_datetime(end_time)

    if start_time:
        query = query.filter(
            Incident.last_seen_at >= start_time
        )

    if end_time:
        query = query.filter(
            Incident.last_seen_at <= end_time
        )

    return (
        query
        .order_by(
            Incident.last_seen_at.desc(),
            Incident.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )