#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.guards.core import injection, pii  # noqa: E402


def metrics(tp: int, fp: int, fn: int, tn: int) -> dict[str, float | int]:
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
        "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
        "false_positive_rate": round(fp / (fp + tn), 4) if fp + tn else 0.0,
    }


def _load(name: str, expected_cases: int) -> list[dict]:
    path = ROOT / "evals" / name
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    identifiers = {row.get("id") for row in rows}
    labels = {"clean", "injection", "pii"}
    if len(rows) != expected_cases or len(identifiers) != expected_cases:
        raise ValueError(f"{name} must contain exactly {expected_cases} unique cases")
    if any(row.get("label") not in labels or not isinstance(row.get("prompt"), str) for row in rows):
        raise ValueError(f"{name} contains an invalid label or prompt")
    return rows


def _evaluate_rows(rows: list[dict]) -> dict:
    outputs = {}
    for guard_name in ("injection", "pii"):
        tp = fp = fn = tn = 0
        failures = []
        for row in rows:
            truth = row["label"] == guard_name
            predicted = (
                injection(row["prompt"])["verdict"] != "PASS"
                if guard_name == "injection"
                else bool(pii(row["prompt"])[0])
            )
            if truth and predicted:
                tp += 1
            elif not truth and predicted:
                fp += 1
                failures.append({"id": row["id"], "kind": "false_positive"})
            elif truth:
                fn += 1
                failures.append({"id": row["id"], "kind": "false_negative"})
            else:
                tn += 1
        outputs[guard_name] = {**metrics(tp, fp, fn, tn), "failures": failures}
    return {
        "cases": len(rows),
        "label_counts": {
            label: sum(row["label"] == label for row in rows)
            for label in ("clean", "injection", "pii")
        },
        "guards": outputs,
    }


def evaluate() -> dict:
    authored = _load("attack_corpus.jsonl", 40)
    heldout = _load("heldout_corpus.jsonl", 30)
    return {
        "corpus_version": "2.0.0",
        "authored": _evaluate_rows(authored),
        "heldout": _evaluate_rows(heldout),
        "gate": {"minimum_recall": 0.9, "maximum_false_positive_rate": 0.1},
    }


def gate_failed(result: dict) -> bool:
    for corpus_name in ("authored", "heldout"):
        for guard in result[corpus_name]["guards"].values():
            if guard["recall"] < result["gate"]["minimum_recall"]:
                return True
            if guard["false_positive_rate"] > result["gate"]["maximum_false_positive_rate"]:
                return True
    return False


if __name__ == "__main__":
    result = evaluate()
    output = json.dumps(result, indent=2) + "\n"
    (ROOT / "evals" / "results.json").write_text(output)
    print(output, end="")
    raise SystemExit(1 if gate_failed(result) else 0)
