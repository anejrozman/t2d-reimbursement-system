"""
T2D Reimbursement System — FastAPI application entry point.
Provides REST endpoints for:
- Listing diabetic patients from a FHIR R4 server
- Retrieving patient biomarkers (HbA1c, fasting glucose, BMI)
- Evaluating and summarising TARDOC reimbursement events
- Creating new FHIR Observations
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, status

from app import fhir_client, tardoc_rules
from app.config import settings
from app.fhir_client import get_fhir_client
from app.schemas import (
    BiomarkerRead,
    ObservationCreate,
    ObservationCreated,
    PatientSummary,
    ReimbursementEvent,
    ReimbursementSummary,
)


# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create and tear down the shared FHIR HTTP client."""
    async with httpx.AsyncClient(timeout=settings.fhir_timeout) as client:
        app.state.fhir_client = client
        yield

# Application
app = FastAPI(
    title="T2D Reimbursement System",
    description=(
        "Automated contract payment service for Type 2 Diabetes patients. "
        "Connects to a FHIR R4 server, evaluates imaginary TARDOC tariff rules, "
        "and returns CHF reimbursement estimates."
    ),
    version=settings.app_version,
    lifespan=lifespan,
)

# Type alias for the injected FHIR client dependency
FHIRClient = Annotated[httpx.AsyncClient, Depends(get_fhir_client)]


# Routes

@app.get("/health", summary="Health check")
async def health() -> dict[str, str]:
    """Return service liveness status."""
    return {"status": "ok"}


@app.get(
    "/patients/diabetic/count={count}",
    response_model=list[PatientSummary],
    summary="List diabetic patients",
    tags=["patients"],
)
async def get_diabetic_patients(client: FHIRClient, count: int) -> list[PatientSummary]:
    """
    Query the FHIR server for patients with a Type 2 Diabetes condition
    (SNOMED CT code 44054006) and return their demographic summaries.
    """
    bundle = await fhir_client.get(client, f"Condition?code=44054006&_count={count}")
    patient_ids = fhir_client.extract_patient_ids(bundle)
    raw = [await fhir_client.extract_patient_summary(client, pid) for pid in patient_ids]
    return [PatientSummary(**s) for s in raw if s is not None]


@app.get(
    "/patients/{patient_id}/biomarkers",
    response_model=list[BiomarkerRead],
    summary="Get patient biomarkers",
    tags=["biomarkers"],
)
async def get_biomarkers(patient_id: str, client: FHIRClient) -> list[BiomarkerRead]:
    """
    Return the latest de-duplicated biomarker observations (HbA1c, fasting
    glucose, BMI) for the given patient, sorted by date ascending.
    """
    raw = await fhir_client.extract_patient_biomarkers(client, patient_id)
    return [BiomarkerRead(**b) for b in raw]


@app.get(
    "/patients/{patient_id}/reimbursement-events",
    response_model=list[ReimbursementEvent],
    summary="Get reimbursement events",
    tags=["reimbursement"],
)
async def get_reimbursement_events(
    patient_id: str, client: FHIRClient
) -> list[ReimbursementEvent]:
    """
    Evaluate TARDOC reimbursement events for each biomarker observation.
    Each triggered tariff position is returned as a separate event.
    """
    biomarkers = await fhir_client.extract_patient_biomarkers(client, patient_id)
    return tardoc_rules.evaluate_reimbursement_events(biomarkers)


@app.get(
    "/patients/{patient_id}/reimbursement-summary",
    response_model=ReimbursementSummary,
    summary="Get reimbursement summary",
    tags=["reimbursement"],
)
async def get_reimbursement_summary(
    patient_id: str, client: FHIRClient
) -> ReimbursementSummary:
    """
    Return the aggregated TARDOC reimbursement summary for a patient,
    including total tariff points, estimated CHF, and a per-code breakdown.
    """
    biomarkers = await fhir_client.extract_patient_biomarkers(client, patient_id)
    events = tardoc_rules.evaluate_reimbursement_events(biomarkers)
    return tardoc_rules.summarize_reimbursement_events(patient_id, events)


@app.post(
    "/patients/{patient_id}/observations",
    response_model=ObservationCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create an observation",
    tags=["observations"],
)
async def create_observation(
    patient_id: str, payload: ObservationCreate, client: FHIRClient
) -> ObservationCreated:
    """
    Post a new FHIR Observation resource for the patient.
    Returns the server-assigned resource ID and the full created resource.
    """
    label = fhir_client.LOINC_LABELS.get(payload.loinc_code, "Unknown biomarker")
    observation = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": payload.loinc_code,
                    "display": label,
                }
            ]
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": payload.date,
        "valueQuantity": {
            "value": payload.value,
            "unit": payload.unit,
            "system": "http://unitsofmeasure.org",
        },
    }
    created = await fhir_client.post(client, "Observation", observation)
    return ObservationCreated(
        observation_id=created.get("id"),
        status="created",
        resource=created,
    )
