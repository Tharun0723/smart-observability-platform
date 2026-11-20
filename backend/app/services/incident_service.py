from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Incident
from app.schemas.incident import IncidentCreate


def normalize_timestamp(value: datetime) -> datetime:
    """
    Normalize timestamps to UTC-naive values for SQLite.

    SQLite removes timezone metadata when reading DateTime values.
    Previously stored naive timestamps are therefore interpreted as UTC.
    Incoming timestamps are validated as timezone-aware by IncidentCreate.
    """

    if value.tzinfo is None or value.utcoffset() is None:
        # SQLite returned a previously stored UTC timestamp without tzinfo.
        return value

    return value.astimezone(timezone.utc).replace(tzinfo=None)


def ingest_or_update_incident(
    db: Session,
    tenant_id: int,
    payload: IncidentCreate,
) -> tuple[Incident, bool]:
    """
    Create a new incident or update an existing matching fingerprint.

    Returns:
        (incident, created)
    """

    occurred_at = normalize_timestamp(payload.occurred_at)

    incident = (
        db.query(Incident)
        .filter(
            Incident.tenant_id == tenant_id,
            Incident.fingerprint == payload.fingerprint,
        )
        .first()
    )

    created = incident is None

    if incident is None:
        incident = Incident(
            tenant_id=tenant_id,
            fingerprint=payload.fingerprint,
            title=payload.title,
            description=payload.description,
            source=payload.source,
            severity=payload.severity,
            priority=payload.priority,
            status="open",
            affected_resource=payload.affected_resource,
            correlation_key=payload.correlation_key,
            recommendation=payload.recommendation,
            first_seen_at=occurred_at,
            last_seen_at=occurred_at,
            occurrence_count=1,
        )

        db.add(incident)

    else:
        previous_first_seen = normalize_timestamp(
            incident.first_seen_at
        )
        previous_last_seen = normalize_timestamp(
            incident.last_seen_at
        )

        incident.first_seen_at = min(
            previous_first_seen,
            occurred_at,
        )

        incident.last_seen_at = max(
            previous_last_seen,
            occurred_at,
        )

        incident.occurrence_count += 1

        # Refresh incident information from the latest AIOps result.
        incident.title = payload.title
        incident.description = payload.description
        incident.source = payload.source
        incident.severity = payload.severity
        incident.priority = payload.priority
        incident.affected_resource = payload.affected_resource
        incident.correlation_key = payload.correlation_key
        incident.recommendation = payload.recommendation

        # Reopen an incident when the same problem occurs again.
        if incident.status in ("resolved", "closed"):
            incident.status = "open"

    try:
        db.commit()
        db.refresh(incident)
    except Exception:
        db.rollback()
        raise

    return incident, created