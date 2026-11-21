import re

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

SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?[^'\"\s,;]+"),
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret)\s*[:=]\s*['\"]?[^'\"\s,;]+"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
]


def redact_sensitive_text(text):
    if not isinstance(text, str):
        raise TypeError("Text must be a string")

    for pattern in SECRET_PATTERNS:
        if "@" in pattern.pattern:
            text = pattern.sub("[REDACTED_EMAIL]", text)
        else:
            text = pattern.sub("[REDACTED_SECRET]", text)

    return text


def filter_approved_metrics(metrics):
    if not isinstance(metrics, dict):
        raise TypeError("Metrics must be a dictionary")

    return {
        key: value
        for key, value in metrics.items()
        if key in ALLOWED_FIELDS
    }


if __name__ == "__main__":
    sample_text = "password=demo123 api_key=abc123 user=test@example.com"

    sample_metrics = {
        "cpu_percent": 45.5,
        "memory_percent": 70.2,
        "password": "demo123",
        "api_key": "abc123"
    }

    print("AegisOps Privacy Filter Test")
    print("Redacted text:")
    print(redact_sensitive_text(sample_text))

    print("\nApproved metrics:")
    print(filter_approved_metrics(sample_metrics))
