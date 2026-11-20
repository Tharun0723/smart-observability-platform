from baseline import calculate_baseline
from anomaly_detector import detect_anomalies
from ml_detector import detect_ml_anomaly
from incident_correlator import correlate_anomalies
from severity_classifier import classify_severity
from ai_explainer import generate_explanation

from datetime import datetime, timezone
import uuid


def run_aiops_engine(historical_data, current_metrics):

    # 1. Calculate historical baseline
    baseline = calculate_baseline(historical_data)

    # 2. Statistical anomaly detection
    statistical_anomalies = detect_anomalies(
        current_metrics,
        baseline
    )

    # 3. Machine learning anomaly detection
    ml_result = detect_ml_anomaly(
        historical_data,
        current_metrics
    )

    ml_detected = (
        ml_result.get("ml_status") == "success"
        and ml_result.get("ml_anomaly", False)
    )

    # 4. Check whether either detector found an anomaly
    if not statistical_anomalies and not ml_detected:
        return {
            "status": "healthy",
            "message": "No anomalies detected.",
            "statistical_detection": statistical_anomalies,
            "ml_detection": ml_result
        }

    # 5. Create incident
    if statistical_anomalies:

        incident = correlate_anomalies(
            statistical_anomalies
        )

    else:

        incident = {
            "incident_id": f"INC-{uuid.uuid4().hex[:8]}",
            "timestamp_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "anomaly_type": "ml_pattern_anomaly",
            "number_of_anomalies": 0,
            "detected_metrics": {},
            "evidence": [
                "Isolation Forest detected an unusual combination of metrics."
            ]
        }

    # 6. Classify severity
    if statistical_anomalies:
        incident["severity"] = classify_severity(
            statistical_anomalies
        )
        incident["severity_basis"] = "Z-score statistical analysis"

    else:
        incident["severity"] = "MEDIUM"
        incident["severity_basis"] = (
            "Provisional severity for ML-only detection"
        )

    # 7. Generate explanation
    if statistical_anomalies:

        explanation = generate_explanation(incident)

    else:

        explanation = {
            "explanation": (
                "Machine learning detected an unusual combination "
                "of infrastructure metrics."
            ),
            "recommendations": [
                "Investigate recent changes in infrastructure activity.",
                "Review CPU, memory and network utilization.",
                "Compare current telemetry with historical patterns."
            ]
        }

    incident.update(explanation)

    # 8. Attach ML results
    incident["statistical_detection"] = {
        "anomaly_count": len(statistical_anomalies),
        "anomalies": statistical_anomalies
    }

    incident["ml_detection"] = ml_result

    # 9. Final incident status
    incident["status"] = "incident_detected"

    return incident


if __name__ == "__main__":

    import json

    historical_data = [
        {"cpu_percent": 30, "memory_percent": 45, "latency_ms": 100},
        {"cpu_percent": 32, "memory_percent": 46, "latency_ms": 105},
        {"cpu_percent": 29, "memory_percent": 44, "latency_ms": 98},
        {"cpu_percent": 31, "memory_percent": 45, "latency_ms": 102},
        {"cpu_percent": 30, "memory_percent": 47, "latency_ms": 101}
    ]

    current_metrics = {
        "cpu_percent": 95,
        "memory_percent": 90,
        "latency_ms": 500
    }

    result = run_aiops_engine(
        historical_data,
        current_metrics
    )

    print("\n========== AEGISOPS HYBRID AIOPS ENGINE ==========")

    print(json.dumps(result, indent=4))