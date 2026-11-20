from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Incident


SEVERITIES = ["info", "low", "medium", "high", "critical"]

PRIORITIES = ["low", "medium", "high", "critical"]

STATUSES = [
    "open",
    "acknowledged",
    "investigating",
    "resolved",
    "closed",
]


def get_tenant_incident_analytics(
    db: Session,
    tenant_id: int,
) -> dict:
    """Calculate incident statistics for one tenant."""

    base_query = db.query(Incident).filter(
        Incident.tenant_id == tenant_id
    )

    total_incidents = base_query.count()

    repeated_incidents = base_query.filter(
        Incident.occurrence_count > 1
    ).count()

    correlated_incidents = base_query.filter(
        Incident.correlation_key.isnot(None)
    ).count()

    severity_rows = (
        db.query(
            Incident.severity,
            func.count(Incident.id).label("count"),
        )
        .filter(Incident.tenant_id == tenant_id)
        .group_by(Incident.severity)
        .all()
    )

    priority_rows = (
        db.query(
            Incident.priority,
            func.count(Incident.id).label("count"),
        )
        .filter(Incident.tenant_id == tenant_id)
        .group_by(Incident.priority)
        .all()
    )

    status_rows = (
        db.query(
            Incident.status,
            func.count(Incident.id).label("count"),
        )
        .filter(Incident.tenant_id == tenant_id)
        .group_by(Incident.status)
        .all()
    )

    severity_counts = {name: 0 for name in SEVERITIES}
    priority_counts = {name: 0 for name in PRIORITIES}
    status_counts = {name: 0 for name in STATUSES}

    for row in severity_rows:
        if row.severity in severity_counts:
            severity_counts[row.severity] = row.count

    for row in priority_rows:
        if row.priority in priority_counts:
            priority_counts[row.priority] = row.count

    for row in status_rows:
        if row.status in status_counts:
            status_counts[row.status] = row.count

    return {
        "total_incidents": total_incidents,
        "repeated_incidents": repeated_incidents,
        "correlated_incidents": correlated_incidents,
        "by_severity": [
            {"severity": name, "count": severity_counts[name]}
            for name in SEVERITIES
        ],
        "by_priority": [
            {"priority": name, "count": priority_counts[name]}
            for name in PRIORITIES
        ],
        "by_status": [
            {"status": name, "count": status_counts[name]}
            for name in STATUSES
        ],
    }