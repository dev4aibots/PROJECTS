# Evaluation

Observed 2026-08-12 in the Linux sandbox:

| Gate | Result |
|---|---:|
| Backend tests | 57 passed |
| Malicious SQL corpus | 25/25 blocked |
| Safe SQL corpus | 25/25 allowed |
| Golden natural-language cases | 13/13 passed |
| Frontend | typecheck and production build passed |

Run `PYTHONPATH=backend python -m pytest -q backend/tests` and `PYTHONPATH=backend python evals/run.py`.

The corpus is authored and finite, not a proof against every SQL dialect trick. Golden results measure deterministic local execution. They do not measure Groq/Gemini semantic accuracy; the churn question intentionally passes only when the system refuses to invent an unavailable prediction.
