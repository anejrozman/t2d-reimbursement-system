"""
Async FHIR R4 client for the HAPI FHIR public test server.
The HTTP client is managed via FastAPI's lifespan context — a single
``httpx.AsyncClient`` is created on startup and closed on shutdown.
Route handlers receive it through the ``get_fhir_client`` dependency.
"""

from __future__ import annotations

import httpx
from fastapi import Request

from app.config import settings

LOINC_LABELS: dict[str, str] = {
    "4548-4": "HbA1c",
    "1558-6": "Fasting glucose",
    "39156-5": "BMI",
    "85354-9": "Blood pressure",
}


# Dependency
def get_fhir_client(request: Request) -> httpx.AsyncClient:
    """FastAPI dependency that returns the shared AsyncClient from app.state."""
    return request.app.state.fhir_client


# Low-level transport
async def get(client: httpx.AsyncClient, resource_path: str) -> dict:
    """
    Fetch a FHIR resource by path from the configured base URL.
    """
    url = f"{settings.fhir_base_url}/{resource_path.lstrip('/')}"
    response = await client.get(url, headers={"Accept": "application/fhir+json"})
    response.raise_for_status()
    return response.json()


async def post(client: httpx.AsyncClient, resource_path: str, body: dict) -> dict:
    """
    POST a new FHIR resource and return the server response.
    """
    url = f"{settings.fhir_base_url}/{resource_path.lstrip('/')}"
    response = await client.post(
        url,
        json=body,
        headers={
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
        },
    )
    response.raise_for_status()
    return response.json()

# FHIR parsing helpers
def extract_patient_ids(bundle: dict) -> list[str]:
    """
    Extract unique patient IDs from a FHIR Bundle of Condition resources.
    """
    patient_ids: set[str] = set()
    for entry in bundle.get("entry", []):
        ref: str = entry["resource"].get("subject", {}).get("reference", "")
        if ref.startswith("Patient/"):
            patient_ids.add(ref.split("/")[1])
    return list(patient_ids)


async def extract_patient_summary(
    client: httpx.AsyncClient, patient_id: str
) -> dict | None:
    """
    Fetch and parse demographic information for one patient.
    """
    try:
        patient = await get(client, f"Patient/{patient_id}")
        name = patient.get("name", [{}])[0]
        given = " ".join(name.get("given", []))
        family = name.get("family", "")
        full_name = f"{given} {family}".strip() or None
        return {
            "patient_id": patient_id,
            "name": full_name,
            "birth_date": patient.get("birthDate"),
        }
    except Exception:
        return None


async def extract_patient_biomarkers(
    client: httpx.AsyncClient, patient_id: str
) -> list[dict]:
    """
    Fetch and de-duplicate biomarker observations for a patient.
    """
    codes = ",".join(LOINC_LABELS.keys())
    bundle = await get(client, f"Observation?patient={patient_id}&code={codes}&_count=100")
    seen: set[tuple[str, float, str | None]] = set()
    results: list[dict] = []

    for entry in bundle.get("entry", []):
        obs = entry["resource"]
        code: str | None = obs.get("code", {}).get("coding", [{}])[0].get("code")
        value_qty: dict = obs.get("valueQuantity", {})
        value: float | None = value_qty.get("value")
        unit: str | None = value_qty.get("unit")
        date: str | None = obs.get("effectiveDateTime")

        if value is None or code not in LOINC_LABELS:
            continue  # skip BP components and malformed entries

        key: tuple[str, float, str | None] = (LOINC_LABELS[code], value, date)
        if key in seen:
            continue
        seen.add(key)
        results.append(
            {"biomarker": LOINC_LABELS[code], "value": value, "unit": unit, "date": date}
        )

    results.sort(key=lambda r: r.get("date") or "")
    return results
