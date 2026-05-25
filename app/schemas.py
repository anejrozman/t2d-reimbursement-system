"""
Pydantic request and response models for the T2D reimbursement API.
Models are grouped by domain
  - Patient
  - Biomarker
  - Reimbursement
"""

from pydantic import BaseModel, Field

# Shared primitive
class BiomarkerRead(BaseModel):
    """A single biomarker observation extracted from FHIR."""
    biomarker: str = Field(description="Human-readable biomarker name.")
    value: float
    unit: str | None = None
    date: str | None = None

# Patient
class PatientSummary(BaseModel):
    """Minimal patient demographic summary."""
    patient_id: str
    name: str | None = Field(default=None, description="Full name; None if not recorded.")
    birth_date: str | None = Field(default=None, description="ISO-8601 birth date.")

# Reimbursement
class ReimbursementEvent(BaseModel):
    """A single billable TARDOC reimbursement event triggered by a biomarker."""
    tardoc_code: str = Field(description="TARDOC tariff position code.")
    description: str
    tariff_points: int
    estimated_chf: float = Field(description="Estimated amount in CHF.")
    triggering_observation: BiomarkerRead

class TardocBreakdownItem(BaseModel):
    """Aggregated totals for a single TARDOC code within a summary."""
    description: str
    count: int
    tariff_points: int
    estimated_chf: float


class ReimbursementSummary(BaseModel):
    """Full reimbursement summary for a patient."""
    patient_id: str
    total_events: int
    total_tariff_points: int
    total_estimated_chf: float
    breakdown_by_code: dict[str, TardocBreakdownItem]

# Observation (write)
class ObservationCreate(BaseModel):
    """Payload for creating a new FHIR Observation."""
    loinc_code: str = Field(description="LOINC code identifying the measurement type.")
    value: float
    unit: str
    date: str = Field(description="ISO-8601 date string.")

class ObservationCreated(BaseModel):
    """Response returned after a new observation is successfully posted to FHIR."""
    observation_id: str | None = Field(
        default=None, description="FHIR resource ID assigned by the server."
    )
    status: str
    resource: dict
