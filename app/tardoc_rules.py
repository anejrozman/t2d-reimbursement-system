"""
TARDOC tariff rule engine for T2D reimbursement evaluation.

``evaluate_reimbursement_events`` maps biomarker readings to billable
TARDOC positions according to Swiss TARDOC tariff rules.
``summarize_reimbursement_events`` aggregates those events into a
per-patient financial summary.
"""

from app.schemas import BiomarkerRead, ReimbursementEvent, ReimbursementSummary, TardocBreakdownItem

TARDOC_CATALOG: dict[str, dict[str, str | int]] = {
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

TARIFF_POINT_VALUE_CHF: float = 0.90  # assumed cantonal average placeholder


def evaluate_reimbursement_events(biomarkers: list[dict]) -> list[ReimbursementEvent]:
    """
    Apply TARDOC tariff rules to a list of biomarker observations.
    """
    events: list[ReimbursementEvent] = []
    for b in biomarkers:
        name: str = b["biomarker"]
        value: float = b["value"]
        code: str | None = None

        if name == "HbA1c" and value >= 6.5:
            code = "CA.00.0050"
        elif name == "Fasting glucose" and value >= 126:
            code = "CA.00.0050"
        elif name == "BMI" and value >= 30:
            code = "CA.00.0080"

        if code:
            item = TARDOC_CATALOG[code]
            events.append(
                ReimbursementEvent(
                    tardoc_code=code,
                    description=str(item["description"]),
                    tariff_points=int(item["tariff_points"]),
                    estimated_chf=round(int(item["tariff_points"]) * TARIFF_POINT_VALUE_CHF, 2),
                    triggering_observation=BiomarkerRead(**b),
                )
            )
    return events


def summarize_reimbursement_events(
    patient_id: str, events: list[ReimbursementEvent]
) -> ReimbursementSummary:
    """
    Aggregate reimbursement events into a per-patient financial summary.
    """
    breakdown: dict[str, TardocBreakdownItem] = {}
    for e in events:
        if e.tardoc_code not in breakdown:
            breakdown[e.tardoc_code] = TardocBreakdownItem(
                description=e.description,
                count=0,
                tariff_points=0,
                estimated_chf=0.0,
            )
        breakdown[e.tardoc_code].count += 1
        breakdown[e.tardoc_code].tariff_points += e.tariff_points
        breakdown[e.tardoc_code].estimated_chf += e.estimated_chf

    return ReimbursementSummary(
        patient_id=patient_id,
        total_events=len(events),
        total_tariff_points=sum(e.tariff_points for e in events),
        total_estimated_chf=round(sum(e.estimated_chf for e in events), 2),
        breakdown_by_code=breakdown,
    )
