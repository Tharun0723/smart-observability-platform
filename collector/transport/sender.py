
import os
import math
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()

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
    "cpu_percent", "memory_percent",
    "disk_percent", "packet_loss_percent",
}

NON_NEGATIVE_FIELDS = {
    "bandwidth_mbps", "latency_ms",
    "network_sent_bytes", "network_received_bytes",
}

UNITS = {
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
    if not isinstance(payload, dict) or not payload:
        raise ValueError("Payload must be a non-empty dictionary")

    for key, value in payload.items():
        if key not in ALLOWED_FIELDS:
            raise ValueError(f"Unapproved field: {key}")

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
    """Convert collector metrics to the FastAPI MetricBatch schema."""

    validate_outbound_payload(payload)
    timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "metrics": [
            {
                "metric_name": METRIC_NAME_MAP[key],
                "value": value,
                "unit": UNITS[key],
                "recorded_at": timestamp,
            }
            for key, value in payload.items()
        ]
    }


def send_telemetry(payload):
    """Send approved metadata to the FastAPI backend."""

    backend_url = os.getenv("BACKEND_URL")
    collector_secret = os.getenv("COLLECTOR_SECRET")

    if not backend_url or not collector_secret:
        raise ValueError("BACKEND_URL and COLLECTOR_SECRET are required")

    parsed = urlparse(backend_url)

    if parsed.scheme != "https" and not (
        parsed.scheme == "http"
        and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    ):
        raise ValueError("HTTPS is required except for localhost testing")

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
        return {"success": False, "error": "Request timed out"}

    except httpx.HTTPStatusError as error:
        return {
            "success": False,
            "error": f"Backend returned HTTP {error.response.status_code}",
        }

    except httpx.RequestError:
        return {"success": False, "error": "Network connection failed"}
