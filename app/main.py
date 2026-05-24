from fastapi import FastAPI
from app import fhir_client

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/patients/diabetic")
def get_diabetic_patients():
    bundle = fhir_client.get("Condition?code=44054006&_count=50")
    patient_ids = fhir_client.extract_patient_ids(bundle)
    summaries = [fhir_client.extract_patient_summary(pid) for pid in patient_ids]
    return [s for s in summaries if s is not None]

@app.get("/patients/{patient_id}/biomarkers")
def get_biomarkers(patient_id: str):
    biomarkers = fhir_client.extract_patient_biomarkers(patient_id)
    return biomarkers

