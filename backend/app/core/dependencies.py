from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import verify_admin_api_key
from app.db.database import get_db
from app.models import Collector
from app.services.collector_auth import authenticate_collector


def require_admin(
    x_admin_api_key: str | None = Header(
        default=None,
        alias="X-Admin-API-Key",
    ),
) -> None:
    """Verify administrator credentials."""

    if not verify_admin_api_key(x_admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid administrator API key",
        )


def get_current_collector(
    x_collector_secret: str | None = Header(
        default=None,
        alias="X-Collector-Secret",
    ),
    db: Session = Depends(get_db),
) -> Collector:
    """Identify an active collector using its secret."""

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

    return collector