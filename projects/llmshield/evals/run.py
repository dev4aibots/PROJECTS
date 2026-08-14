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
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
        "recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
        "false_positive_rate": round(fp / (fp + tn), 4) if fp + tn else 0.0,
    }


def evaluate() -> dict:
    rows = [json.loads(line) for line in (ROOT / "evals" / "attack_corpus.jsonl").read_text().splitlines() if line.strip()]
    if len(rows) != 40 or len({row["id"] for row in rows}) != 40:
        raise ValueError("corpus must contain exactly 40 uniquely identified cases")
    outputs = {}
    for guard_name in ("injection", "pii"):
        truth_label = guard_name
        tp = fp = fn = tn = 0
        failures = []
        for row in rows:
            truth = row["label"] == truth_label
            predicted = injection(row["prompt"])["verdict"] != "PASS" if guard_name == "injection" else bool(pii(row["prompt"])[0])
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
    return {"corpus_version": "1.0.0", "cases": len(rows), "label_counts": {label: sum(row["label"] == label for row in rows) for label in ("clean", "injection", "pii")}, "guards": outputs}


if __name__ == "__main__":
    result = evaluate()
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if any(data["fn"] for data in result["guards"].values()) else 0)
