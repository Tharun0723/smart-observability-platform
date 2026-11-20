import math

from datetime import datetime, timezone
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    field_serializer,
)


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

class MetricRead(BaseModel):
    """One stored metric returned to the dashboard."""

    id: int
    tenant_id: int
    collector_id: int
    metric_name: str
    value: float
    unit: str | None
    recorded_at: datetime
    received_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("recorded_at", "received_at")
    def serialize_as_utc(self, value: datetime):
        # SQLite may return timezone-naive datetimes.
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)


class MetricSummaryItem(BaseModel):
    """Aggregated measurements for one metric type."""

    metric_name: str
    count: int
    average: float
    minimum: float
    maximum: float
    latest_recorded_at: datetime

    @field_serializer("latest_recorded_at")
    def serialize_latest_as_utc(self, value: datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)


class MetricSummaryResponse(BaseModel):
    """Summary of all available metrics for one tenant."""

    tenant_id: int
    metrics: list[MetricSummaryItem]    