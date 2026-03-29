from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.db.session import get_db
from app.models.patient import Patient
from app.models.bp_reading import BPReading
from app.models.alert import Alert
from app.models.symptom_log import SymptomLog

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/{patient_id}")
async def get_dashboard_data(patient_id: int, db: AsyncSession = Depends(get_db)):
    """
    Returns aggregated BP trends, ML anomalies, and Chatbot symptoms
    shaped specifically for the Frontend Doctor Dashboard.
    """
    # 1. Fetch patient
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # 2. Fetch trailing 24 BP readings
    result = await db.execute(
        select(BPReading)
        .where(BPReading.patient_id == patient_id)
        .order_by(BPReading.timestamp.desc())
        .limit(24)
    )
    readings = list(result.scalars().all())
    # Reverse to chronological order for charts
    readings.reverse()

    trend = []
    moving_avg = []
    anomalies = []
    
    window_size = 3
    for i, r in enumerate(readings):
        trend.append({
            "timestamp": r.timestamp.isoformat(),
            "systolic": r.systolic,
            "diastolic": r.diastolic
        })
        
        # Capture Anomaly output from isolation forest
        if getattr(r, "is_anomaly", 0) == 1:
             anomalies.append({
                 "timestamp": r.timestamp.isoformat(),
                 "systolic": r.systolic,
                 "score": getattr(r, "anomaly_score", 0.0)
             })

        # Generate a baseline moving avg for visualization
        start_idx = max(0, i - window_size + 1)
        window = readings[start_idx:i+1]
        sys_avg = sum(w.systolic for w in window) / len(window)
        moving_avg.append({
            "timestamp": r.timestamp.isoformat(),
            "systolic_avg": round(sys_avg, 1)
        })

    # 3. Assess past critical alerts for active risk flags
    stmt_alert = select(Alert).where(Alert.patient_id == patient_id).order_by(Alert.triggered_at.desc()).limit(3)
    alerts = list((await db.execute(stmt_alert)).scalars().all())

    # 4. Merge recent qualitative WhatsApp Chatbot logs 
    stmt_slog = select(SymptomLog).where(
        SymptomLog.patient_id == patient_id, 
        SymptomLog.chat_step == 'done'
    ).order_by(SymptomLog.logged_at.desc()).limit(1)
    symptom_log = (await db.execute(stmt_slog)).scalars().first()

    # 5. Distill overall holistic Risk Level and Explanations
    risk_level = "LOW"
    explanations = []

    # Parse Quantitative Alerts First
    found_critical = False
    found_high = False
    for alert in alerts:
        if alert.severity == "critical":
            found_critical = True
            if alert.explanation and alert.explanation not in explanations:
                explanations.append(f"CRITICAL: {alert.explanation}")
        elif alert.severity == "high":
            found_high = True
            if alert.explanation and alert.explanation not in explanations:
                explanations.append(f"HIGH RISK: {alert.explanation}")

    if found_critical:
        risk_level = "CRITICAL"
    elif found_high:
        risk_level = "HIGH"

    # Merge Qualitative Chatbot Data
    if symptom_log:
        symptom_exps = []
        high_symptom = False
        
        if symptom_log.fatigue and symptom_log.fatigue >= 8:
            symptom_exps.append(f"severe fatigue ({symptom_log.fatigue}/10)")
            high_symptom = True
        if symptom_log.pain_level and symptom_log.pain_level >= 8:
            symptom_exps.append(f"severe pain ({symptom_log.pain_level}/10)")
            high_symptom = True
        if symptom_log.swelling and symptom_log.swelling >= 8:
            symptom_exps.append(f"severe swelling ({symptom_log.swelling}/10)")
            high_symptom = True
        
        if symptom_exps:
            explanations.append(f"Patient reported {', '.join(symptom_exps)} during latest WhatsApp check-in")
            
        # Escalate risk if symptoms indicate problems lacking watch anomalies
        if high_symptom and risk_level == "LOW":
            risk_level = "MODERATE"
        elif high_symptom and risk_level == "MODERATE":
            risk_level = "HIGH"
            
        if symptom_log.notes:
            explanations.append(f"Chatbot Note: '{symptom_log.notes}'")

    # Add rapid-spike visual heuristic
    if len(trend) >= 2:
        last = trend[-1]["systolic"]
        prev = trend[-2]["systolic"]
        if last - prev >= 30:
            msg = f"Sudden structural spike: 30+ mmHg rise between final dual readings."
            if msg not in explanations:
                explanations.append(msg)

    # Fallback default
    if not explanations:
        explanations.append("Patient vitals and chatbot logs appear stable.")

    # Conform exactly to the Dashboard Payload JSON Contract
    return {
        "patient_id": patient.id,
        "patient_name": patient.name,
        "ckd_stage": patient.ckd_stage,
        "trend": trend,
        "moving_avg": moving_avg,
        "anomalies": anomalies,
        "risk_level": risk_level,
        "explanation": explanations
    }
