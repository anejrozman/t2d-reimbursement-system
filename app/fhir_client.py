"""


"""

import httpx

BASE_URL = "https://hapi.fhir.org/baseR4"

LOINC_LABELS = {
    "4548-4": "HbA1c",
    "1558-6": "Fasting glucose",
    "39156-5": "BMI",
    "85354-9": "Blood pressure",
}

def get(resource_path: str) -> dict: 
    """
    Fetches a FHIR resource from the HAPI FHIR server.
    """
    url = f"{BASE_URL}/{resource_path.lstrip("/")}"
    response = httpx.get(url, headers={"Accept": "application/fhir+json"}, timeout=10.0)
    response.raise_for_status()
    return response.json()

def post(resource_path: str, body: dict) -> dict:
    """POST a FHIR resource and return the server's response."""
    url = f"{BASE_URL}/{resource_path.lstrip('/')}"
    response = httpx.post(
        url,
        json=body,
        headers={
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
        },
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()

def extract_patient_ids(bundle: dict) -> list:
    """
    Extracts patient IDs from a FHIR Bundle of Condition resources.
    """
    patient_ids = set()
    for entry in bundle.get("entry", []):
        ref = entry["resource"].get("subject", {}).get("reference", "")
        if ref.startswith("Patient/"):
            patient_ids.add(ref.split("/")[1])
    return list(patient_ids)

def extract_patient_summary(patient_id: str) -> dict | None:
    """
    Extracts a summary of patient information given a patient ID.
    """
    try:
        patient = get(f"Patient/{patient_id}")
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

def extract_patient_biomarkers(patient_id: str) -> list:
    """
    Extracts biomarker observations for a given patient ID.
    """
    codes = ",".join(LOINC_LABELS.keys())
    bundle = get(f"Observation?patient={patient_id}&code={codes}&_count=100")
    seen_codes = set() # To check for duplicates
    
    results = []
    for entry in bundle.get("entry", []):
        obs = entry["resource"]
        code = obs.get("code", {}).get("coding", [{}])[0].get("code")
        value_qty = obs.get("valueQuantity", {})
        value = value_qty.get("value")
        unit = value_qty.get("unit")
        date = obs.get("effectiveDateTime")
        
        if value is None or code not in LOINC_LABELS:
            continue  # skip BP (no valueQuantity) and broken entries
        
        key = (LOINC_LABELS[code], value, date)
        if key in seen_codes:
            continue
        seen_codes.add(key)
        results.append({
            "biomarker": LOINC_LABELS[code],
            "value": value,
            "unit": unit,
            "date": date,
        })
    
    results.sort(key=lambda r: r.get("date") or "")
    return results