import math

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class MetricCreate(BaseModel):
    """One infrastructure measurement sent by a collector."""

    metric_name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_.-]*$",
    )

    value: float

    unit: str | None = Field(
        default=None,
        max_length=30,
    )

    recorded_at: datetime

    @field_validator("value")
    @classmethod
    def validate_value(cls, value):
        if not math.isfinite(value):
            raise ValueError("Metric value must be a finite number")
        return value

    @field_validator("recorded_at")
    @classmethod
    def validate_recorded_at_timezone(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "recorded_at must include a timezone"
            )
        return value


class MetricBatch(BaseModel):
    """A batch of metrics sent by one collector."""

    metrics: list[MetricCreate] = Field(
        min_length=1,
        max_length=100,
    )


class MetricIngestResponse(BaseModel):
    """Confirmation returned after metric ingestion."""

    message: str
    accepted: int
    collector_id: int
    tenant_id: int