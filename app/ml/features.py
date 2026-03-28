import numpy as np
from typing import Optional

def engineer_features(
    systolic: float,
    diastolic: float,
    history: list[dict]  # list of recent readings from DB, newest first
) -> dict:
    """
    Computes all 8 features the Isolation Forest expects.
    history: list of dicts with keys 'systolic', each from DB ordered newest first.
    Cold start: if fewer than 5 readings in history, time-series features default safely.
    """

    
    pulse_pressure = systolic - diastolic
    map_value      = diastolic + (pulse_pressure / 3)

    
    history_sys = [r['systolic'] for r in history]

    cold_start = len(history_sys) < 5

    if len(history_sys) >= 1:
        delta_1 = systolic - history_sys[0]
    else:
        delta_1 = 0.0

    if len(history_sys) >= 3:
        delta_3 = systolic - history_sys[2]
    else:
        delta_3 = 0.0

    if len(history_sys) >= 1:
        recent = history_sys[:5]
        rolling_mean_5 = np.mean(recent)
        rolling_std_5  = float(np.std(recent)) if len(recent) > 1 else 0.0
    else:
        rolling_mean_5 = systolic
        rolling_std_5  = 0.0

    return {
        "systolic":        systolic,
        "diastolic":       diastolic,
        "pulse_pressure":  pulse_pressure,
        "map":             map_value,
        "rolling_mean_5":  rolling_mean_5,
        "rolling_std_5":   rolling_std_5,
        "delta_1":         delta_1,
        "delta_3":         delta_3,
        "cold_start":      cold_start   # passed to anomaly.py, not fed to model
    }