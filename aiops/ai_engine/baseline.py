import statistics
import math


def calculate_baseline(telemetry):
    """
    Calculate historical baselines for server metrics.
    """

    metrics = [
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "bandwidth_mbps",
        "latency_ms",
        "packet_loss_percent"
    ]

    baseline = {}

    for metric in metrics:

        values = [
            record[metric]
            for record in telemetry
            if isinstance(record.get(metric), (int, float))
            and not isinstance(record.get(metric), bool)
            and math.isfinite(record[metric])
        ]

        if not values:
            continue

        baseline[metric] = {
            "count": len(values),
            "mean": round(statistics.mean(values), 2),
            "std_dev": round(statistics.pstdev(values), 2),
            "min": min(values),
            "max": max(values)
        }

    return baseline


if __name__ == "__main__":

    historical_data = [
        {"cpu_percent": 30, "memory_percent": 45, "latency_ms": 100},
        {"cpu_percent": 32, "memory_percent": 46, "latency_ms": 105},
        {"cpu_percent": 29, "memory_percent": 44, "latency_ms": 98},
        {"cpu_percent": 31, "memory_percent": 45, "latency_ms": 102},
        {"cpu_percent": 30, "memory_percent": 47, "latency_ms": 101}
    ]

    result = calculate_baseline(historical_data)

    print("\nSERVER BASELINE ANALYSIS")
    print("-----------------------")

    for metric, values in result.items():
        print(f"\nMetric: {metric}")
        for key, value in values.items():
            print(f"{key}: {value}")
