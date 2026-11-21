import os
import time
import uuid

from dotenv import load_dotenv

load_dotenv()

from collector.sources.system_metrics import collect_system_metrics
from collector.privacy.privacy_filter import filter_approved_metrics
from collector.processing.validator import validate_metrics
from collector.storage.sqlite_buffer import (
    initialize_database,
    store_event,
    get_pending_events,
    mark_event_sent,
    increment_retry,
)
from collector.transport.sender import send_telemetry


def flush_pending():
    events = get_pending_events(limit=100)

    for event in events:
        result = send_telemetry(event["payload"])

        if result.get("success"):
            mark_event_sent(event["event_id"])
            print(
                f"[SENT] {result['accepted']} metrics "
                f"| Tenant {result['tenant_id']}"
            )
        else:
            increment_retry(event["event_id"])
            print("[RETRY]", result.get("error"))
            break


def collect_once():
    raw_metrics = collect_system_metrics()

    approved_metrics = filter_approved_metrics(raw_metrics)
    validated_metrics = validate_metrics(approved_metrics)

    event_id = str(uuid.uuid4())
    store_event(event_id, validated_metrics)

    print("[COLLECTED]", validated_metrics)

    flush_pending()


def main():
    if not os.getenv("BACKEND_URL") or not os.getenv("COLLECTOR_SECRET"):
        raise RuntimeError("Backend configuration missing from .env")

    initialize_database()

    print("CICADA Continuous Collector Started")
    print("Collection interval: 10 seconds")
    print("Press Ctrl+C to stop")

    while True:
        started = time.monotonic()

        try:
            collect_once()
        except Exception as error:
            print("[ERROR]", type(error).__name__, str(error))

        elapsed = time.monotonic() - started
        time.sleep(max(0, 10 - elapsed))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCICADA Collector stopped.")
