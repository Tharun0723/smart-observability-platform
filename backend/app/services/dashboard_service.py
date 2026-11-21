from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Collector, Metric, Event


# Dashboard health rules
OFFLINE_AFTER_MINUTES = 5
WARNING_THRESHOLD = 75.0
CRITICAL_THRESHOLD = 90.0

HEALTH_METRICS = (
    "cpu_usage_percent",
    "memory_usage_percent",
    "disk_usage_percent",
)

DASHBOARD_METRICS = (
    "cpu_usage_percent",
    "memory_usage_percent",
    "disk_usage_percent",
    "network_bytes_sent",
    "network_bytes_received",
)

SEVERITIES = ("info", "low", "medium", "high", "critical")


def as_utc(value: datetime) -> datetime:
    """Normalize SQLite or timezone-aware timestamps to UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def get_dashboard_overview(
    db: Session,
    tenant_id: int,
    now: datetime | None = None,
) -> dict:
    """Build the dashboard overview for one tenant."""

    now = now or datetime.now(timezone.utc)
    offline_limit = timedelta(minutes=OFFLINE_AFTER_MINUTES)

    # 1. Load collectors belonging to this tenant.
    collectors = (
        db.query(Collector)
        .filter(Collector.tenant_id == tenant_id)
        .all()
    )

    total_devices = len(collectors)
    active_collectors = sum(1 for c in collectors if c.is_active)
    inactive_collectors = total_devices - active_collectors

    collector_ids = [c.id for c in collectors]

    # 2. Get the latest CPU, memory and disk metrics per collector.
    latest_health = {}

    if collector_ids:
        rows = (
            db.query(Metric)
            .filter(
                Metric.tenant_id == tenant_id,
                Metric.collector_id.in_(collector_ids),
                Metric.metric_name.in_(HEALTH_METRICS),
            )
            .order_by(
                Metric.recorded_at.desc(),
                Metric.id.desc(),
            )
            .all()
        )

        for row in rows:
            key = (row.collector_id, row.metric_name)

            # First record is the newest because results are descending.
            if key not in latest_health:
                latest_health[key] = row.value

    # 3. Classify collector/device health.
    healthy_devices = 0
    warning_devices = 0
    critical_devices = 0
    offline_devices = 0

    for collector in collectors:
        last_seen = collector.last_seen_at

        is_offline = (
            not collector.is_active
            or last_seen is None
            or (now - as_utc(last_seen)) > offline_limit
        )

        if is_offline:
            offline_devices += 1
            continue

        values = [
            latest_health[(collector.id, name)]
            for name in HEALTH_METRICS
            if (collector.id, name) in latest_health
        ]

        # Missing health telemetry is not automatically healthy.
        if not values:
            warning_devices += 1
        elif any(value >= CRITICAL_THRESHOLD for value in values):
            critical_devices += 1
        elif any(value >= WARNING_THRESHOLD for value in values):
            warning_devices += 1
        else:
            healthy_devices += 1

    # 4. Retrieve the latest known dashboard metric for each metric type.
    latest_metrics = []

    for metric_name in DASHBOARD_METRICS:
        metric = (
            db.query(Metric)
            .filter(
                Metric.tenant_id == tenant_id,
                Metric.metric_name == metric_name,
            )
            .order_by(
                Metric.recorded_at.desc(),
                Metric.id.desc(),
            )
            .first()
        )

        if metric is not None:
            latest_metrics.append({
                "metric_name": metric.metric_name,
                "value": metric.value,
                "unit": metric.unit,
                "collector_id": metric.collector_id,
                "recorded_at": metric.recorded_at,
            })

    # 5. Count events grouped by severity.
    total_events = (
        db.query(func.count(Event.id))
        .filter(Event.tenant_id == tenant_id)
        .scalar()
        or 0
    )

    severity_rows = (
        db.query(
            Event.severity,
            func.count(Event.id).label("count"),
        )
        .filter(Event.tenant_id == tenant_id)
        .group_by(Event.severity)
        .all()
    )

    severity_counts = {
        severity: 0 for severity in SEVERITIES
    }

    for row in severity_rows:
        if row.severity in severity_counts:
            severity_counts[row.severity] = row.count

    events_by_severity = [
        {
            "severity": severity,
            "count": severity_counts[severity],
        }
        for severity in SEVERITIES
    ]

    return {
        "tenant_id": tenant_id,
        "total_devices": total_devices,
        "active_collectors": active_collectors,
        "inactive_collectors": inactive_collectors,
        "healthy_devices": healthy_devices,
        "warning_devices": warning_devices,
        "critical_devices": critical_devices,
        "offline_devices": offline_devices,
        "total_events": total_events,
        "critical_events": severity_counts["critical"],
        "events_by_severity": events_by_severity,
        "latest_metrics": latest_metrics,
    }