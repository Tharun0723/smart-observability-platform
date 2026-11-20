from sqlalchemy.orm import Session

from app.models import Collector, Metric
from app.schemas.metric import MetricCreate


def ingest_metrics(
    db: Session,
    collector: Collector,
    metrics: list[MetricCreate],
) -> int:
    """
    Store a batch of metrics for an authenticated collector.

    Tenant ownership is taken from the authenticated collector,
    never from the incoming request.
    """

    metric_records = [
        Metric(
            tenant_id=collector.tenant_id,
            collector_id=collector.id,
            metric_name=item.metric_name,
            value=item.value,
            unit=item.unit,
            recorded_at=item.recorded_at,
        )
        for item in metrics
    ]

    try:
        db.add_all(metric_records)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return len(metric_records)