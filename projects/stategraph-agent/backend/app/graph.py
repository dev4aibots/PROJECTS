"""LangGraph workflow with typed agent services and a durable human boundary."""
from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .agents import AgentServices, Analysis, Review, Source, build_agent_services


RISK_TERMS = {
    "financial": "financial_domain",
    "legal": "legal_domain",
    "medical": "medical_domain",
    "risk": "explicit_risk_request",
    "sensitive": "sensitive_content",
    "uncertain": "explicit_uncertainty",
}


def risk_flags_for(request: str, review: Review) -> list[str]:
    """Apply the deterministic human-gate policy used by runtime and evals."""
    normalized = request.casefold()
    flags = [flag for term, flag in RISK_TERMS.items() if term in normalized]
    if review.confidence < 0.5:
        flags.append("low_model_confidence")
    return flags


class AgentState(TypedDict, total=False):
    title: str
    input: str
    memories: list[str]
    events: Annotated[list[dict], operator.add]
    sources: list[dict]
    analysis: dict
    model_review: dict
    risk_flags: list[str]
    result: str
    rejected: bool


def build_graph(checkpointer=None, services: AgentServices | None = None):
    agents = services or build_agent_services("local")

    def research(state: AgentState) -> dict:
        sources = agents.research(state["title"], state["input"])
        return {
            "sources": [item.model_dump(mode="json") for item in sources],
            "events": [{"agent": "research", "output": f"Gathered {len(sources)} validated HTTPS source(s) via {agents.mode} mode"}],
        }

    def analyst(state: AgentState) -> dict:
        sources = [Source.model_validate(item) for item in state.get("sources", [])]
        analysis = agents.analyze(state["input"], sources)
        return {
            "analysis": analysis.model_dump(mode="json"),
            "events": [{"agent": "analyst", "output": analysis.summary[:500]}],
        }

    def reviewer(state: AgentState) -> dict:
        analysis = Analysis.model_validate(state["analysis"])
        model_review = agents.review(state["input"], analysis)
        flags = risk_flags_for(state["input"], model_review)
        if flags:
            decision = interrupt({
                "reason": "Risk policy requires a human veto",
                "risk_flags": flags,
            })
            approved = bool(decision.get("approved")) if isinstance(decision, dict) else bool(decision)
            if not approved:
                return {
                    "model_review": model_review.model_dump(mode="json"),
                    "risk_flags": flags,
                    "rejected": True,
                    "events": [{"agent": "reviewer", "output": "Human rejected the run"}],
                }
        return {
            "model_review": model_review.model_dump(mode="json"),
            "risk_flags": flags,
            "events": [{"agent": "reviewer", "output": f"Review passed at confidence {model_review.confidence:.2f}"}],
        }

    def route_after_review(state: AgentState) -> str:
        return END if state.get("rejected") else "writer"

    def writer(state: AgentState) -> dict:
        analysis = Analysis.model_validate(state["analysis"])
        sources = [Source.model_validate(item) for item in state.get("sources", [])]
        draft = agents.write(state["title"], state["input"], analysis, sources)
        return {
            "result": draft.markdown,
            "events": [{"agent": "writer", "output": f"Final cited deliverable created with {len(draft.cited_source_urls)} source(s)"}],
        }

    builder = StateGraph(AgentState)
    builder.add_node("research", research)
    builder.add_node("analyst", analyst)
    builder.add_node("reviewer", reviewer)
    builder.add_node("writer", writer)
    builder.add_edge(START, "research")
    builder.add_edge("research", "analyst")
    builder.add_edge("analyst", "reviewer")
    builder.add_conditional_edges("reviewer", route_after_review, {"writer": "writer", END: END})
    builder.add_edge("writer", END)
    return builder.compile(checkpointer=checkpointer or InMemorySaver())


graph = build_graph()
