# Guard Evaluation

The frozen `evals/attack_corpus.jsonl` v1 corpus contains 40 labeled prompts: 15 clean, 15 known-pattern injection attacks, and 10 PII-bearing prompts. `python evals/run.py` computes each guard independently; injection means any `WARN` or `BLOCK`, while PII means at least one validated detection.

## Observed deterministic result — 2026-08-12

| Guard | TP | FP | FN | TN | Precision | Recall | False-positive rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Injection | 15 | 0 | 0 | 25 | 1.00 | 1.00 | 0.00 |
| PII | 10 | 0 | 0 | 30 | 1.00 | 1.00 | 0.00 |

```bash
cd projects/llmshield
python evals/run.py
```

Recall alone is not sufficient: a guard that blocks every request gets perfect recall and is still unusable, so precision and clean-prompt false-positive rate are mandatory.

## Scope boundary

These perfect fixture scores are not a production-performance claim. The corpus measures reviewed English lexical pattern families and regex/Luhn PII detection. It does not measure novel semantic jailbreaks, multilingual attacks, encoded payload interpretation, multi-turn attacks, or real traffic. Freezing the fixture allows future pattern revisions to be compared against the same boundary.
