from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Event


def normalize_datetime(value: datetime | None):
    """Normalize timestamps for SQLite comparisons."""

    if value is None:
        return None

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Datetime must include a timezone")

    return value.astimezone(timezone.utc).replace(tzinfo=None)


def get_tenant_events(
    db: Session,
    tenant_id: int,
    event_type: str | None = None,
    severity: str | None = None,
    source: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Event]:

    query = db.query(Event).filter(
        Event.tenant_id == tenant_id
    )

    if event_type:
        query = query.filter(Event.event_type == event_type)

    if severity:
        query = query.filter(Event.severity == severity)

    if source:
        query = query.filter(Event.source == source)

    start_time = normalize_datetime(start_time)
    end_time = normalize_datetime(end_time)

    if start_time:
        query = query.filter(Event.occurred_at >= start_time)

    if end_time:
        query = query.filter(Event.occurred_at <= end_time)

    return (
        query
        .order_by(Event.occurred_at.desc(), Event.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_tenant_event_summary(
    db: Session,
    tenant_id: int,
    event_type: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict:

    query = db.query(Event).filter(
        Event.tenant_id == tenant_id
    )

    if event_type:
        query = query.filter(Event.event_type == event_type)

    start_time = normalize_datetime(start_time)
    end_time = normalize_datetime(end_time)

    if start_time:
        query = query.filter(Event.occurred_at >= start_time)

    if end_time:
        query = query.filter(Event.occurred_at <= end_time)

    total_events = query.count()

    severity_results = (
        query.with_entities(
            Event.severity,
            func.count(Event.id).label("count"),
        )
        .group_by(Event.severity)
        .order_by(Event.severity)
        .all()
    )

    return {
        "total_events": total_events,
        "by_severity": [
            {
                "severity": row.severity,
                "count": row.count,
            }
            for row in severity_results
        ],
    }