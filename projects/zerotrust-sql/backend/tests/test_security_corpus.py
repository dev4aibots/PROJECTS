"""Property-style corpus test: 25 safe + 25 malicious SQL fixtures.

Gate (from the specification): 100% of malicious fixtures blocked and
>= 90% of safe fixtures allowed. The honest measured numbers live in
docs/evaluation.md.
"""
import json
from pathlib import Path

from app.validator import validate

FIXTURES = json.loads(
    (Path(__file__).resolve().parents[2] / "evals" / "sql_fixtures.json").read_text())


def test_corpus_shape():
    assert len(FIXTURES["safe"]) == 25
    assert len(FIXTURES["malicious"]) == 25


def test_all_malicious_blocked():
    escaped = [sql for sql in FIXTURES["malicious"] if validate(sql).allowed]
    assert not escaped, f"malicious SQL escaped validation: {escaped}"


def test_safe_allow_rate_at_least_90_percent():
    allowed = [sql for sql in FIXTURES["safe"] if validate(sql).allowed]
    rate = len(allowed) / len(FIXTURES["safe"])
    assert rate >= 0.9, (
        f"safe allow rate {rate:.0%}; blocked: "
        f"{[s for s in FIXTURES['safe'] if s not in allowed]}")
