from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Metric


def normalize_datetime(value: datetime | None) -> datetime | None:
    """Convert a timezone-aware datetime to UTC for SQLite queries."""

    if value is None:
        return None

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Datetime must include a timezone")

    return value.astimezone(timezone.utc).replace(tzinfo=None)


def get_tenant_metrics(
    db: Session,
    tenant_id: int,
    metric_name: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Metric]:
    """Retrieve filtered metric history for one tenant."""

    query = db.query(Metric).filter(
        Metric.tenant_id == tenant_id
    )

    if metric_name:
        query = query.filter(Metric.metric_name == metric_name)

    start_time = normalize_datetime(start_time)
    end_time = normalize_datetime(end_time)

    if start_time:
        query = query.filter(Metric.recorded_at >= start_time)

    if end_time:
        query = query.filter(Metric.recorded_at <= end_time)

    return (
        query
        .order_by(Metric.recorded_at.desc(), Metric.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_tenant_metric_summary(
    db: Session,
    tenant_id: int,
    metric_name: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> list[dict]:
    """Calculate count, average, minimum, maximum and latest time."""

    query = db.query(
        Metric.metric_name.label("metric_name"),
        func.count(Metric.id).label("count"),
        func.avg(Metric.value).label("average"),
        func.min(Metric.value).label("minimum"),
        func.max(Metric.value).label("maximum"),
        func.max(Metric.recorded_at).label("latest_recorded_at"),
    ).filter(
        Metric.tenant_id == tenant_id
    )

    if metric_name:
        query = query.filter(Metric.metric_name == metric_name)

    start_time = normalize_datetime(start_time)
    end_time = normalize_datetime(end_time)

    if start_time:
        query = query.filter(Metric.recorded_at >= start_time)

    if end_time:
        query = query.filter(Metric.recorded_at <= end_time)

    results = (
        query
        .group_by(Metric.metric_name)
        .order_by(Metric.metric_name)
        .all()
    )

    return [
        {
            "metric_name": row.metric_name,
            "count": row.count,
            "average": float(row.average),
            "minimum": float(row.minimum),
            "maximum": float(row.maximum),
            "latest_recorded_at": row.latest_recorded_at,
        }
        for row in results
    ]