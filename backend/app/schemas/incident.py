from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator


class IncidentCreate(BaseModel):
    """Incident data received from the AIOps engine."""

    fingerprint: str = Field(
        min_length=1,
        max_length=128,
    )

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    source: str | None = Field(
        default=None,
        max_length=100,
    )

    severity: Literal[
        "info",
        "low",
        "medium",
        "high",
        "critical",
    ]

    priority: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ]

    affected_resource: str | None = Field(
        default=None,
        max_length=200,
    )

    correlation_key: str | None = Field(
        default=None,
        max_length=128,
    )

    recommendation: str | None = Field(
        default=None,
        max_length=5000,
    )

    occurred_at: datetime

    @field_validator(
        "fingerprint",
        "title",
        "description",
        "source",
        "affected_resource",
        "correlation_key",
        "recommendation",
    )
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


class IncidentRead(BaseModel):
    """Incident information returned to the frontend."""

    id: int
    tenant_id: int
    fingerprint: str
    title: str
    description: str | None
    source: str | None
    severity: str
    priority: str
    status: str
    affected_resource: str | None
    correlation_key: str | None
    recommendation: str | None
    first_seen_at: datetime
    last_seen_at: datetime
    occurrence_count: int

    model_config = ConfigDict(from_attributes=True)


class IncidentIngestResponse(BaseModel):
    message: str
    incident: IncidentRead
    created: bool


class IncidentStatusUpdate(BaseModel):
    status: Literal[
        "open",
        "acknowledged",
        "investigating",
        "resolved",
        "closed",
    ]