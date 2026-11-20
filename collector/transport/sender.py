
import os
import math
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx


# Raw collector field -> backend database metric name
METRIC_NAME_MAP = {
    "cpu_percent": "cpu_usage_percent",
    "memory_percent": "memory_usage_percent",
    "disk_percent": "disk_usage_percent",
    "bandwidth_mbps": "bandwidth_mbps",
    "latency_ms": "latency_ms",
    "packet_loss_percent": "packet_loss_percent",
    "network_sent_bytes": "network_bytes_sent",
    "network_received_bytes": "network_bytes_received",
}

ALLOWED_FIELDS = set(METRIC_NAME_MAP)

PERCENTAGE_FIELDS = {
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "packet_loss_percent",
}

NON_NEGATIVE_FIELDS = {
    "bandwidth_mbps",
    "latency_ms",
    "network_sent_bytes",
    "network_received_bytes",
}

METRIC_UNITS = {
    "cpu_percent": "%",
    "memory_percent": "%",
    "disk_percent": "%",
    "bandwidth_mbps": "Mbps",
    "latency_ms": "ms",
    "packet_loss_percent": "%",
    "network_sent_bytes": "bytes",
    "network_received_bytes": "bytes",
}


def validate_outbound_payload(payload):
    """Reject unapproved fields and invalid metric values."""

    if not isinstance(payload, dict):
        raise TypeError("Payload must be a dictionary")

    if not payload:
        raise ValueError("Payload cannot be empty")

    for key, value in payload.items():

        if key not in ALLOWED_FIELDS:
            raise ValueError(f"Blocked unapproved field: {key}")

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} must be numeric")

        if not math.isfinite(value):
            raise ValueError(f"{key} must be finite")

        if key in PERCENTAGE_FIELDS and not 0 <= value <= 100:
            raise ValueError(f"{key} must be between 0 and 100")

        if key in NON_NEGATIVE_FIELDS and value < 0:
            raise ValueError(f"{key} cannot be negative")

    return payload


def build_backend_payload(payload):
    """
    Convert collector metrics into the backend MetricBatch schema.

    Backend expects:
    {
        "metrics": [
            {
                "metric_name": "...",
                "value": 45.0,
                "unit": "%",
                "recorded_at": "UTC timestamp"
            }
        ]
    }
    """

    validate_outbound_payload(payload)

    recorded_at = datetime.now(timezone.utc).isoformat()

    metrics = []

    for field, value in payload.items():
        metrics.append({
            "metric_name": METRIC_NAME_MAP[field],
            "value": value,
            "unit": METRIC_UNITS[field],
            "recorded_at": recorded_at,
        })

    return {"metrics": metrics}


def validate_backend_url(backend_url):
    """Allow HTTPS, or HTTP only for local development."""

    parsed = urlparse(backend_url)

    if parsed.scheme == "https":
        return

    local_hosts = {"localhost", "127.0.0.1", "::1"}

    if parsed.scheme == "http" and parsed.hostname in local_hosts:
        return

    raise ValueError(
        "Backend must use HTTPS. HTTP is allowed only for localhost testing."
    )


def send_telemetry(payload):
    """
    Send approved telemetry to the CICADA FastAPI backend.

    Authentication:
        X-Collector-Secret

    Endpoint:
        POST /api/v1/metrics
    """

    backend_url = os.getenv("BACKEND_URL")
    collector_secret = os.getenv("COLLECTOR_SECRET")

    if not backend_url:
        raise ValueError("BACKEND_URL is not configured")

    if not collector_secret:
        raise ValueError("COLLECTOR_SECRET is not configured")

    validate_backend_url(backend_url)

    # Construct and validate the exact backend payload.
    backend_payload = build_backend_payload(payload)

    headers = {
        "X-Collector-Secret": collector_secret,
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=10.0, verify=True) as client:

            response = client.post(
                backend_url,
                json=backend_payload,
                headers=headers,
            )

            response.raise_for_status()

            result = response.json()

            return {
                "success": True,
                "status_code": response.status_code,
                "accepted": result.get("accepted", 0),
                "collector_id": result.get("collector_id"),
                "tenant_id": result.get("tenant_id"),
            }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Request timed out",
        }

    except httpx.HTTPStatusError as error:
        return {
            "success": False,
            "error": f"Backend returned HTTP {error.response.status_code}",
        }

    except httpx.RequestError:
        return {
            "success": False,
            "error": "Network connection failed",
        }


if __name__ == "__main__":

    print("CICADA Secure Collector Sender")
    print("--------------------------------")

    sample_metrics = {
        "cpu_percent": 45.5,
        "memory_percent": 70.2,
        "disk_percent": 60.0,
        "network_sent_bytes": 1024,
        "network_received_bytes": 2048,
    }

    print("Testing telemetry validation...")
    validate_outbound_payload(sample_metrics)

    print("Testing backend payload conversion...")
    print(build_backend_payload(sample_metrics))

    print("--------------------------------")
    print("Sender module loaded successfully.")


