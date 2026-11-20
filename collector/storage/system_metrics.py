
import psutil
import time


def collect_system_metrics():
    """Collect basic system performance metrics."""

    cpu_percent = psutil.cpu_percent(interval=1)

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    network_before = psutil.net_io_counters()
    time.sleep(1)
    network_after = psutil.net_io_counters()

    bytes_sent = network_after.bytes_sent - network_before.bytes_sent
    bytes_received = network_after.bytes_recv - network_before.bytes_recv

    return {
        "cpu_percent": round(cpu_percent, 2),
        "memory_percent": round(memory.percent, 2),
        "disk_percent": round(disk.percent, 2),
        "network_sent_bytes": bytes_sent,
        "network_received_bytes": bytes_received
    }


if __name__ == "__main__":
    metrics = collect_system_metrics()
    print("AegisOps System Metrics:")
    print(metrics)

