"""Schema allowlist — the single source of truth for what the LLM may see and touch.

The decoy table ``internal_credentials`` deliberately exists in the database but
is absent here; the validator and the restricted DB role must both reject it.
"""

ALLOWED_TABLES: dict[str, dict] = {
    "customers": {
        "columns": ["id", "name", "email", "country", "city", "signup_date", "segment"],
        "description": "One row per customer. segment is one of consumer|smb|enterprise.",
    },
    "products": {
        "columns": ["id", "name", "category", "unit_price", "cost", "active"],
        "description": "Product catalog with sale price and internal cost (margin = unit_price - cost).",
    },
    "orders": {
        "columns": ["id", "customer_id", "order_date", "status", "shipping_country"],
        "description": "Order headers. status is one of completed|shipped|pending|cancelled.",
    },
    "order_items": {
        "columns": ["id", "order_id", "product_id", "quantity", "unit_price"],
        "description": "Order lines; revenue for a line is quantity * unit_price.",
    },
}

RELATIONSHIPS = [
    "orders.customer_id -> customers.id",
    "order_items.order_id -> orders.id",
    "order_items.product_id -> products.id",
]

ALLOWED_FUNCTIONS: set[str] = {
    # aggregates
    "count", "sum", "avg", "min", "max",
    # date/time
    "date", "date_trunc", "extract", "now", "current_date", "to_char", "strftime",
    # math
    "round", "abs", "ceil", "floor", "power", "sqrt", "coalesce", "nullif",
    # string basics
    "lower", "upper", "trim", "length", "substr", "substring", "concat", "cast",
    # window helpers commonly emitted by models
    "rank", "row_number", "dense_rank",
}

MAX_ROWS = 100
STATEMENT_TIMEOUT_SECONDS = 5


def schema_prompt() -> str:
    """Render the allowlisted schema as the ONLY schema context the LLM sees."""
    lines = ["You may query ONLY these PostgreSQL tables:"]
    for table, meta in ALLOWED_TABLES.items():
        lines.append(f"- {table}({', '.join(meta['columns'])}) — {meta['description']}")
    lines.append("Relationships: " + "; ".join(RELATIONSHIPS))
    lines.append(f"Always produce a single SELECT statement with LIMIT <= {MAX_ROWS}.")
    return "\n".join(lines)


def schema_payload() -> dict:
    """What GET /api/schema returns — exactly the LLM's view, nothing more."""
    return {
        "tables": [
            {"name": t, "columns": m["columns"], "description": m["description"]}
            for t, m in ALLOWED_TABLES.items()
        ],
        "relationships": RELATIONSHIPS,
        "allowed_functions": sorted(ALLOWED_FUNCTIONS),
        "max_rows": MAX_ROWS,
        "statement_timeout_seconds": STATEMENT_TIMEOUT_SECONDS,
    }
