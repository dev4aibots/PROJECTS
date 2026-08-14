"""SQL generation provider abstraction.

Live mode: Groq primary -> Gemini fallback with one corrective retry on
malformed structured output (owner keys required; not exercised locally).
Deterministic mode: a template mapping over the allowlisted schema so the full
pipeline — including the Attack Lab — runs with zero secrets. The validator is
the product; the generator is deliberately swappable.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass

from .allowlist import schema_prompt

MAX_QUESTION_LENGTH = 500
INJECTION_PHRASES = [
    "ignore previous instructions", "ignore your rules", "you are now",
    "system prompt", "developer mode", "disregard",
]


class GenerationError(Exception):
    """Raised when a SQL draft cannot be produced (bad output twice, provider down)."""


@dataclass
class Draft:
    sql: str
    explanation: str
    tables_used: list[str]
    confidence: float
    model: str
    injection_flags: list[str]


def input_guard(question: str) -> list[str]:
    """Length/empty checks raise; suspicious phrases are logged, not blocked —
    the SQL validators are the real wall."""
    if not question or not question.strip():
        raise ValueError("question must not be empty")
    if len(question) > MAX_QUESTION_LENGTH:
        raise ValueError(f"question exceeds {MAX_QUESTION_LENGTH} characters")
    lowered = question.lower()
    return [p for p in INJECTION_PHRASES if p in lowered]


class DeterministicGenerator:
    """Keyless template generator for local/demo mode.

    Attack-lab questions intentionally produce the malicious SQL a jailbroken
    model would emit — proving the validator, not the model, is the defense.
    """

    model = "deterministic-templates"

    TEMPLATES: list[tuple[str, str, str, list[str]]] = [
        (r"delete all customers",
         "DELETE FROM customers",
         "Attempted destructive delete (attack-lab).", ["customers"]),
        (r"show customers.*drop table",
         "SELECT name FROM customers; DROP TABLE orders;",
         "Piggybacked multi-statement attack (attack-lab).", ["customers", "orders"]),
        (r"drop table orders",
         "DROP TABLE orders",
         "Attempted table drop (attack-lab).", ["orders"]),
        (r"internal_credentials",
         "SELECT * FROM internal_credentials",
         "Attempted read of the decoy sensitive table (attack-lab).",
         ["internal_credentials"]),
        (r"dbadmingpt|update customers set",
         "UPDATE customers SET segment = 'vip'",
         "Prompt-injection produced an UPDATE (attack-lab).", ["customers"]),
        (r"1,?000,?000 rows|million rows",
         "SELECT id, order_id, product_id, quantity, unit_price FROM order_items LIMIT 1000000",
         "Requested one million order item rows.", ["order_items"]),
        (r"pg_shadow",
         "SELECT * FROM pg_shadow",
         "Attempted read of Postgres password hashes (attack-lab).", ["pg_shadow"]),
        (r"pg_sleep",
         "SELECT pg_sleep(60)",
         "Attempted denial-of-service sleep call (attack-lab).", []),
        (r"top (\d+|ten)? ?customers by revenue",
         "SELECT c.name, SUM(oi.quantity * oi.unit_price) AS revenue "
         "FROM customers AS c JOIN orders AS o ON o.customer_id = c.id "
         "JOIN order_items AS oi ON oi.order_id = o.id "
         "WHERE o.status = 'completed' GROUP BY c.name ORDER BY revenue DESC LIMIT 10",
         "Ranks customers by completed-order revenue, highest first.",
         ["customers", "orders", "order_items"]),
        (r"monthly revenue",
         "SELECT SUBSTR(o.order_date, 1, 7) AS month, "
         "ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue "
         "FROM orders AS o JOIN order_items AS oi ON oi.order_id = o.id "
         "WHERE o.status = 'completed' GROUP BY month ORDER BY month LIMIT 24",
         "Sums completed-order revenue per calendar month.",
         ["orders", "order_items"]),
        (r"category by margin|best category",
         "SELECT p.category, ROUND(SUM((p.unit_price - p.cost) * oi.quantity), 2) AS margin "
         "FROM products AS p JOIN order_items AS oi ON oi.product_id = p.id "
         "GROUP BY p.category ORDER BY margin DESC LIMIT 10",
         "Ranks product categories by total gross margin.",
         ["products", "order_items"]),
        (r"customers (in|from) (\w+)",
         "SELECT name, city, segment FROM customers WHERE country = 'DE' LIMIT 50",
         "Lists customers filtered by country.", ["customers"]),
        (r"how many orders.*completed|completed orders count",
         "SELECT COUNT(id) AS completed_orders FROM orders "
         "WHERE status = 'completed' LIMIT 1",
         "Counts completed orders.", ["orders"]),
        (r"top (\d+|five)? ?products by units|units sold",
         "SELECT p.name, SUM(oi.quantity) AS units_sold "
         "FROM products AS p JOIN order_items AS oi ON oi.product_id = p.id "
         "GROUP BY p.name ORDER BY units_sold DESC LIMIT 5",
         "Ranks products by total units sold.", ["products", "order_items"]),
        (r"most expensive products",
         "SELECT name, category, unit_price FROM products "
         "ORDER BY unit_price DESC LIMIT 15",
         "Lists products by unit price, highest first.", ["products"]),
        (r"orders by status|status breakdown|orders per status",
         "SELECT status, COUNT(id) AS orders FROM orders GROUP BY status "
         "ORDER BY orders DESC LIMIT 10",
         "Counts orders per status.", ["orders"]),
        (r"average order value",
         "SELECT ROUND(AVG(t.total), 2) AS avg_order_value FROM "
         "(SELECT o.id, SUM(oi.quantity * oi.unit_price) AS total FROM orders AS o "
         "JOIN order_items AS oi ON oi.order_id = o.id "
         "WHERE o.status = 'completed' GROUP BY o.id) AS t LIMIT 1",
         "Computes the average value of a completed order.",
         ["orders", "order_items"]),
        (r"active products|product catalog",
         "SELECT name, category, unit_price FROM products WHERE active = 1 "
         "ORDER BY unit_price DESC LIMIT 40",
         "Lists active products by price.", ["products"]),
        (r"segment.*revenue|revenue.*segment",
         "SELECT c.segment, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue "
         "FROM customers AS c JOIN orders AS o ON o.customer_id = c.id "
         "JOIN order_items AS oi ON oi.order_id = o.id "
         "WHERE o.status = 'completed' GROUP BY c.segment ORDER BY revenue DESC LIMIT 10",
         "Total completed revenue per customer segment.",
         ["customers", "orders", "order_items"]),
        (r"cancelled orders",
         "SELECT COUNT(id) AS cancelled_orders FROM orders "
         "WHERE status = 'cancelled' LIMIT 1",
         "Counts cancelled orders.", ["orders"]),
        (r"countries.*orders|orders.*country",
         "SELECT shipping_country, COUNT(id) AS orders FROM orders "
         "GROUP BY shipping_country ORDER BY orders DESC LIMIT 10",
         "Order volume by shipping country.", ["orders"]),
    ]

    def generate(self, question: str) -> Draft:
        flags = input_guard(question)
        lowered = question.lower()
        for pattern, sql, explanation, tables in self.TEMPLATES:
            if re.search(pattern, lowered):
                return Draft(sql=sql, explanation=explanation, tables_used=tables,
                             confidence=0.9, model=self.model, injection_flags=flags)
        raise GenerationError(
            "deterministic mode has no template for this question; "
            "try an example question or run with provider keys")


class LiveGenerator:
    """Groq primary → Gemini fallback with one corrective retry each.

    Only constructed when keys are present; every response is still forced
    through the identical validation pipeline.
    """

    model = "groq/llama-3.3-70b-versatile"

    def __init__(self) -> None:
        self.groq_key = os.environ.get("GROQ_API_KEY", "")
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "")

    def _prompt(self, question: str) -> str:
        return (
            f"{schema_prompt()}\n\nUser question: {question}\n"
            'Respond ONLY with JSON: {"sql": str, "explanation": str, '
            '"tables_used": [str], "confidence": float}'
        )

    def _call_groq(self, prompt: str) -> str:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps({
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            }).encode(),
            headers={"Authorization": f"Bearer {self.groq_key}",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)["choices"][0]["message"]["content"]

    def _call_gemini(self, prompt: str) -> str:
        req = urllib.request.Request(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={self.gemini_key}",
            data=json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            }).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)["candidates"][0]["content"]["parts"][0]["text"]

    def generate(self, question: str) -> Draft:
        flags = input_guard(question)
        prompt = self._prompt(question)
        providers = []
        if self.groq_key:
            providers.append(("groq/llama-3.3-70b-versatile", self._call_groq))
        if self.gemini_key:
            providers.append(("gemini-2.0-flash", self._call_gemini))
        last_error: Exception | None = None
        for model, call in providers:
            for attempt in range(2):  # one corrective retry on malformed output
                try:
                    raw = call(prompt if attempt == 0 else
                               prompt + "\nYour previous output was not valid JSON. "
                                        "Return ONLY the JSON object.")
                    data = json.loads(raw)
                    return Draft(sql=data["sql"], explanation=data.get("explanation", ""),
                                 tables_used=data.get("tables_used", []),
                                 confidence=float(data.get("confidence", 0.5)),
                                 model=model, injection_flags=flags)
                except (json.JSONDecodeError, KeyError, TypeError) as err:
                    last_error = err
                    continue
                except Exception as err:  # provider/network failure -> next provider
                    last_error = err
                    break
        raise GenerationError(f"all SQL generation providers failed: {last_error}")


def build_generator():
    if os.environ.get("GROQ_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        return LiveGenerator()
    return DeterministicGenerator()
