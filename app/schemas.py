from pydantic import BaseModel

class ObservationCreate(BaseModel):
    loinc_code: str
    value: float
    unit: str
    date: str  # ISO format: "2026-05-25"