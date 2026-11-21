from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TenantCreate(BaseModel):
    """Data required to create a customer tenant."""

    name: str = Field(
        min_length=1,
        max_length=150
    )


class TenantRead(BaseModel):
    """Tenant information returned by the backend."""

    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)