import math

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


def validate_metrics(metrics):
    """Validate telemetry before transmission."""

    if not isinstance(metrics, dict):
        raise TypeError("Metrics must be a dictionary")

    validated = {}

    for key, value in metrics.items():

        if key not in ALLOWED_FIELDS:
            raise ValueError(f"Unapproved metric field: {key}")

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} must be numeric")

        if not math.isfinite(value):
            raise ValueError(f"{key} must be a finite number")

        if key in PERCENTAGE_FIELDS and not 0 <= value <= 100:
            raise ValueError(f"{key} must be between 0 and 100")

        if key in {
            "bandwidth_mbps",
            "latency_ms",
            "network_sent_bytes",
            "network_received_bytes"
        } and value < 0:
            raise ValueError(f"{key} cannot be negative")

        validated[key] = value

    return validated


if __name__ == "__main__":

    sample_metrics = {
        "cpu_percent": 45.5,
        "memory_percent": 70.2,
        "disk_percent": 60.0,
        "bandwidth_mbps": 12.5,
        "latency_ms": 45
    }

    print("AegisOps Metric Validation Test")
    print(validate_metrics(sample_metrics))
    print("\nTesting invalid metric:")

    try:
        validate_metrics({"cpu_percent": 150})
    except ValueError as error:
        print("Correctly rejected:", error)
