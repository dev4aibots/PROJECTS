"""
ZeroTrust-SQL — AST-level SQL guardrails for NL analytics
=========================================================
Natural-language questions become SQL, but NOTHING reaches the database
without passing an AST safety interceptor built on sqlglot:

  - single statement only (kills `...; DROP TABLE orders;` injections)
  - SELECT-only (no DDL/DML/PRAGMA/ATTACH — checked on the *parsed tree*,
    not with regex, so comment-obfuscation `DR/**/OP` doesn't help)
  - table allow-list {products, customers, orders, order_items}
  - suspicious function blocklist (load_extension, readfile, writefile)
  - LIMIT <= 200 enforced (injected when missing)

Demo mode (no keys): pattern-matched NL→SQL over a seeded, deterministic
SQLite warehouse opened read-only. With GROQ_API_KEY set, Llama 3 writes the
SQL from the live schema — and STILL goes through the same interceptor.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from typing import Any, Optional

import sqlglot
from sqlglot import exp
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="ZeroTrust-SQL",
    description="AST SQL guardrails: NL→SQL analytics where nothing hits the DB without passing a sqlglot safety interceptor.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Demo warehouse — deterministic seeded sales data, opened READ-ONLY
# ---------------------------------------------------------------------------
ALLOWED_TABLES = {"products", "customers", "orders", "order_items"}
MAX_LIMIT = 200

_DB_PATH = os.path.join(tempfile.gettempdir(), "zerotrust_warehouse.db")


def _seed_db() -> None:
    if os.path.exists(_DB_PATH):
        return
    con = sqlite3.connect(_DB_PATH)
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL);
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, country TEXT, signup_date TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, order_date TEXT, status TEXT);
        CREATE TABLE order_items (id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER, quantity INTEGER, unit_price REAL);
        """
    )
    products = [
        (1, "Laptop Pro 15", "Electronics", 1899.00),
        (2, "Wireless Mouse", "Electronics", 39.99),
        (3, "Mechanical Keyboard", "Electronics", 129.00),
        (4, "Standing Desk", "Furniture", 549.00),
        (5, "Ergo Chair", "Furniture", 429.00),
        (6, "Monitor 27in 4K", "Electronics", 479.00),
        (7, "USB-C Dock", "Electronics", 189.00),
        (8, "Desk Lamp", "Furniture", 59.00),
        (9, "Notebook Set", "Office", 19.50),
        (10, "Whiteboard", "Office", 89.00),
    ]
    customers = [
        (1, "Acme Corp", "USA", "2024-01-15"),
        (2, "Globex GmbH", "Germany", "2024-02-20"),
        (3, "Initech LLC", "USA", "2024-03-05"),
        (4, "Umbrella SA", "France", "2024-04-11"),
        (5, "Stark Industries", "USA", "2024-05-02"),
        (6, "Wayne Enterprises", "UK", "2024-06-18"),
        (7, "Hooli KK", "Japan", "2024-07-09"),
        (8, "Pied Piper Inc", "USA", "2024-08-23"),
    ]
    cur.executemany("INSERT INTO products VALUES (?,?,?,?)", products)
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?)", customers)

    # Deterministic pseudo-random orders (LCG so every deploy seeds identically)
    seed = 42
    def rnd(n: int) -> int:
        nonlocal seed
        seed = (seed * 1103515245 + 12345) % (2**31)
        return seed % n

    oid = 0
    iid = 0
    orders = []
    items = []
    for month in range(1, 13):
        for _ in range(6 + rnd(5)):
            oid += 1
            cust = 1 + rnd(len(customers))
            day = 1 + rnd(28)
            status = ["completed", "completed", "completed", "shipped", "cancelled"][rnd(5)]
            orders.append((oid, cust, f"2025-{month:02d}-{day:02d}", status))
            for _ in range(1 + rnd(4)):
                iid += 1
                pid = 1 + rnd(len(products))
                qty = 1 + rnd(5)
                items.append((iid, oid, pid, qty, products[pid - 1][3]))
    cur.executemany("INSERT INTO orders VALUES (?,?,?,?)", orders)
    cur.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", items)
    con.commit()
    con.close()


def _connect_ro() -> sqlite3.Connection:
    _seed_db()
    return sqlite3.connect(f"file:{_DB_PATH}?mode=ro", uri=True)


SCHEMA_DOC = {
    "products": {"columns": {"id": "INTEGER", "name": "TEXT", "category": "TEXT", "price": "REAL"}},
    "customers": {"columns": {"id": "INTEGER", "name": "TEXT", "country": "TEXT", "signup_date": "TEXT"}},
    "orders": {"columns": {"id": "INTEGER", "customer_id": "INTEGER", "order_date": "TEXT", "status": "TEXT"}},
    "order_items": {"columns": {"id": "INTEGER", "order_id": "INTEGER", "product_id": "INTEGER", "quantity": "INTEGER", "unit_price": "REAL"}},
}

# ---------------------------------------------------------------------------
# THE AST SAFETY INTERCEPTOR
# ---------------------------------------------------------------------------
SUSPICIOUS_FUNCS = {"load_extension", "readfile", "writefile", "fts3_tokenizer", "edit"}


class GuardVerdict(dict):
    """{approved: bool, reason: str, safe_sql: Optional[str], checks: [..]}"""


def guard_sql(raw_sql: str) -> GuardVerdict:
    checks: list[dict[str, Any]] = []

    def fail(reason: str) -> GuardVerdict:
        checks.append({"check": "verdict", "passed": False, "detail": reason})
        return GuardVerdict(approved=False, reason=reason, safe_sql=None, checks=checks)

    # 1. Parse — everything below operates on the AST, never on raw text.
    try:
        statements = sqlglot.parse(raw_sql, read="sqlite")
    except Exception as e:
        return fail(f"unparseable SQL: {e}")
    statements = [s for s in statements if s is not None]
    if not statements:
        return fail("empty statement")
    checks.append({"check": "parse", "passed": True, "detail": f"{len(statements)} statement(s) parsed"})

    # 2. Single statement only
    if len(statements) > 1:
        return fail(f"multi-statement input rejected ({len(statements)} statements) — classic injection vector")
    tree = statements[0]
    checks.append({"check": "single_statement", "passed": True, "detail": "exactly one statement"})

    # 3. SELECT-only, verified on node types across the whole tree
    forbidden_nodes = (
        exp.Drop, exp.Delete, exp.Update, exp.Insert, exp.Alter,
        exp.Create, exp.TruncateTable, exp.Pragma, exp.Attach, exp.Detach,
        exp.Command, exp.Transaction, exp.Grant,
    )
    if not isinstance(tree, exp.Select) and not isinstance(tree, exp.Union):
        return fail(f"non-SELECT statement rejected: {type(tree).__name__.upper()}")
    for node in tree.walk():
        if isinstance(node, forbidden_nodes):
            return fail(f"forbidden operation in tree: {type(node).__name__.upper()}")
        if isinstance(node, exp.Into):
            return fail("SELECT INTO rejected (creates tables)")
    checks.append({"check": "select_only", "passed": True, "detail": "read-only statement"})

    # 4. Table allow-list
    tables = {t.name.lower() for t in tree.find_all(exp.Table)}
    outside = tables - ALLOWED_TABLES
    if outside:
        return fail(f"table(s) outside allow-list: {sorted(outside)}")
    checks.append({"check": "table_allowlist", "passed": True, "detail": f"tables: {sorted(tables) or ['(none)']}"})

    # 5. Suspicious functions
    for fn in tree.find_all(exp.Anonymous):
        if str(fn.this).lower() in SUSPICIOUS_FUNCS:
            return fail(f"suspicious function: {fn.this}")
    for fn in tree.find_all(exp.Func):
        name = fn.sql_name().lower() if hasattr(fn, "sql_name") else ""
        if name in SUSPICIOUS_FUNCS:
            return fail(f"suspicious function: {name}")
    checks.append({"check": "function_blocklist", "passed": True, "detail": "no dangerous functions"})

    # 6. LIMIT enforcement (inject or clamp on the AST, then re-render)
    limit_node = tree.args.get("limit")
    if limit_node is None:
        tree = tree.limit(MAX_LIMIT)
        checks.append({"check": "limit", "passed": True, "detail": f"LIMIT {MAX_LIMIT} injected"})
    else:
        try:
            current = int(limit_node.expression.this)
        except Exception:
            current = MAX_LIMIT + 1
        if current > MAX_LIMIT:
            tree = tree.limit(MAX_LIMIT)
            checks.append({"check": "limit", "passed": True, "detail": f"LIMIT clamped {current} → {MAX_LIMIT}"})
        else:
            checks.append({"check": "limit", "passed": True, "detail": f"LIMIT {current} within bounds"})

    safe_sql = tree.sql(dialect="sqlite")
    checks.append({"check": "verdict", "passed": True, "detail": "APPROVED"})
    return GuardVerdict(approved=True, reason="approved", safe_sql=safe_sql, checks=checks)


# ---------------------------------------------------------------------------
# NL → SQL: Groq/Llama when key set; deterministic patterns otherwise
# ---------------------------------------------------------------------------
DEMO_NL2SQL: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"top\s+(\d+)?\s*(selling\s+)?products|best\s+sell", re.I),
     """SELECT p.name, SUM(oi.quantity) AS units_sold, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM order_items oi JOIN products p ON p.id = oi.product_id
        JOIN orders o ON o.id = oi.order_id WHERE o.status != 'cancelled'
        GROUP BY p.id ORDER BY revenue DESC LIMIT 10""",
     "bar"),
    (re.compile(r"revenue\s+by\s+(country|region)", re.I),
     """SELECT c.country, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM order_items oi JOIN orders o ON o.id = oi.order_id
        JOIN customers c ON c.id = o.customer_id WHERE o.status != 'cancelled'
        GROUP BY c.country ORDER BY revenue DESC""",
     "bar"),
    (re.compile(r"revenue\s+by\s+categor|category\s+revenue", re.I),
     """SELECT p.category, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM order_items oi JOIN products p ON p.id = oi.product_id
        JOIN orders o ON o.id = oi.order_id WHERE o.status != 'cancelled'
        GROUP BY p.category ORDER BY revenue DESC""",
     "bar"),
    (re.compile(r"month(ly)?\s+(revenue|trend|sales)|revenue\s+per\s+month|trend", re.I),
     """SELECT substr(o.order_date, 1, 7) AS month, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue
        FROM order_items oi JOIN orders o ON o.id = oi.order_id WHERE o.status != 'cancelled'
        GROUP BY month ORDER BY month""",
     "bar"),
    (re.compile(r"(average|avg)\s+order\s+value", re.I),
     """SELECT ROUND(AVG(order_total), 2) AS avg_order_value FROM (
        SELECT o.id, SUM(oi.quantity * oi.unit_price) AS order_total
        FROM orders o JOIN order_items oi ON oi.order_id = o.id
        WHERE o.status != 'cancelled' GROUP BY o.id)""",
     "table"),
    (re.compile(r"top\s+\d*\s*customers|biggest\s+customers|customers\s+by\s+(revenue|spend)", re.I),
     """SELECT c.name, c.country, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_spend
        FROM customers c JOIN orders o ON o.customer_id = c.id
        JOIN order_items oi ON oi.order_id = o.id WHERE o.status != 'cancelled'
        GROUP BY c.id ORDER BY total_spend DESC LIMIT 5""",
     "bar"),
    (re.compile(r"cancel+ed\s+orders|cancellation", re.I),
     """SELECT substr(order_date, 1, 7) AS month, COUNT(*) AS cancelled_orders
        FROM orders WHERE status = 'cancelled' GROUP BY month ORDER BY month""",
     "bar"),
    (re.compile(r"how\s+many\s+orders|order\s+count|total\s+orders", re.I),
     "SELECT status, COUNT(*) AS orders FROM orders GROUP BY status ORDER BY orders DESC",
     "bar"),
]


def nl_to_sql(question: str) -> tuple[str, str, str]:
    """returns (sql, engine, chart_type)"""
    if os.environ.get("GROQ_API_KEY"):
        try:
            import urllib.request
            schema_desc = json.dumps(SCHEMA_DOC)
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
                    "content-type": "application/json",
                },
                data=json.dumps({
                    "model": "llama-3.3-70b-versatile",
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": f"You write a single SQLite SELECT statement for this schema: {schema_desc}. Reply with ONLY the SQL, no fences, no prose."},
                        {"role": "user", "content": question},
                    ],
                }).encode(),
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
            sql = data["choices"][0]["message"]["content"].strip().strip("`")
            if sql.lower().startswith("sql"):
                sql = sql[3:].strip()
            return sql, "groq/llama-3.3-70b", "table"
        except Exception:
            pass  # fall through to demo patterns
    for pattern, sql, chart in DEMO_NL2SQL:
        if pattern.search(question):
            return re.sub(r"\s+", " ", sql).strip(), "demo-patterns", chart
    # Direct SQL passthrough? If the question *looks like* SQL, run it through the guard as-is.
    if re.match(r"^\s*(select|with|drop|delete|update|insert|alter|create|pragma|attach)\b", question, re.I) or ";" in question:
        return question, "raw-passthrough", "table"
    # default: category revenue
    return re.sub(r"\s+", " ", DEMO_NL2SQL[2][1]).strip(), "demo-default", "bar"


# ---------------------------------------------------------------------------
# Audit log (in-memory per instance)
# ---------------------------------------------------------------------------
AUDIT: list[dict[str, Any]] = []


def audit(entry: dict[str, Any]) -> None:
    entry["at"] = datetime.now(timezone.utc).isoformat()
    AUDIT.insert(0, entry)
    del AUDIT[500:]


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------
def run_guarded(sql: str, source: str, question: Optional[str] = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    verdict = guard_sql(sql)
    if not verdict["approved"]:
        audit({"outcome": "BLOCKED", "source": source, "question": question, "sql": sql, "reason": verdict["reason"]})
        return {
            "ast_verdict": "BLOCKED",
            "reason": verdict["reason"],
            "checks": verdict["checks"],
            "sql": sql,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    con = _connect_ro()
    try:
        cur = con.execute(verdict["safe_sql"])
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = [list(r) for r in cur.fetchall()]
    except sqlite3.Error as e:
        audit({"outcome": "EXEC_ERROR", "source": source, "question": question, "sql": verdict["safe_sql"], "reason": str(e)})
        return {
            "ast_verdict": "APPROVED",
            "exec_error": str(e),
            "checks": verdict["checks"],
            "sql": verdict["safe_sql"],
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
        }
    finally:
        con.close()
    audit({"outcome": "EXECUTED", "source": source, "question": question, "sql": verdict["safe_sql"], "rows": len(rows)})
    return {
        "ast_verdict": "APPROVED",
        "checks": verdict["checks"],
        "sql": verdict["safe_sql"],
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
    }


# ---------------------------------------------------------------------------
# API models & endpoints
# ---------------------------------------------------------------------------
class QueryIn(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)


class SqlIn(BaseModel):
    sql: str = Field(..., min_length=2, max_length=5000)


@app.post("/api/query")
def api_query(q: QueryIn):
    sql, engine, chart = nl_to_sql(q.question)
    result = run_guarded(sql, source=f"nl2sql:{engine}", question=q.question)
    result["question"] = q.question
    result["nl2sql_engine"] = engine
    if result.get("ast_verdict") == "APPROVED" and result.get("columns"):
        cols = result["columns"]
        if chart == "bar" and len(cols) >= 2:
            result["chart"] = {"type": "bar", "x": cols[0], "y": cols[-1]}
        else:
            result["chart"] = {"type": "table"}
    return result


@app.post("/api/sql")
def api_sql(q: SqlIn):
    """Raw SQL through the same guard — the injection-attack demo endpoint."""
    return run_guarded(q.sql, source="raw-sql")


@app.get("/api/schema")
def api_schema():
    return {"tables": SCHEMA_DOC, "allow_list": sorted(ALLOWED_TABLES), "max_limit": MAX_LIMIT}


@app.get("/api/audit")
def api_audit():
    return {"count": len(AUDIT), "blocked": sum(1 for a in AUDIT if a["outcome"] == "BLOCKED"), "entries": AUDIT[:100]}


@app.get("/api/health")
def api_health():
    return {
        "status": "ok",
        "service": "zerotrust-sql",
        "mode": "live" if os.environ.get("GROQ_API_KEY") else "demo",
        "integrations": {"groq_nl2sql": bool(os.environ.get("GROQ_API_KEY"))},
        "guard": {"allow_list": sorted(ALLOWED_TABLES), "max_limit": MAX_LIMIT, "engine": "sqlglot AST"},
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/")
def root():
    path = os.path.join(os.path.dirname(__file__), "..", "public", "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse({"service": "zerotrust-sql", "docs": "/docs"})
