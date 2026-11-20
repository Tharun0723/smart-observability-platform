from datetime import datetime, timezone
import uuid


def correlate_anomalies(anomalies):

    if not anomalies:
        return None

    detected_metrics = {}

    for anomaly in anomalies:
        detected_metrics[anomaly["metric"]] = {
            "current_value": anomaly["current_value"],
            "z_score": anomaly["z_score"],
            "anomaly_type": anomaly["anomaly_type"]
        }

    incident = {
        "incident_id": f"INC-{uuid.uuid4().hex[:8]}",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "anomaly_type": (
            "multiple_metric_anomaly"
            if len(anomalies) > 1
            else "single_metric_anomaly"
        ),
        "number_of_anomalies": len(anomalies),
        "detected_metrics": detected_metrics,
        "evidence": [
            f"{metric} is behaving abnormally"
            for metric in detected_metrics
        ]
    }

    return incident


if __name__ == "__main__":

    sample_anomalies = [
        {
            "metric": "cpu_percent",
            "current_value": 96,
            "z_score": 5.2,
            "anomaly_type": "high"
        },
        {
            "metric": "memory_percent",
            "current_value": 92,
            "z_score": 4.5,
            "anomaly_type": "high"
        },
        {
            "metric": "latency_ms",
            "current_value": 2500,
            "z_score": 6.1,
            "anomaly_type": "high"
        }
    ]

    result = correlate_anomalies(sample_anomalies)

    print("\nAIOPS INCIDENT CORRELATION")
    print("-------------------------")

    for key, value in result.items():
        print(f"\n{key}: {value}")
