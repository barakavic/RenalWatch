import numpy as np
import joblib
from pathlib import Path
from app.ml.features import engineer_features

MODEL_DIR = Path(__file__).parent.parent.parent / "ml" / "models"

model         = joblib.load(MODEL_DIR / "isolation_forest.pkl")
scaler        = joblib.load(MODEL_DIR / "bp_scaler.pkl")
feature_names = joblib.load(MODEL_DIR / "feature_names.pkl")

SPIKE_DELTA_THRESHOLD  = 20   # mmHg rise in one reading = spike
DROP_DELTA_THRESHOLD   = -25  # mmHg drop in one reading = sudden drop
STD_SPIKE_THRESHOLD    = 15   # high rolling std = unstable progression

def spike_detector(features: dict) -> dict:
    """
    Rule-based progression detector.
    Catches what Isolation Forest misses — gradual dangerous trends.
    """
    flags  = []
    reason = []

    if features['delta_1'] >= SPIKE_DELTA_THRESHOLD:
        flags.append("sudden_spike")
        reason.append(
            f"BP rose {features['delta_1']:.0f} mmHg from previous reading"
        )

    if features['delta_1'] <= DROP_DELTA_THRESHOLD:
        flags.append("sudden_drop")
        reason.append(
            f"BP dropped {abs(features['delta_1']):.0f} mmHg from previous reading"
        )

    if features['delta_3'] >= SPIKE_DELTA_THRESHOLD * 2:
        flags.append("progressive_rise")
        reason.append(
            f"BP rose {features['delta_3']:.0f} mmHg over last 3 readings"
        )

    if features['rolling_std_5'] >= STD_SPIKE_THRESHOLD:
        flags.append("unstable_bp")
        reason.append(
            f"BP highly unstable — std deviation {features['rolling_std_5']:.1f} mmHg over last 5 readings"
        )

    return {
        "spike_detected": len(flags) > 0,
        "spike_flags":    flags,
        "spike_reasons":  reason
    }


def run_isolation_forest(features: dict) -> dict:
    """
    Runs the trained Isolation Forest on the engineered features.
    Returns anomaly flag + score.
    """
    # Build feature vector in exact training order
    X = np.array([[features[f] for f in feature_names]])

    X_scaled    = scaler.transform(X)
    prediction  = model.predict(X_scaled)[0]       # -1 = anomaly, 1 = normal
    score       = model.decision_function(X_scaled)[0]  # negative = more anomalous

    return {
        "if_anomaly": prediction == -1,
        "if_score":   round(float(score), 4)
    }


def detect(
    systolic:   float,
    diastolic:  float,
    history:    list[dict]   # newest first, each dict has 'systolic'
) -> dict:
    """
    Main entry point for anomaly detection.
    Combines Isolation Forest + spike rules into one unified result.

    Returns:
        is_anomaly    : bool   — final anomaly decision
        anomaly_score : float  — IF confidence score
        flags         : list   — list of triggered rule flags
        reasons       : list   — human-readable reason strings
        cold_start    : bool   — whether history was insufficient
        if_result     : dict   — raw IF output
        spike_result  : dict   — raw spike detector output
    """

 
    features = engineer_features(systolic, diastolic, history)
    cold_start = features.pop("cold_start")

   
    if_result = run_isolation_forest(features)

    
    # Skip spike detection during cold start — deltas are zeroed, unreliable
    if cold_start:
        spike_result = {
            "spike_detected": False,
            "spike_flags":    [],
            "spike_reasons":  ["Insufficient history for spike detection"]
        }
    else:
        spike_result = spike_detector(features)

    
    is_anomaly = if_result["if_anomaly"] or spike_result["spike_detected"]

    all_flags   = spike_result["spike_flags"]
    all_reasons = spike_result["spike_reasons"].copy()

    if if_result["if_anomaly"]:
        all_flags.append("isolation_forest_flag")
        all_reasons.append(
            f"Isolation Forest flagged reading as anomalous (score: {if_result['if_score']:.4f})"
        )

    if cold_start:
        all_reasons.append(
            "Note: fewer than 5 readings on record — time-series detection limited"
        )

    return {
        "is_anomaly":    is_anomaly,
        "anomaly_score": if_result["if_score"],
        "flags":         all_flags,
        "reasons":       all_reasons,
        "cold_start":    cold_start,
        "if_result":     if_result,
        "spike_result":  spike_result,
        "features":      features    # passed to explain.py
    }