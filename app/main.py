from fastapi import FastAPI
from app.fhir_client import get # TODO: Remove the import after removing /test endpoint

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/test") # TODO: Remove this endpoint after testing
def test():
    return get("Patient/131287982")