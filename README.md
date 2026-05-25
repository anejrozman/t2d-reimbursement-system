# t2d-reimbursement-system

A small backend service that demonstrates automatic contract payment for a Type 2 Diabetes use case following the FHIR standard.

---

### Package Management

This project uses the **[uv](https://docs.astral.sh/uv/)**  package manager. To install it, run the following command 

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv

# Windows (PowerShell) using winget
winget install --id=astral-sh.uv -e
```

### Getting Started

```bash
# Clone the repo
git clone <repo-url>
cd t2d-reimbursement-system

# Install all dependencies (add --group dev for linting)
uv sync

# Run the application
uv run uvicorn app.main:app --reload
```

The interactive API docs are available at `http://localhost:8000/docs` once the server is running.

---

### Limitations

- **No error handling:** FHIR server failures (network errors, 4xx/5xx responses) propagate as unhandled exceptions and return a generic 500 to the caller. Production use would require proper `HTTPException` mapping.
- **Tariff point value is a placeholder:** `TARIFF_POINT_VALUE_CHF = 0.90` is a cantonal average estimate, not an officially sourced rate.
- **Public FHIR server:** The service targets `https://hapi.fhir.org/baseR4`, a shared public test server with no guarantees of uptime or data consistency.
