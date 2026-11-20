from baseline import calculate_baseline
from anomaly_detector import detect_anomalies
from incident_correlator import correlate_anomalies
from severity_classifier import classify_severity
from ai_explainer import generate_explanation


def run_aiops_engine(historical_data, current_metrics):

    baseline = calculate_baseline(historical_data)

    anomalies = detect_anomalies(current_metrics, baseline)

    if not anomalies:
        return {
            "status": "healthy",
            "message": "No anomalies detected."
        }

    incident = correlate_anomalies(anomalies)

    incident["severity"] = classify_severity(anomalies)

    explanation = generate_explanation(incident)

    incident.update(explanation)

    incident["status"] = "incident_detected"

    return incident


if __name__ == "__main__":

    historical_data = [
        {"cpu_percent": 30, "memory_percent": 45, "latency_ms": 100},
        {"cpu_percent": 32, "memory_percent": 46, "latency_ms": 105},
        {"cpu_percent": 29, "memory_percent": 44, "latency_ms": 98},
        {"cpu_percent": 31, "memory_percent": 45, "latency_ms": 102},
        {"cpu_percent": 30, "memory_percent": 47, "latency_ms": 101}
    ]

    current_metrics = {
        "cpu_percent": 95,
        "memory_percent": 46,
        "latency_ms": 101
    }

    result = run_aiops_engine(historical_data, current_metrics)

    print("\n========== AEGISOPS INTELLIGENCE ENGINE ==========")

    import json
    print(json.dumps(result, indent=4))
