import time
from datetime import datetime, timezone
import os
import sys

import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings
from app.integrations.zfit_adb import pull_db, get_latest_bp

API_URL = os.getenv("RENALWATCH_API_URL", settings.renalwatch_api_url)
POLL_INTERVAL = int(os.getenv("ADB_POLL_INTERVAL", str(settings.adb_poll_interval)))
WEARABLE_PATIENT_ID = int(os.getenv("WEARABLE_PATIENT_ID", str(settings.wearable_patient_id)))
ADB_PULL_ENABLED = os.getenv("ADB_PULL_ENABLED", str(settings.adb_pull_enabled)).lower() in {"1", "true", "yes", "on"}


def start_worker():
    print(f"Starting ADB Worker... Polling every {POLL_INTERVAL} seconds.")
    last_seen_id = None

    while True:
        try:
            if ADB_PULL_ENABLED:
                # In full ADB mode, refresh the local DB before reading it.
                pull_db()

            row = get_latest_bp()
            if not row:
                print("Waiting for fitPro.db or table to initialize...")
                time.sleep(POLL_INTERVAL)
                continue

            _id, timestamp_ms, systolic, diastolic = row

            if _id != last_seen_id:
                print(f"NEW READING DETECTED: ID={_id}, BP={systolic}/{diastolic}")
                dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)

                payload = {
                    "patient_id": WEARABLE_PATIENT_ID,
                    "systolic": systolic,
                    "diastolic": diastolic,
                    "timestamp": dt.isoformat(),
                    "source": "wearable",
                }

                response = httpx.post(API_URL, json=payload, timeout=10.0)
                if response.status_code in (200, 201):
                    print("Successfully sent reading to FastAPI /readings.")
                    last_seen_id = _id
                else:
                    print(f"Failed to send reading. Status={response.status_code}, Response={response.text}")
            else:
                print(f"No new data. Current ID = {_id}")

        except httpx.RequestError as e:
            print(f"Connection error (FastAPI might be down): {e}")
        except Exception as e:
            print(f"Unexpected Error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    start_worker()
