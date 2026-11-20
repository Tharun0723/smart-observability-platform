def generate_explanation(incident):

    metrics = incident["detected_metrics"]

    explanations = []
    recommendations = []

    if "cpu_percent" in metrics:
        value = metrics["cpu_percent"]["current_value"]

        explanations.append(
            f"CPU usage has increased abnormally to {value}%."
        )

        recommendations.append(
            "Inspect resource-intensive processes."
        )

    if "memory_percent" in metrics:
        value = metrics["memory_percent"]["current_value"]

        explanations.append(
            f"Memory usage has increased abnormally to {value}%."
        )

        recommendations.append(
            "Check memory consumption and possible memory leaks."
        )

    if "latency_ms" in metrics:
        value = metrics["latency_ms"]["current_value"]

        explanations.append(
            f"Network or application latency has increased to {value} ms."
        )

        recommendations.append(
            "Investigate network delays and application response times."
        )

    if "disk_percent" in metrics:
        value = metrics["disk_percent"]["current_value"]

        explanations.append(
            f"Disk utilization is abnormal at {value}%."
        )

        recommendations.append(
            "Check disk space and remove unnecessary files if appropriate."
        )

    if "packet_loss_percent" in metrics:
        value = metrics["packet_loss_percent"]["current_value"]

        explanations.append(
            f"Packet loss has increased to {value}%."
        )

        recommendations.append(
            "Investigate network connectivity and packet loss."
        )

    if "bandwidth_mbps" in metrics:
        value = metrics["bandwidth_mbps"]["current_value"]

        explanations.append(
            f"Bandwidth usage is abnormal at {value} Mbps."
        )

        recommendations.append(
            "Inspect network traffic for unexpected bandwidth consumption."
        )

    return {
        "explanation": " ".join(explanations),
        "recommendations": recommendations
    }


if __name__ == "__main__":

    sample_incident = {
        "detected_metrics": {
            "cpu_percent": {"current_value": 96},
            "memory_percent": {"current_value": 92},
            "latency_ms": {"current_value": 2500}
        }
    }

    result = generate_explanation(sample_incident)

    print("\nAI INCIDENT EXPLANATION")
    print("----------------------")
    print("Explanation:", result["explanation"])

    print("\nRecommendations:")

    for recommendation in result["recommendations"]:
        print("-", recommendation)
