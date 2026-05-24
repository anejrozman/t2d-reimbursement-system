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

# Install all dependencies
uv sync

# Run the application
uv run uvicorn app/main:app --reload
```
