import math


def detect_anomalies(current_metrics, baseline, z_threshold=3):

    anomalies = []

    for metric, current_value in current_metrics.items():

        if metric not in baseline:
            continue

        if not isinstance(current_value, (int, float)) or isinstance(current_value, bool):
            continue

        if not math.isfinite(current_value):
            continue

        historical = baseline[metric]

        if historical["count"] < 5:
            continue

        mean = historical["mean"]
        std_dev = historical["std_dev"]

        if std_dev <= 0:
            continue

        z_score = (current_value - mean) / std_dev

        if abs(z_score) > z_threshold:

            anomalies.append({
                "metric": metric,
                "current_value": current_value,
                "historical_average": mean,
                "z_score": round(z_score, 2),
                "anomaly_type": "high" if z_score > 0 else "low"
            })

    return anomalies


if __name__ == "__main__":

    from baseline import calculate_baseline

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

    baseline = calculate_baseline(historical_data)

    results = detect_anomalies(current_metrics, baseline)

    print("\nAIOPS ANOMALY DETECTION")
    print("----------------------")

    if results:
        for anomaly in results:
            print(f"\nAnomaly detected: {anomaly['metric']}")
            for key, value in anomaly.items():
                print(f"{key}: {value}")
    else:
        print("No anomalies detected.")
