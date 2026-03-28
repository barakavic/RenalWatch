def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _rising_membership(value: float, start: float, end: float) -> float:
    if value <= start:
        return 0.0
    if value >= end:
        return 1.0
    return (value - start) / (end - start)


def classify_bp(systolic: float, diastolic: float) -> dict:
    """
    Classify blood pressure using architecture-aligned rule/fuzzy logic.

    Returns:
        {
            "severity": "stage2",
            "membership": {
                "normal": 0.0,
                "elevated": 0.0,
                "stage1": 0.2,
                "stage2": 0.8,
                "crisis": 0.0,
            },
            "dominant_score": 0.8,
        }
    """

    crisis = 1.0 if systolic > 180 or diastolic > 120 else 0.0

    stage2 = 0.0
    if crisis == 0.0 and (systolic >= 140 or diastolic >= 90):
        stage2 = max(
            _rising_membership(systolic, 140, 180),
            _rising_membership(diastolic, 90, 120),
            0.6,
        )

    stage1 = 0.0
    if crisis == 0.0 and stage2 == 0.0 and (130 <= systolic <= 139 or 80 <= diastolic <= 89):
        stage1 = max(
            _rising_membership(systolic, 130, 140),
            _rising_membership(diastolic, 80, 90),
            0.6,
        )

    elevated = 0.0
    if crisis == 0.0 and stage2 == 0.0 and stage1 == 0.0 and diastolic < 80 and 120 <= systolic <= 129:
        elevated = 1.0

    normal = 0.0
    if crisis == stage2 == stage1 == elevated == 0.0 and systolic < 120 and diastolic < 80:
        normal = 1.0

    membership = {
        "normal": round(_clamp(normal), 4),
        "elevated": round(_clamp(elevated), 4),
        "stage1": round(_clamp(stage1), 4),
        "stage2": round(_clamp(stage2), 4),
        "crisis": round(_clamp(crisis), 4),
    }

    severity_order = ["normal", "elevated", "stage1", "stage2", "crisis"]
    severity = max(severity_order, key=lambda key: membership[key])
    dominant_score = membership[severity]

    if dominant_score == 0.0:
        if systolic > 180 or diastolic > 120:
            severity = "crisis"
        elif systolic >= 140 or diastolic >= 90:
            severity = "stage2"
        elif systolic >= 130 or diastolic >= 80:
            severity = "stage1"
        elif 120 <= systolic <= 129 and diastolic < 80:
            severity = "elevated"
        else:
            severity = "normal"
        dominant_score = 1.0
        membership[severity] = 1.0

    return {
        "severity": severity,
        "membership": membership,
        "dominant_score": round(dominant_score, 4),
    }
