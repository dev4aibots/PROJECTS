"""Prompt construction and JSON extraction for live chat providers.

The system prompt pins the model to evidence-only answering with a strict
JSON output contract. Downstream, deterministic citation validation is the
real enforcement — this prompt just maximizes the chance the model complies
on the first try.
"""

from __future__ import annotations

import json

from ..domain.models import RetrievedChunk

SYSTEM_PROMPT = """You are a document question-answering assistant.

RULES (non-negotiable):
1. Answer ONLY from the EVIDENCE blocks provided. Never use outside knowledge.
2. If the evidence does not answer the question, reply with an empty citations
   list and the exact answer: "INSUFFICIENT_EVIDENCE".
3. Every factual claim must carry a citation naming the chunk_id it came from,
   with an "excerpt" copied VERBATIM from that chunk (10-200 characters).
4. Output MUST be a single JSON object, no markdown fences, matching:
   {"answer": "<string>", "citations": [{"chunk_id": "<uuid>", "page": <int>, "excerpt": "<verbatim>"}]}
"""


def build_user_prompt(question: str, evidence: list[RetrievedChunk]) -> str:
    blocks = []
    for chunk in evidence:
        blocks.append(
            f"[chunk_id={chunk.chunk_id} document={chunk.filename} page={chunk.page_number}]\n"
            f"{chunk.content}"
        )
    return (
        "EVIDENCE:\n\n" + "\n\n---\n\n".join(blocks) + f"\n\nQUESTION: {question}\n\n"
        "Respond with the JSON object only."
    )


def extract_json_object(raw: str) -> dict:
    """Pull the first JSON object out of possibly-noisy model output.

    Tolerates markdown fences and leading/trailing prose. Raises ValueError
    if no parseable object exists — callers translate to MalformedModelOutputError.
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first == -1 or last == -1 or last <= first:
        raise ValueError("no JSON object in model output")
    return json.loads(cleaned[first : last + 1])
