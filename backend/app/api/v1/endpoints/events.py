from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_collector
from app.db.database import get_db
from app.models import Collector
from app.schemas.event import EventBatch, EventIngestResponse
from app.services.event_ingestion import ingest_events


router = APIRouter()


@router.post(
    "",
    response_model=EventIngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Events"],
)
def receive_events(
    payload: EventBatch,
    collector: Collector = Depends(get_current_collector),
    db: Session = Depends(get_db),
):
    """Receive approved events from an authenticated collector."""

    accepted = ingest_events(
        db=db,
        collector=collector,
        events=payload.events,
    )

    return {
        "message": "Events received successfully",
        "accepted": accepted,
        "collector_id": collector.id,
        "tenant_id": collector.tenant_id,
    }