import os
import shutil
import subprocess
import time
from pathlib import Path

REMOTE_PATH = os.getenv(
    "FITPRO_REMOTE_PATH",
    "/sdcard/Android/data/com.legend.simsonlab.app.android/db/fitPro",
)
LOCAL_PATH = Path(os.getenv("FITPRO_LOCAL_PATH", "fitPro.db"))
TMP_PATH = LOCAL_PATH.with_suffix(LOCAL_PATH.suffix + ".tmp")
SYNC_INTERVAL = int(os.getenv("FITPRO_SYNC_INTERVAL", "10"))


def sync_once() -> bool:
    result = subprocess.run(
        ["adb", "pull", REMOTE_PATH, str(TMP_PATH)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip() or "Unknown adb pull error"
        print(f"fitPro sync failed: {error}")
        return False

    shutil.move(str(TMP_PATH), str(LOCAL_PATH))
    print(f"fitPro sync ok -> {LOCAL_PATH}")
    return True


def main() -> None:
    print(f"Starting fitPro sync loop. Remote={REMOTE_PATH} Local={LOCAL_PATH} Every={SYNC_INTERVAL}s")
    while True:
        try:
            sync_once()
        except Exception as exc:
            print(f"fitPro sync error: {exc}")
        time.sleep(SYNC_INTERVAL)


if __name__ == "__main__":
    main()
