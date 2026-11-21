from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_aiops
from app.db.database import get_db
from app.models import Tenant
from app.schemas.incident import (
    IncidentCreate,
    IncidentIngestResponse,
)
from app.services.incident_service import ingest_or_update_incident


# Every endpoint in this router requires the AIOps integration key.
router = APIRouter(
    dependencies=[Depends(require_aiops)]
)


@router.post(
    "/tenants/{tenant_id}/incidents",
    response_model=IncidentIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
def receive_aiops_incident(
    tenant_id: int,
    payload: IncidentCreate,
    db: Session = Depends(get_db),
):
    """Receive and deduplicate an incident from the AIOps engine."""

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    incident, created = ingest_or_update_incident(
        db=db,
        tenant_id=tenant_id,
        payload=payload,
    )

    return {
        "message": (
            "Incident created successfully"
            if created
            else "Existing incident updated successfully"
        ),
        "incident": incident,
        "created": created,
    }