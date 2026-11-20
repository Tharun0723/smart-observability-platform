from fastapi import Header, HTTPException, status

from app.core.security import verify_admin_api_key


def require_admin(
    x_admin_api_key: str | None = Header(
        default=None,
        alias="X-Admin-API-Key",
    ),
) -> None:
    """Block requests that do not have the correct administrator key."""

    if not verify_admin_api_key(x_admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid administrator API key",
        )