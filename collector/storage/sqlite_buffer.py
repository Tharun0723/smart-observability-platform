
import sqlite3
import json
from pathlib import Path


DB_PATH = Path("data") / "collector_buffer.db"


def initialize_database():
    """Create the local telemetry buffer database."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_buffer (
                event_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                retry_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def store_event(event_id, payload):
    """Store an approved telemetry event locally."""

    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError("A valid event ID is required")

    if not isinstance(payload, dict):
        raise TypeError("Payload must be a dictionary")

    serialized_payload = json.dumps(
        payload,
        allow_nan=False
    )

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            INSERT OR IGNORE INTO telemetry_buffer
            (event_id, payload)
            VALUES (?, ?)
        """, (event_id, serialized_payload))


def get_pending_events(limit=100):
    """Retrieve events waiting for transmission."""

    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("Limit must be a positive integer")

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute("""
            SELECT event_id, payload, retry_count
            FROM telemetry_buffer
            WHERE status = 'pending'
            ORDER BY created_at
            LIMIT ?
        """, (limit,)).fetchall()

    return [
        {
            "event_id": row["event_id"],
            "payload": json.loads(row["payload"]),
            "retry_count": row["retry_count"]
        }
        for row in rows
    ]


def mark_event_sent(event_id):
    """Mark an event as successfully delivered."""

    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute("""
            UPDATE telemetry_buffer
            SET status = 'sent'
            WHERE event_id = ? AND status = 'pending'
        """, (event_id,))

        return cursor.rowcount == 1


def increment_retry(event_id):
    """Increase the retry count for a pending event."""

    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute("""
            UPDATE telemetry_buffer
            SET retry_count = retry_count + 1
            WHERE event_id = ? AND status = 'pending'
        """, (event_id,))

        return cursor.rowcount == 1


if __name__ == "__main__":
    initialize_database()

    sample_event = {
        "cpu_percent": 45.5,
        "memory_percent": 70.2
    }

    store_event("test-event-001", sample_event)

    # Test duplicate event protection
    store_event("test-event-001", sample_event)

    print("AegisOps SQLite Buffer Test")
    print("Pending events:")
    print(get_pending_events())