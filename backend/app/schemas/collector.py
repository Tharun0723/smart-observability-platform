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