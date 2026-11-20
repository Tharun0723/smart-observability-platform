from sqlalchemy.orm import Session

from app.models import Collector, Event
from app.schemas.event import EventCreate


def ingest_events(
    db: Session,
    collector: Collector,
    events: list[EventCreate],
) -> int:
    """
    Store approved event metadata for an authenticated collector.

    Tenant ownership comes from the authenticated collector.
    """

    event_records = [
        Event(
            tenant_id=collector.tenant_id,
            collector_id=collector.id,
            event_type=item.event_type,
            severity=item.severity,
            source=item.source,
            title=item.title,
            summary=item.summary,
            occurred_at=item.occurred_at,
        )
        for item in events
    ]

    try:
        db.add_all(event_records)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return len(event_records)