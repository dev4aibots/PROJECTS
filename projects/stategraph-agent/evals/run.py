"""Deterministic held-out release evaluation for routing and citation policy."""
from __future__ import annotations

import json
from pathlib import Path

from app.agents import AgentDependencyError, AgentServices, Analysis, Draft, Source
from app.graph import risk_flags_for
from app.agents import Review


ROOT = Path(__file__).resolve().parent


class CaseSearch:
    def __init__(self, urls: list[str]) -> None:
        self.urls = urls

    def search(self, _query: str) -> list[Source]:
        return [
            Source(title=f"Evidence {index}", url=url, snippet="Held-out evidence fixture.")
            for index, url in enumerate(self.urls, start=1)
        ]


class CaseProvider:
    name = "held-out-case"

    def __init__(self, citations: list[str]) -> None:
        self.citations = citations

    def generate(self, schema, _system, _payload):
        if schema is Draft:
            return Draft(markdown="Held-out answer", cited_source_urls=self.citations)
        return Analysis(summary="Held-out analysis", uncertainty="Fixture evaluation")


def citation_policy_accepts(case: dict) -> bool:
    services = AgentServices(
        CaseSearch(case["allowed"]), CaseProvider(case["cited"]), "held-out"
    )
    sources = services.research("Held-out", "citation policy")
    try:
        services.write(
            "Held-out",
            "citation policy",
            Analysis(summary="Held-out analysis", uncertainty="Fixture evaluation"),
            sources,
        )
        return True
    except AgentDependencyError:
        return False


def main() -> int:
    corpus = json.loads((ROOT / "cases.json").read_text())
    routing_results = []
    for case in corpus["routing_cases"]:
        flags = risk_flags_for(
            case["request"], Review(concerns=[], confidence=case["confidence"])
        )
        actual = bool(flags)
        routing_results.append({
            "id": case["id"],
            "passed": actual == case["expect_gate"],
            "expected_gate": case["expect_gate"],
            "actual_gate": actual,
            "flags": flags,
        })

    citation_results = []
    for case in corpus["citation_cases"]:
        actual = citation_policy_accepts(case)
        citation_results.append({
            "id": case["id"],
            "passed": actual == case["expect_accept"],
            "expected_accept": case["expect_accept"],
            "actual_accept": actual,
        })

    routing_accuracy = sum(item["passed"] for item in routing_results) / len(routing_results)
    citation_accuracy = sum(item["passed"] for item in citation_results) / len(citation_results)
    thresholds = corpus["thresholds"]
    passed = (
        routing_accuracy >= thresholds["routing_accuracy"]
        and citation_accuracy >= thresholds["citation_policy_accuracy"]
    )
    report = {
        "dataset": corpus["version"],
        "metrics": {
            "routing_accuracy": routing_accuracy,
            "citation_policy_accuracy": citation_accuracy,
        },
        "thresholds": thresholds,
        "passed": passed,
        "failures": [
            item for item in routing_results + citation_results if not item["passed"]
        ],
    }
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
