TARDOC_CATALOG = {
    "CA.00.0010": {
        "description": "Basic consultation, first 5 minutes",
        "tariff_points": 10,
    },
    "CA.00.0050": {
        "description": "Diabetes follow-up consultation",
        "tariff_points": 25,
    },
    "AA.00.0210": {
        "description": "HbA1c laboratory analysis",
        "tariff_points": 8,
    },
    "CA.00.0080": {
        "description": "Structured patient education, chronic disease",
        "tariff_points": 40,
    },
}

TARIFF_POINT_VALUE_CHF = 0.90  # cantonal average placeholder

def evaluate_reimbursement_events(biomarkers: list) -> list:
    events = []
    for b in biomarkers:
        name, value = b["biomarker"], b["value"]
        code = None
        
        if name == "HbA1c" and value >= 6.5:
            code = "CA.00.0050"
        elif name == "Fasting glucose" and value >= 126:
            code = "CA.00.0050"
        elif name == "BMI" and value >= 30:
            code = "CA.00.0080"
        
        if code:
            item = TARDOC_CATALOG[code]
            events.append({
                "tardoc_code": code,
                "description": item["description"],
                "tariff_points": item["tariff_points"],
                "estimated_chf": round(item["tariff_points"] * TARIFF_POINT_VALUE_CHF, 2),
                "triggering_observation": b,
            })
    return events

def summarize_reimbursement_events(patient_id: str, events: list) -> dict:
    breakdown = {}
    for e in events:
        code = e["tardoc_code"]
        if code not in breakdown:
            breakdown[code] = {
                "description": e["description"],
                "count": 0,
                "tariff_points": 0,
                "estimated_chf": 0.0,
            }
        breakdown[code]["count"] += 1
        breakdown[code]["tariff_points"] += e["tariff_points"]
        breakdown[code]["estimated_chf"] += e["estimated_chf"]
    
    return {
        "patient_id": patient_id,
        "total_events": len(events),
        "total_tariff_points": sum(e["tariff_points"] for e in events),
        "total_estimated_chf": round(sum(e["estimated_chf"] for e in events), 2),
        "breakdown_by_code": breakdown,
    }