# DietSense — Tests (Member 4)

Test suite covering unit, integration, and safety-gate tests across all domains.

---

## Setup

```bash
# From repo root
pip install -r backend/requirements.txt
pip install -r ml/requirements.txt
pip install pytest pytest-asyncio httpx
```

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# By domain
pytest tests/test_scoring.py -v       # ML scoring formula
pytest tests/test_safety_gate.py -v   # Hard safety constraint filter
pytest tests/test_etl.py -v           # Data pipeline validation
pytest tests/test_api.py -v           # FastAPI endpoint tests (Phase 4+)
```

---

## Test Files (Implementation in respective phases)

| File | Domain | Phase | Description |
|------|--------|-------|-------------|
| `test_scoring.py` | ML | Phase 6 | Scoring weights sum to 1.0, score bounds [0,1] |
| `test_safety_gate.py` | Backend/ML | Phase 6 | Allergen filter blocks unsafe recipes |
| `test_etl.py` | Data | Phase 2 | ETL output shape, no NaN calories, bounds |
| `test_api.py` | Backend | Phase 4 | HTTP status codes, Pydantic validation |
| `test_schema.py` | DB | Phase 3 | Schema constraints, FK integrity |

---

## Testing Philosophy

- **Safety gate tests** are treated as **critical** — any failure blocks the CI pipeline
- All tests must pass before merging to `main`
- Rule 1 (LLM never writes nutrition facts) is verified by checking that `ai_interaction_logs` is read-only from the LLM perspective
