def classify_severity(anomalies):

    if not anomalies:
        return "LOW"

    max_z_score = max(
        abs(anomaly["z_score"])
        for anomaly in anomalies
    )

    if max_z_score >= 10:
        return "CRITICAL"

    elif max_z_score >= 5:
        return "HIGH"

    elif max_z_score >= 3:
        return "MEDIUM"

    return "LOW"


if __name__ == "__main__":

    sample_anomalies = [
        {"metric": "cpu_percent", "z_score": 5.2},
        {"metric": "memory_percent", "z_score": 4.5},
        {"metric": "latency_ms", "z_score": 6.1}
    ]

    severity = classify_severity(sample_anomalies)

    print("\nINCIDENT SEVERITY")
    print("-----------------")
    print("Severity:", severity)
