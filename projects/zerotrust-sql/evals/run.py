"""Golden-query execution-accuracy eval.

Runs each NL question end-to-end through the API app (deterministic generator,
seeded SQLite sandbox) and scores whether the returned result satisfies the
declared assertion. Refusals count as PASS when the fixture expects them —
"I can't answer that" is the correct behaviour for unanswerable questions.

Run: PYTHONPATH=backend python evals/run.py
Gate: execution accuracy >= 90% on answerable questions.
"""
import json
import pathlib
import sys

from fastapi.testclient import TestClient

from app.main import app

FIXTURES = pathlib.Path(__file__).with_name("golden_queries.jsonl")


def _sorted(rows, col, desc):
    vals = [r[col] for r in rows if r[col] is not None]
    return vals == sorted(vals, reverse=desc)


def check(payload: dict, spec: dict) -> str | None:
    if spec.get("refused"):
        return None if payload.get("_refused") else "expected a refusal"
    if spec.get("allowed") and payload.get("security", {}).get("allowed") is not True:
        return "expected security.allowed=true"
    rows = payload.get("rows", [])
    rc = payload.get("row_count", 0)
    if "row_count" in spec and rc != spec["row_count"]:
        return f"row_count {rc} != {spec['row_count']}"
    if "min_rows" in spec and rc < spec["min_rows"]:
        return f"row_count {rc} < min {spec['min_rows']}"
    if "sorted_desc_col" in spec and not _sorted(rows, spec["sorted_desc_col"], True):
        return "rows not sorted descending"
    if "sorted_asc_col" in spec and not _sorted(rows, spec["sorted_asc_col"], False):
        return "rows not sorted ascending"
    if spec.get("limit_injected") and not payload.get("security", {}).get("limit_injected"):
        return "expected limit_injected"
    return None


def main() -> None:
    client = TestClient(app)
    passed = total = 0
    for line in FIXTURES.read_text().splitlines():
        if not line.strip():
            continue
        case = json.loads(line)
        total += 1
        r = client.post("/api/query", json={"question": case["question"]})
        if r.status_code == 200:
            payload = r.json()
        else:
            payload = {"_refused": True, "detail": r.json().get("detail", "")}
        err = check(payload, case["assert"])
        status = "PASS" if err is None else "FAIL"
        passed += err is None
        print(f"{status}  {case['question']}  ({err or 'ok'})")
    print(f"\nexecution_accuracy: {passed}/{total}")
    sys.exit(0 if passed / total >= 0.9 else 1)


if __name__ == "__main__":
    main()
