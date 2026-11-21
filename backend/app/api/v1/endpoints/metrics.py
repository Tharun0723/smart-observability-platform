from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_collector
from app.db.database import get_db
from app.models import Collector
from app.schemas.metric import (
    MetricBatch,
    MetricIngestResponse,
)
from app.services.metric_ingestion import ingest_metrics


router = APIRouter()


@router.post(
    "",
    response_model=MetricIngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Telemetry"],
)
def receive_metrics(
    payload: MetricBatch,
    collector: Collector = Depends(get_current_collector),
    db: Session = Depends(get_db),
):
    """Receive and store metrics from an authenticated collector."""

    accepted = ingest_metrics(
        db=db,
        collector=collector,
        metrics=payload.metrics,
    )

    return {
        "message": "Metrics received successfully",
        "accepted": accepted,
        "collector_id": collector.id,
        "tenant_id": collector.tenant_id,
    }