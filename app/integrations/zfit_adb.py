import subprocess
import sqlite3
import os

REMOTE_PATH = "/sdcard/Android/data/com.legend.simsonlab.app.android/db/fitPro"
LOCAL_PATH = "fitPro.db"

def pull_db():
    print("Attempting to pull database via ADB...")
    try:
        # We capture output so it fails gracefully if no ADB device is connected
        result = subprocess.run(["adb", "pull", REMOTE_PATH, LOCAL_PATH], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("Successfully pulled fitPro.db via ADB.")
            return True
        else:
            print(f"ADB Pull failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"ADB Error: {e}")
        return False

def get_latest_bp():
    """Reads the local fitPro.db and returns the latest measurement."""
    if not os.path.exists(LOCAL_PATH):
        print(f"Local database {LOCAL_PATH} not found.")
        return None

    try:
        conn = sqlite3.connect(LOCAL_PATH)
        cursor = conn.cursor()
        
        # Based on schema inspection:
        # col2 = DATE (unix ms)
        # col3 = H_BLOOD (systolic)
        # col4 = L_BLOOD (diastolic)
        cursor.execute("SELECT _id, DATE, H_BLOOD, L_BLOOD FROM MEASURE_BLOOD_MODEL ORDER BY _id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row
    except sqlite3.Error as e:
        print(f"SQLite error reading {LOCAL_PATH}: {e}")
        return None
