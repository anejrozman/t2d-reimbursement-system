from fastapi import FastAPI
from app import fhir_client
from app import tardoc_rules
from app import schemas

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

@app.get("/patients/{patient_id}/reimbursement-events")
def get_reimbursement_events(patient_id: str):
    biomarkers = fhir_client.extract_patient_biomarkers(patient_id)
    return tardoc_rules.evaluate_reimbursement_events(biomarkers)

@app.get("/patients/{patient_id}/reimbursement-summary")
def get_reimbursement_summary(patient_id: str):
    biomarkers = fhir_client.extract_patient_biomarkers(patient_id)
    events = tardoc_rules.evaluate_reimbursement_events(biomarkers)
    return tardoc_rules.summarize_reimbursement_events(patient_id, events) 

@app.post("/patients/{patient_id}/observations")
def create_observation(patient_id: str, payload: schemas.ObservationCreate):
    label = fhir_client.LOINC_LABELS.get(payload.loinc_code, "Unknown biomarker")
    
    observation = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": payload.loinc_code,
                "display": label,
            }]
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": payload.date,
        "valueQuantity": {
            "value": payload.value,
            "unit": payload.unit,
            "system": "http://unitsofmeasure.org",
        },
    }
    
    created = fhir_client.post("Observation", observation)
    return {
        "observation_id": created.get("id"),
        "status": "created",
        "resource": created,
    }