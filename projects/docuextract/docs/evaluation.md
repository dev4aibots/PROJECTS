# Evaluation

Observed 2026-08-12: 18 backend tests passed; deterministic generated-document verdict accuracy was 5/5; frontend typecheck and production build passed. Run `PYTHONPATH=backend python evals/run.py`.

This proves deterministic extraction fixtures and verification correctness, not live Gemini field accuracy. The requested 3× live multimodal evaluation remains owner-gated until a Gemini key is configured; results must not be inferred from local samples.
