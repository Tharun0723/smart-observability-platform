from app.schemas import DashboardOverviewResponse

from app.services.dashboard_service import get_dashboard_overview
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.database import get_db
from app.models import Tenant
from app.schemas import TenantCreate, TenantRead
from app.services.collector_auth import provision_collector
from app.schemas import CollectorProvision, CollectorProvisioned
from datetime import datetime, timezone
from app.models import Metric, Event

from sqlalchemy import func
from typing import Literal

from app.models import Metric
from app.schemas import MetricRead, MetricSummaryResponse
from app.services.metric_queries import (
    get_tenant_metrics,
    get_tenant_metric_summary,
)
from app.schemas import (
    EventRead,
    EventSummaryResponse,
)
from app.services.event_queries import (
    get_tenant_events,
    get_tenant_event_summary,
)
from fastapi import Query
from typing import Literal

from app.models import Incident

from app.schemas import (
    IncidentRead,
    IncidentStatusUpdate,
)

from app.services.incident_queries import get_tenant_incidents

def validate_time_range(
    start_time: datetime | None,
    end_time: datetime | None,
):
    """Require timezone-aware timestamps and a valid time range."""

    for label, value in (
        ("start_time", start_time),
        ("end_time", end_time),
    ):
        if value is not None and (
            value.tzinfo is None or value.utcoffset() is None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{label} must include a timezone",
            )

    if start_time and end_time and start_time > end_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time must not be later than end_time",
        )
# Every endpoint in this router requires administrator authentication.
router = APIRouter(
    dependencies=[Depends(require_admin)]
)


@router.post(
    "/tenants",
    response_model=TenantRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
):
    """Create a new customer tenant."""

    name = payload.name.strip()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tenant name cannot be empty",
        )

    tenant = Tenant(name=name)

    try:
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    except Exception:
        db.rollback()
        raise

    return tenant


@router.get(
    "/tenants",
    response_model=list[TenantRead],
)
def list_tenants(db: Session = Depends(get_db)):
    """Return all registered tenants."""

    return db.query(Tenant).order_by(Tenant.id).all()

@router.post(
    "/collectors",
    response_model=CollectorProvisioned,
    status_code=status.HTTP_201_CREATED,
)
def create_collector(
    payload: CollectorProvision,
    db: Session = Depends(get_db),
):
    """Register a collector and return its secret one time."""

    try:
        collector, secret = provision_collector(
            db=db,
            tenant_id=payload.tenant_id,
            name=payload.name,
        )
    except ValueError as exc:
        message = str(exc)
        error_status = (
            status.HTTP_404_NOT_FOUND
            if message == "Tenant not found"
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(
            status_code=error_status,
            detail=message,
        )

    return {
        "id": collector.id,
        "tenant_id": collector.tenant_id,
        "name": collector.name,
        "is_active": collector.is_active,
        "created_at": collector.created_at,
        "collector_secret": secret,
    }
@router.get(
    "/tenants/{tenant_id}/metrics",
    response_model=list[MetricRead],
)
def read_tenant_metrics(
    tenant_id: int,
    metric_name: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve metric history for one tenant."""

    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=422,
            detail="limit must be between 1 and 500",
        )

    if offset < 0:
        raise HTTPException(
            status_code=422,
            detail="offset cannot be negative",
        )

    validate_time_range(start_time, end_time)

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    return get_tenant_metrics(
        db=db,
        tenant_id=tenant_id,
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
@router.get(
    "/tenants/{tenant_id}/metrics/summary",
    response_model=MetricSummaryResponse,
)
def read_tenant_metric_summary(
    tenant_id: int,
    metric_name: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: Session = Depends(get_db),
):
    """Return aggregated metric information for a tenant."""

    validate_time_range(start_time, end_time)

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    summaries = get_tenant_metric_summary(
        db=db,
        tenant_id=tenant_id,
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time,
    )

    return {
        "tenant_id": tenant_id,
        "metrics": summaries,
    }
@router.get(
    "/tenants/{tenant_id}/events",
    response_model=list[EventRead],
)
def read_tenant_events(
    tenant_id: int,
    event_type: Literal[
        "security_alert",
        "application_error",
        "network_event",
        "system_event",
    ] | None = None,
    severity: Literal[
        "info",
        "low",
        "medium",
        "high",
        "critical",
    ] | None = None,
    source: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve filtered event history for one tenant."""

    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=422,
            detail="limit must be between 1 and 500",
        )

    if offset < 0:
        raise HTTPException(
            status_code=422,
            detail="offset cannot be negative",
        )

    validate_time_range(start_time, end_time)

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    return get_tenant_events(
        db=db,
        tenant_id=tenant_id,
        event_type=event_type,
        severity=severity,
        source=source,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
@router.get(
    "/tenants/{tenant_id}/events/summary",
    response_model=EventSummaryResponse,
)
def read_tenant_event_summary(
    tenant_id: int,
    event_type: Literal[
        "security_alert",
        "application_error",
        "network_event",
        "system_event",
    ] | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: Session = Depends(get_db),
):
    """Return event totals grouped by severity."""

    validate_time_range(start_time, end_time)

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    summary = get_tenant_event_summary(
        db=db,
        tenant_id=tenant_id,
        event_type=event_type,
        start_time=start_time,
        end_time=end_time,
    )

    return {
        "tenant_id": tenant_id,
        **summary,
    }
@router.get(
    "/tenants/{tenant_id}/dashboard",
    response_model=DashboardOverviewResponse,
)
def read_tenant_dashboard(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """Return the complete dashboard overview for one tenant."""

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    return get_dashboard_overview(
        db=db,
        tenant_id=tenant_id,
    )
@router.get(
    "/tenants/{tenant_id}/incidents",
    response_model=list[IncidentRead],
)
def read_tenant_incidents(
    tenant_id: int,
    severity: Literal[
        "info", "low", "medium", "high", "critical"
    ] | None = None,
    priority: Literal[
        "low", "medium", "high", "critical"
    ] | None = None,
    incident_status: Literal[
        "open",
        "acknowledged",
        "investigating",
        "resolved",
        "closed",
    ] | None = Query(default=None, alias="status"),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List and filter incidents belonging to one tenant."""

    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=422,
            detail="limit must be between 1 and 500",
        )

    if offset < 0:
        raise HTTPException(
            status_code=422,
            detail="offset cannot be negative",
        )

    validate_time_range(start_time, end_time)

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    return get_tenant_incidents(
        db=db,
        tenant_id=tenant_id,
        severity=severity,
        priority=priority,
        incident_status=incident_status,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
@router.patch(
    "/tenants/{tenant_id}/incidents/{incident_id}/status",
    response_model=IncidentRead,
)
def update_incident_status(
    tenant_id: int,
    incident_id: int,
    payload: IncidentStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update the status of an incident belonging to a tenant."""

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id
    ).first()

    if tenant is None:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found",
        )

    incident = (
        db.query(Incident)
        .filter(
            Incident.id == incident_id,
            Incident.tenant_id == tenant_id,
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found for this tenant",
        )

    incident.status = payload.status

    try:
        db.commit()
        db.refresh(incident)
    except Exception:
        db.rollback()
        raise

    return incident