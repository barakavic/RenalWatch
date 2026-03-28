import time
import httpx
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.integrations.zfit_adb import pull_db, get_latest_bp

API_URL = "http://localhost:8001/readings/"
POLL_INTERVAL = 10 # Testing slightly faster polling

def start_worker():
    print("Starting ADB Worker... Polling every 10 seconds.")
    last_seen_id = None
    
    while True:
        try:
            # 1. Optionall pull via ADB (will fail gracefully to local read if no device)
            pull_db()
            
            # 2. Read latest row from fitPro.db
            row = get_latest_bp()
            if not row:
                print("Waiting for fitPro.db or table to initialize...")
                time.sleep(POLL_INTERVAL)
                continue
                
            _id, timestamp_ms, systolic, diastolic = row
            
            # 3. If new reading (different _id from last seen):
            if _id != last_seen_id:
                print(f"NEW READING DETECTED: ID={_id}, BP={systolic}/{diastolic}")
                
                # Convert Unix timestamp ms to ISO format datetime string
                dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
                
                # 3a. POST to /readings/ endpoint
                payload = {
                    "systolic": systolic,
                    "diastolic": diastolic,
                    "timestamp": dt.isoformat(),
                    "source": "wearable",
                    "patient_id": 1
                }
                
                response = httpx.post(API_URL, json=payload, timeout=5)
                if response.status_code == 200:
                    print("Successfully sent to FastAPI /readings!")
                    # 3b. Update last_seen_id
                    last_seen_id = _id
                else:
                    print(f"Failed to send. API response: {response.text}")
            else:
                print(f"No new data. Current ID = {_id}")
                
        except httpx.RequestError as e:
             print(f"Connection error (FastAPI might be down): {e}")
        except Exception as e:
             print(f"Unexpected Error: {e}")
             
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    start_worker()
