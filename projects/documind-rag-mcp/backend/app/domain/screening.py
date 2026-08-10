"""Question input screening: length, emptiness, injection heuristics.

Injection screening is a heuristic blast-radius reducer, not a guarantee;
the real defenses are the evidence gate and deterministic citation
validation downstream. This layer just rejects the obvious attempts early
with a clear error.
"""

from __future__ import annotations

import re

from ..core.errors import ValidationAppError

_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"you\s+are\s+now\s+(a|an)\s+",
        r"system\s*prompt",
        r"reveal\s+(your\s+)?(instructions|prompt)",
        r"</?\s*system\s*>",
        r"\bDAN\b.{0,40}jailbreak",
        r"pretend\s+(you\s+have\s+)?no\s+(rules|restrictions|guidelines)",
    )
]


def screen_question(question: str, max_chars: int = 2000) -> str:
    """Validate and normalize a user question. Returns the cleaned question."""
    q = " ".join(question.split()).strip()
    if not q:
        raise ValidationAppError("The question is empty.")
    if len(q) > max_chars:
        raise ValidationAppError(f"Questions are limited to {max_chars} characters.")
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(q):
            raise ValidationAppError(
                "The question appears to contain prompt-injection content and was rejected."
            )
    return q
