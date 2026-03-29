def _join_parts(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def render_doctor_explanation(*, severity: str, anomaly_score: float | None, reasons: list[str], cold_start: bool) -> str:
    header = f"Reading classified as {severity.replace('_', ' ')}."
    score_text = f" Anomaly score: {anomaly_score:.4f}." if anomaly_score is not None else ""
    caveat = " Historical context is still limited." if cold_start else ""
    details = " ".join(reasons[:4])
    return _join_parts([header + score_text, details, caveat])


def render_patient_explanation(*, severity: str, is_anomaly: bool) -> str:
    if severity == "crisis":
        return "Your blood pressure reading is very high. Please contact your doctor or seek urgent care right away."
    if severity == "stage2":
        return "Your blood pressure is higher than your target range. Please take a repeat reading and follow your care plan."
    if severity == "stage1":
        return "Your blood pressure is slightly above the normal range. Keep monitoring and follow your care plan."
    if is_anomaly:
        return "This reading looks different from your usual pattern. Please repeat the reading when you can."
    return "Your reading looks stable right now. Keep taking your blood pressure as scheduled."


def render_summary_text(*, severity: str, is_anomaly: bool) -> str:
    if is_anomaly:
        return f"{severity.replace('_', ' ').title()} BP with anomaly flag."
    return f"{severity.replace('_', ' ').title()} blood pressure reading."


def format_checkin_prompt(step: str, patient_name: str) -> str:
    prompts = {
        "start": f"Hi {patient_name}, it is time for your weekly check-in. On a scale of 1 to 10, how bad is your fatigue or low energy today?",
        "fatigue": "Thank you. On the same 1 to 10 scale, how much pain are you feeling today?",
        "pain": "Got it. How much swelling have you noticed in your legs or ankles today? Reply with 1 to 10.",
        "swelling": "Thanks. How much nausea are you feeling today? Reply with 1 to 10.",
        "nausea": "Almost done. Is there anything else you would like your doctor to know today?",
    }
    return prompts.get(step, "Thanks. Please continue with your check-in.")


def format_invalid_rating(step_label: str) -> str:
    return f"Please reply with a number between 1 and 10 for {step_label}."


def format_help_message(step: str) -> str:
    help_messages = {
        "fatigue": "Reply with one number from 1 to 10, where 1 means you feel okay and 10 means the symptom is very bad.",
        "pain": "Reply with one number from 1 to 10 for your pain today.",
        "swelling": "Reply with one number from 1 to 10 for swelling in your legs or ankles.",
        "nausea": "Reply with one number from 1 to 10 for nausea today.",
        "notes": "Reply with any short message you want your doctor to see, or type 'none' if there is nothing else to add.",
    }
    return help_messages.get(step, "Reply with the information asked in the previous message.")


def format_completion_message(patient_name: str) -> str:
    return f"Thank you, {patient_name}. Your check-in has been saved and your doctor has been notified."


def render_symptom_summary(patient_name: str, fatigue: int | None, pain_level: int | None, swelling: int | None, nausea: int | None, notes: str | None) -> str:
    return _join_parts([
        f"RenalWatch symptom update for {patient_name}.",
        f"Fatigue {fatigue or 'N/A'}/10.",
        f"Pain {pain_level or 'N/A'}/10.",
        f"Swelling {swelling or 'N/A'}/10.",
        f"Nausea {nausea or 'N/A'}/10.",
        f"Notes: {notes or 'None provided'}.",
    ])
