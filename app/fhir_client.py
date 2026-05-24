"""


"""

import httpx

BASE_URL = "https://hapi.fhir.org/baseR4"

def get(resource_path: str) -> dict: 
    """
    Fetches a FHIR resource from the HAPI FHIR server.
    """
    url = f"{BASE_URL}/{resource_path.lstrip("/")}"
    response = httpx.get(url, headers={"Accept": "application/fhir+json"}, timeout=10.0)
    response.raise_for_status()
    return response.json()