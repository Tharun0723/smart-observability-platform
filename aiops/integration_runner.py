import os
import sys
import time
import json
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
ENGINE = ROOT / "aiops" / "ai_engine"

load_dotenv(ROOT / ".env")
load_dotenv(BACKEND / ".env", override=True)

sys.path.insert(0, str(ENGINE))

from main import run_aiops_engine

BASE_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000/api/v1/metrics"
).split("/api/v1/")[0].rstrip("/")

ADMIN_KEY = os.getenv("ADMIN_API_KEY")
AIOPS_KEY = os.getenv("AIOPS_API_KEY")
TENANT_ID = 1

METRIC_MAP = {
    "cpu_usage_percent": "cpu_percent",
    "memory_usage_percent": "memory_percent",
    "disk_usage_percent": "disk_percent",
    "bandwidth_mbps": "bandwidth_mbps",
    "latency_ms": "latency_ms",
    "packet_loss_percent": "packet_loss_percent",
}


def fetch_history():
    response = httpx.get(
        f"{BASE_URL}/api/v1/admin/tenants/{TENANT_ID}/metrics",
        params={"limit": 200},
        headers={"X-Admin-API-Key": ADMIN_KEY},
        timeout=10
    )
    response.raise_for_status()

    rows = response.json()
    snapshots = defaultdict(dict)

    for row in rows:
        name = METRIC_MAP.get(row["metric_name"])
        if name:
            timestamp = row["recorded_at"]
            snapshots[timestamp][name] = float(row["value"])

    ordered = []
    for timestamp, metrics in snapshots.items():
        if metrics:
            ordered.append((timestamp, metrics))

    ordered.sort(key=lambda item: item[0])

    if len(ordered) < 6:
        print(f"[WAITING] Need 6 metric snapshots; found {len(ordered)}")
        return None

    historical = [item[1] for item in ordered[:-1]]
    current = ordered[-1][1]
    current_timestamp = ordered[-1][0]

    if len(historical) < 5:
        return None

    return historical, current, current_timestamp


def submit_incident(incident, current_timestamp):
    detected = incident.get("detected_metrics", {})
    anomaly_type = incident.get("anomaly_type", "infrastructure_anomaly")

    metric_names = sorted(detected.keys())
    fingerprint_source = f"tenant-{TENANT_ID}:{anomaly_type}:{','.join(metric_names)}"
    fingerprint = hashlib.sha256(
        fingerprint_source.encode()
    ).hexdigest()[:32]

    severity = incident.get("severity", "MEDIUM").lower()
    if severity not in ("low", "medium", "high", "critical"):
        severity = "medium"

    title = f"{severity.upper()} infrastructure anomaly: {anomaly_type}"

    explanation = incident.get(
        "explanation",
        "The AIOps engine detected an unusual infrastructure pattern."
    )

    evidence = incident.get("evidence", [])
    description = explanation
    if evidence:
        description += "\nEvidence: " + "; ".join(map(str, evidence))

    recommendations = incident.get("recommendations", [])
    recommendation = " ".join(map(str, recommendations))

    occurred_at = incident.get("timestamp_utc") or current_timestamp

    payload = {
        "fingerprint": fingerprint,
        "title": title,
        "description": description,
        "source": "nexora_aiops_engine",
        "severity": severity,
        "priority": severity,
        "affected_resource": "tenant-1-infrastructure",
        "correlation_key": anomaly_type,
        "recommendation": recommendation,
        "occurred_at": occurred_at
    }

    response = httpx.post(
        f"{BASE_URL}/api/v1/aiops/tenants/{TENANT_ID}/incidents",
        json=payload,
        headers={"X-AIOps-API-Key": AIOPS_KEY},
        timeout=10
    )

    if response.is_success:
        print(f"[INCIDENT SENT] {title}")
        print(response.text[:1000])
    else:
        print(f"[INCIDENT ERROR] HTTP {response.status_code}")
        print(response.text[:2000])


def run_once():
    data = fetch_history()
    if not data:
        return

    historical, current, timestamp = data

    print(
        f"[AIOPS] Analyzing {len(historical)} historical snapshots "
        f"and current metrics: {current}"
    )

    result = run_aiops_engine(historical, current)

    if result.get("status") == "healthy":
        print("[AIOPS HEALTHY] No anomalies detected.")
        return

    print("[AIOPS INCIDENT DETECTED]")
    print(json.dumps(result, indent=2, default=str))
    submit_incident(result, timestamp)


def main():
    if not ADMIN_KEY or not AIOPS_KEY:
        print("[ERROR] ADMIN_API_KEY or AIOPS_API_KEY missing in backend/.env")
        return

    print("NEXORA AIOps Integration Runner")
    print(f"Backend: {BASE_URL}")
    print(f"Tenant: {TENANT_ID}")

    while True:
        try:
            run_once()
        except httpx.HTTPStatusError as error:
            print(
                f"[API ERROR] {error.response.status_code}: "
                f"{error.response.text[:1000]}"
            )
        except Exception as error:
            print(f"[AIOPS ERROR] {type(error).__name__}: {error}")

        if "--once" in sys.argv:
            break

        print("[AIOPS] Next analysis in 30 seconds.")
        time.sleep(30)


if __name__ == "__main__":
    main()
