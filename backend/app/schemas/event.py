from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EventCreate(BaseModel):
    """Approved security or application event metadata."""

    event_type: Literal[
        "security_alert",
        "application_error",
        "network_event",
        "system_event",
    ]

    severity: Literal[
        "info",
        "low",
        "medium",
        "high",
        "critical",
    ]

    source: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    summary: str | None = Field(
        default=None,
        max_length=500,
    )

    occurred_at: datetime

    @field_validator("title", "source", "summary")
    @classmethod
    def clean_text(cls, value):
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Text field cannot be empty")

        return value
    
    @field_validator("occurred_at")
    @classmethod
    def validate_timestamp(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "occurred_at must include a timezone"
            )
        return value


class EventBatch(BaseModel):
    """A batch of event metadata from one collector."""

    events: list[EventCreate] = Field(
        min_length=1,
        max_length=100,
    )


class EventIngestResponse(BaseModel):
    message: str
    accepted: int
    collector_id: int
    tenant_id: int

from pydantic import ConfigDict, field_serializer
from datetime import timezone


class EventRead(BaseModel):
    """Event record returned to the dashboard."""

    id: int
    tenant_id: int
    collector_id: int
    event_type: str
    severity: str
    source: str | None
    title: str
    summary: str | None
    occurred_at: datetime
    received_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("occurred_at", "received_at")
    def serialize_as_utc(self, value: datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)


class EventSeverityCount(BaseModel):
    severity: str
    count: int


class EventSummaryResponse(BaseModel):
    tenant_id: int
    total_events: int
    by_severity: list[EventSeverityCount]    