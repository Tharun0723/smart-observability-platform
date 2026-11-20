
import os
import math
import httpx


# ==========================================
# 1. APPROVED TELEMETRY FIELDS
# ==========================================

ALLOWED_FIELDS = {
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "bandwidth_mbps",
    "latency_ms",
    "packet_loss_percent",
    "network_sent_bytes",
    "network_received_bytes"
}

PERCENTAGE_FIELDS = {
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "packet_loss_percent"
}

NON_NEGATIVE_FIELDS = {
    "bandwidth_mbps",
    "latency_ms",
    "network_sent_bytes",
    "network_received_bytes"
}


# ==========================================
# 2. OUTBOUND PAYLOAD VALIDATION
# ==========================================

def validate_outbound_payload(payload):
    """
    Validate telemetry before transmission.
    Reject unapproved fields and invalid values.
    """

    if not isinstance(payload, dict):
        raise TypeError("Payload must be a dictionary")

    if not payload:
        raise ValueError("Payload cannot be empty")

    for key, value in payload.items():

        if key not in ALLOWED_FIELDS:
            raise ValueError(
                f"Blocked unapproved field: {key}"
            )

        if isinstance(value, bool) or not isinstance(
            value, (int, float)
        ):
            raise ValueError(
                f"{key} must be numeric"
            )

        if not math.isfinite(value):
            raise ValueError(
                f"{key} must be finite"
            )

        if key in PERCENTAGE_FIELDS:
            if not 0 <= value <= 100:
                raise ValueError(
                    f"{key} must be between 0 and 100"
                )

        if key in NON_NEGATIVE_FIELDS:
            if value < 0:
                raise ValueError(
                    f"{key} cannot be negative"
                )

    return payload


# ==========================================
# 3. SECURE TELEMETRY TRANSMISSION
# ==========================================

def send_telemetry(payload):
    """
    Send approved telemetry to the backend.

    Security features:
    - HTTPS enforcement
    - TLS certificate verification
    - Bearer token authentication
    - Strict payload validation
    - Request timeout
    - HTTP error handling
    """

    # Validate before any network request.
    validate_outbound_payload(payload)

    backend_url = os.getenv("BACKEND_URL")
    api_token = os.getenv("BACKEND_API_TOKEN")

    if not backend_url:
        raise ValueError(
            "BACKEND_URL is not configured"
        )

    if not api_token:
        raise ValueError(
            "BACKEND_API_TOKEN is not configured"
        )

    if not backend_url.lower().startswith("https://"):
        raise ValueError(
            "Only HTTPS backend URLs are allowed"
        )

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        with httpx.Client(
            timeout=10.0,
            verify=True
        ) as client:

            response = client.post(
                backend_url,
                json=payload,
                headers=headers
            )

            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code
            }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Request timed out"
        }

    except httpx.HTTPStatusError as error:
        return {
            "success": False,
            "error": (
                f"Backend returned HTTP "
                f"{error.response.status_code}"
            )
        }

    except httpx.RequestError:
        return {
            "success": False,
            "error": "Network connection failed"
        }


# ==========================================
# 4. MODULE EXECUTION TEST
# ==========================================

if __name__ == "__main__":

    print("AegisOps Secure Sender Module")
    print("--------------------------------")

    print("HTTPS enforcement: Enabled")
    print("TLS verification: Enabled")
    print("Authentication: Environment variable")
    print("Strict payload validation: Enabled")
    print("Request timeout: 10 seconds")

    print("--------------------------------")
    print("Sender module loaded successfully.")

