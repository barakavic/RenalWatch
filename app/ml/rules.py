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

    stage3 = 1.0 if systolic >= 180 or diastolic >= 110 else 0.0

    stage2 = 0.0
    if stage3 == 0.0 and (systolic >= 160 or diastolic >= 100):
        stage2 = max(
            _rising_membership(systolic, 160, 180),
            _rising_membership(diastolic, 100, 110),
            0.6,
        )

    stage1 = 0.0
    if stage3 == 0.0 and stage2 == 0.0 and (140 <= systolic <= 159 or 90 <= diastolic <= 99):
        stage1 = max(
            _rising_membership(systolic, 140, 160),
            _rising_membership(diastolic, 90, 100),
            0.6,
        )

    elevated = 0.0
    if stage3 == 0.0 and stage2 == 0.0 and stage1 == 0.0 and (131 <= systolic <= 139 or 81 <= diastolic <= 89):
        elevated = 1.0

    normal = 0.0
    if stage3 == stage2 == stage1 == elevated == 0.0 and systolic <= 130 and diastolic <= 80:
        normal = 1.0

    membership = {
        "normal": round(_clamp(normal), 4),
        "elevated": round(_clamp(elevated), 4),
        "stage1": round(_clamp(stage1), 4),
        "stage2": round(_clamp(stage2), 4),
        "stage3": round(_clamp(stage3), 4),
    }

    severity_order = ["normal", "elevated", "stage1", "stage2", "stage3"]
    severity = max(severity_order, key=lambda key: membership[key])
    dominant_score = membership[severity]

    if dominant_score == 0.0:
        if systolic >= 180 or diastolic >= 110:
            severity = "stage3"
        elif systolic >= 160 or diastolic >= 100:
            severity = "stage2"
        elif systolic >= 140 or diastolic >= 90:
            severity = "stage1"
        elif systolic >= 131 or diastolic >= 81:
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
