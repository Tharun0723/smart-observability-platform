from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CollectorProvision(BaseModel):
    """Internal collector registration data."""

    tenant_id: int = Field(gt=0)

    name: str = Field(
        min_length=1,
        max_length=150
    )


class CollectorRead(BaseModel):
    """Collector information returned by the backend."""

    id: int
    tenant_id: int
    name: str
    is_active: bool
    created_at: datetime
    last_seen_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class CollectorProvisioned(BaseModel):
    """Collector details returned immediately after provisioning."""

    id: int
    tenant_id: int
    name: str
    is_active: bool
    created_at: datetime

    # Returned once during provisioning; never stored in the database.
    collector_secret: str    

class CollectorStatusRead(BaseModel):
    """Collector status after activation or revocation."""

    id: int
    tenant_id: int
    name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CollectorSecretRotationResponse(BaseModel):
    """New collector secret, returned only during rotation."""

    id: int
    tenant_id: int
    name: str
    collector_secret: str