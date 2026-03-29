from app.nlp.formatter import (
    render_doctor_explanation,
    render_patient_explanation,
    render_summary_text,
)


def build_explanations(
    *,
    systolic: float,
    diastolic: float,
    anomaly_result: dict,
    rule_result: dict,
) -> dict:
    """
    Build human-readable explanations from anomaly + rule outputs.

    Returns:
        {
            "summary": "...",
            "reasons": ["...", "..."],
            "severity": "stage2",
        }
    """

    reasons: list[str] = []

    severity = rule_result["severity"]
    membership = rule_result.get("membership", {})
    dominant_score = rule_result.get("dominant_score", 0.0)

    seen_reasons: set[str] = set()

    def add_reason(message: str) -> None:
        normalized = message.strip()
        if not normalized or normalized in seen_reasons:
            return
        seen_reasons.add(normalized)
        reasons.append(normalized)

    for reason in anomaly_result.get("reasons", []):
        add_reason(reason.rstrip(".") + ".")

    if severity == "crisis":
        add_reason("Blood pressure is in the crisis range based on rule thresholds.")
    elif severity == "stage2":
        add_reason("Blood pressure is in the Stage 2 hypertension range.")
    elif severity == "stage1":
        add_reason("Blood pressure is in the Stage 1 hypertension range.")
    elif severity == "elevated":
        add_reason("Blood pressure is elevated above the normal range.")
    else:
        add_reason("Blood pressure is within the normal range.")

    if dominant_score:
        add_reason(
            f"Rule-based severity classified this reading as {severity} with confidence {dominant_score:.2f}."
        )

    non_zero_membership = [
        f"{label}={score:.2f}"
        for label, score in membership.items()
        if score > 0
    ]
    if non_zero_membership:
        add_reason("Membership scores: " + ", ".join(non_zero_membership) + ".")

    summary = (
        f"Reading {systolic:.0f}/{diastolic:.0f} mmHg classified as {severity}."
    )
    if anomaly_result.get("cold_start"):
        summary += " Limited historical context was available for anomaly detection."

    return {
        "summary": render_summary_text(
            severity=severity,
            is_anomaly=anomaly_result.get("is_anomaly", False),
        ),
        "doctor_explanation": render_doctor_explanation(
            severity=severity,
            anomaly_score=anomaly_result.get("anomaly_score"),
            reasons=reasons,
            cold_start=anomaly_result.get("cold_start", False),
        ),
        "patient_explanation": render_patient_explanation(
            severity=severity,
            is_anomaly=anomaly_result.get("is_anomaly", False),
        ),
        "dashboard_summary": summary,
        "reasons": reasons,
        "severity": severity,
    }
