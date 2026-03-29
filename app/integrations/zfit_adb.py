import subprocess
import sqlite3
import os

from app.core.config import settings

REMOTE_PATH = settings.fitpro_remote_path
LOCAL_PATH = settings.fitpro_local_path


def pull_db():
    print("Attempting to pull database via ADB...")
    try:
        result = subprocess.run(
            ["adb", "pull", REMOTE_PATH, LOCAL_PATH],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print("Successfully pulled fitPro.db via ADB.")
            return True
        print(f"ADB Pull failed: {result.stderr.strip()}")
        return False
    except Exception as e:
        print(f"ADB Error: {e}")
        return False


def get_latest_bp():
    if not os.path.exists(LOCAL_PATH):
        print(f"Local database {LOCAL_PATH} not found.")
        return None

    try:
        conn = sqlite3.connect(LOCAL_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT _id, DATE, H_BLOOD, L_BLOOD FROM MEASURE_BLOOD_MODEL ORDER BY _id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row
    except sqlite3.Error as e:
        print(f"SQLite error reading {LOCAL_PATH}: {e}")
        return None
