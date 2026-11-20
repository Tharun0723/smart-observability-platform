from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.collector_auth import authenticate_collector


router = APIRouter()


@router.get("/me")
def get_current_collector(
    x_collector_secret: str | None = Header(
        default=None,
        alias="X-Collector-Secret"
    ),
    db: Session = Depends(get_db),
):
    """Return the identity of the authenticated collector."""

    if not x_collector_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Collector secret is required",
        )

    collector = authenticate_collector(db, x_collector_secret)

    if collector is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive collector",
        )

    return {
        "message": "Collector authenticated successfully",
        "collector_id": collector.id,
        "tenant_id": collector.tenant_id,
        "name": collector.name,
        "is_active": collector.is_active,
    }