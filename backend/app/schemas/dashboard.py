from datetime import datetime

from pydantic import BaseModel


class DashboardSeverityCount(BaseModel):
    severity: str
    count: int


class DashboardMetricValue(BaseModel):
    metric_name: str
    value: float
    unit: str | None
    collector_id: int
    recorded_at: datetime


class DashboardOverviewResponse(BaseModel):
    """Complete overview information for one tenant."""

    tenant_id: int

    # Collector and device overview
    total_devices: int
    active_collectors: int
    inactive_collectors: int

    # Device health
    healthy_devices: int
    warning_devices: int
    critical_devices: int
    offline_devices: int

    # Security and application events
    total_events: int
    critical_events: int
    events_by_severity: list[DashboardSeverityCount]

    # Latest infrastructure readings
    latest_metrics: list[DashboardMetricValue]