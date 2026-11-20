from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.database import get_db
from app.models import Tenant
from app.schemas import TenantCreate, TenantRead


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