"""
ZeroTrust-SQL — AST-level SQL guardrails for NL analytics
=========================================================

Every SQL statement — whether written by an LLM or typed by a human — passes
through an sqlglot AST interceptor before touching the database:

  reject : multi-statement · any non-SELECT verb · tables outside allow-list ·
           SELECT INTO · suspicious functions (load_extension/readfile/writefile)
  enforce: LIMIT ≤ 200 (injected into the AST if missing, clamped if larger)

Execution happens on a READ-ONLY SQLite connection (mode=ro) over a bundled,
deterministically-seeded sales warehouse. Demo mode is default (no keys);
setting GROQ_API_KEY upgrades NL→SQL to Llama 3 via Groq — the guard treats
both paths as equally untrusted.
"""
import json
import os
import random
import re
import sqlite3
import time
import urllib.request

import sqlglot
from sqlglot import exp
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(
    title="ZeroTrust-SQL",
    description="AST SQL guardrails for natural-language analytics. Untrusted SQL in, safe SELECTs out.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Warehouse (deterministic seeded demo data)
# ---------------------------------------------------------------------------
DB_PATH = os.environ.get("ZTSQL_DB_PATH", "/tmp/zerotrust_warehouse.db")
ALLOWED_TABLES = {"products", "customers", "orders", "order_items"}
MAX_LIMIT = 200

SCHEMA_SQL = """
CREATE TABLE products  (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL);
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT, country TEXT, segment TEXT, signup_date TEXT);
CREATE TABLE orders    (id INTEGER PRIMARY KEY, customer_id INTEGER, order_date TEXT, status TEXT,
                        FOREIGN KEY(customer_id) REFERENCES customers(id));
CREATE TABLE order_items (id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER,
                          quantity INTEGER, unit_price REAL,
                          FOREIGN KEY(order_id) REFERENCES orders(id),
                          FOREIGN KEY(product_id) REFERENCES products(id));
"""

PRODUCTS = [
    ("Aurora Standing Desk", "Furniture", 549.0), ("Nimbus Laptop Stand", "Accessories", 79.0),
    ("Volt USB-C Dock", "Electronics", 199.0), ("Echo Mechanical Keyboard", "Electronics", 149.0),
    ("Drift Ergonomic Chair", "Furniture", 899.0), ("Pulse 4K Monitor", "Electronics", 429.0),
    ("Slate Desk Mat", "Accessories", 39.0), ("Orbit Wireless Mouse", "Electronics", 69.0),
    ("Beam LED Desk Lamp", "Accessories", 59.0), ("Terra Monitor Arm", "Accessories", 129.0),
    ("Flux Webcam Pro", "Electronics", 179.0), ("Cove Acoustic Panel", "Furniture", 89.0),
]
COUNTRIES = ["US", "DE", "GB", "FR", "JP", "CA", "AU", "NL"]
SEGMENTS = ["enterprise", "smb", "consumer"]
STATUSES = ["completed", "completed", "completed", "completed", "shipped", "pending", "refunded"]


def seed_warehouse() -> None:
    if os.path.exists(DB_PATH):
        return
    rng = random.Random(42)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)
    for i, (name, cat, price) in enumerate(PRODUCTS, 1):
        conn.execute("INSERT INTO products VALUES (?,?,?,?)", (i, name, cat, price))
    first = ["Ada", "Grace", "Alan", "Edsger", "Barbara", "Donald", "Radia", "Vint", "Margaret", "Linus",
             "Katherine", "Tim", "Frances", "Guido", "Hedy", "Dennis", "Anita", "Ken", "Shafi", "John"]
    last = ["Lovelace", "Hopper", "Turing", "Dijkstra", "Liskov", "Knuth", "Perlman", "Cerf", "Hamilton",
            "Torvalds", "Johnson", "Berners-Lee", "Allen", "Rossum", "Lamarr", "Ritchie", "Borg", "Thompson",
            "Goldwasser", "McCarthy"]
    for i in range(1, 61):
        conn.execute("INSERT INTO customers VALUES (?,?,?,?,?)", (
            i, f"{rng.choice(first)} {rng.choice(last)}", rng.choice(COUNTRIES), rng.choice(SEGMENTS),
            f"2025-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"))
    oid, iid = 0, 0
    for month in range(1, 9):  # Jan–Aug 2026
        for _ in range(rng.randint(28, 44)):
            oid += 1
            conn.execute("INSERT INTO orders VALUES (?,?,?,?)", (
                oid, rng.randint(1, 60), f"2026-{month:02d}-{rng.randint(1, 28):02d}", rng.choice(STATUSES)))
            for _ in range(rng.randint(1, 4)):
                iid += 1
                pid = rng.randint(1, len(PRODUCTS))
                conn.execute("INSERT INTO order_items VALUES (?,?,?,?,?)", (
                    iid, oid, pid, rng.randint(1, 5), PRODUCTS[pid - 1][2]))
    conn.commit()
    conn.close()


def ro_connection() -> sqlite3.Connection:
    """Defense-in-depth layer 2: the connection itself is read-only."""
    seed_warehouse()
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


# ---------------------------------------------------------------------------
# AST safety interceptor
# ---------------------------------------------------------------------------
SUSPICIOUS_FUNCS = {"load_extension", "readfile", "writefile", "fts3_tokenizer", "edit"}


def guard_sql(sql: str) -> dict:
    """Returns {verdict: APPROVED|BLOCKED, reason, safe_sql} — pure function of the SQL text."""
    sql = (sql or "").strip().rstrip(";").strip() + ""
    if not sql:
        return {"verdict": "BLOCKED", "reason": "empty SQL", "safe_sql": None}

    raw = sql
    try:
        statements = sqlglot.parse(raw, read="sqlite")
    except Exception as e:  # unparseable → blocked (fail closed)
        return {"verdict": "BLOCKED", "reason": f"unparseable SQL rejected (fail-closed): {e}", "safe_sql": None}

    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        return {"verdict": "BLOCKED",
                "reason": f"multi-statement input rejected ({len(statements)} statements) — classic injection vector",
                "safe_sql": None}

    tree = statements[0]

    if not isinstance(tree, exp.Select):
        verb = tree.key.upper() if hasattr(tree, "key") else type(tree).__name__.upper()
        return {"verdict": "BLOCKED", "reason": f"non-SELECT statement rejected: {verb}", "safe_sql": None}

    if tree.find(exp.Into):
        return {"verdict": "BLOCKED", "reason": "SELECT INTO rejected — writes are forbidden", "safe_sql": None}

    # nested writes anywhere in the tree (e.g. CTE hiding a DELETE)
    for node in tree.walk():
        if isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Create,
                             exp.TruncateTable, exp.Pragma, exp.Attach, exp.Detach, exp.Command)):
            return {"verdict": "BLOCKED", "reason": f"embedded write/DDL op rejected: {node.key.upper()}",
                    "safe_sql": None}

    # table allow-list (ignore CTE aliases)
    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    for tbl in tree.find_all(exp.Table):
        name = tbl.name.lower()
        if name and name not in ALLOWED_TABLES and name not in cte_names:
            return {"verdict": "BLOCKED", "reason": f"table '{name}' is outside the allow-list {sorted(ALLOWED_TABLES)}",
                    "safe_sql": None}

    # suspicious functions
    for fn in tree.find_all(exp.Anonymous):
        if (fn.name or "").lower() in SUSPICIOUS_FUNCS:
            return {"verdict": "BLOCKED", "reason": f"suspicious function rejected: {fn.name}", "safe_sql": None}
    for fn in tree.find_all(exp.Func):
        nm = (fn.sql_name() or "").lower()
        if nm in SUSPICIOUS_FUNCS:
            return {"verdict": "BLOCKED", "reason": f"suspicious function rejected: {nm}", "safe_sql": None}

    # LIMIT enforcement on the tree itself
    limit_node = tree.args.get("limit")
    if limit_node is None:
        tree = tree.limit(MAX_LIMIT)
    else:
        try:
            current = int(limit_node.expression.this)
            if current > MAX_LIMIT:
                tree = tree.limit(MAX_LIMIT)
        except Exception:
            tree = tree.limit(MAX_LIMIT)

    return {"verdict": "APPROVED", "reason": "single read-only SELECT on allow-listed tables; LIMIT enforced",
            "safe_sql": tree.sql(dialect="sqlite")}


# ---------------------------------------------------------------------------
# NL → SQL (demo pattern matcher; GROQ_API_KEY upgrades to Llama 3)
# ---------------------------------------------------------------------------
SCHEMA_DOC = {
    "products": ["id", "name", "category", "price"],
    "customers": ["id", "name", "country", "segment", "signup_date"],
    "orders": ["id", "customer_id", "order_date", "status"],
    "order_items": ["id", "order_id", "product_id", "quantity", "unit_price"],
}

DEMO_PATTERNS = [
    (r"top|best.?sell", 
     "SELECT p.name, SUM(oi.quantity) AS units_sold, ROUND(SUM(oi.quantity*oi.unit_price),2) AS revenue "
     "FROM order_items oi JOIN products p ON p.id=oi.product_id "
     "GROUP BY p.id ORDER BY revenue DESC LIMIT 10",
     {"type": "bar", "x": "name", "y": "revenue"}),
    (r"revenue by (country|geo)|country",
     "SELECT c.country, ROUND(SUM(oi.quantity*oi.unit_price),2) AS revenue "
     "FROM order_items oi JOIN orders o ON o.id=oi.order_id JOIN customers c ON c.id=o.customer_id "
     "WHERE o.status IN ('completed','shipped') GROUP BY c.country ORDER BY revenue DESC",
     {"type": "bar", "x": "country", "y": "revenue"}),
    (r"month|trend|over time",
     "SELECT substr(o.order_date,1,7) AS month, ROUND(SUM(oi.quantity*oi.unit_price),2) AS revenue "
     "FROM order_items oi JOIN orders o ON o.id=oi.order_id "
     "GROUP BY month ORDER BY month",
     {"type": "bar", "x": "month", "y": "revenue"}),
    (r"average|avg.*order",
     "SELECT ROUND(AVG(t.total),2) AS avg_order_value FROM "
     "(SELECT o.id, SUM(oi.quantity*oi.unit_price) AS total FROM orders o "
     "JOIN order_items oi ON oi.order_id=o.id GROUP BY o.id) t",
     {"type": "none", "x": None, "y": None}),
    (r"segment",
     "SELECT c.segment, COUNT(DISTINCT o.id) AS orders, ROUND(SUM(oi.quantity*oi.unit_price),2) AS revenue "
     "FROM customers c JOIN orders o ON o.customer_id=c.id JOIN order_items oi ON oi.order_id=o.id "
     "GROUP BY c.segment ORDER BY revenue DESC",
     {"type": "bar", "x": "segment", "y": "revenue"}),
    (r"refund",
     "SELECT o.id, o.order_date, c.name, c.country FROM orders o JOIN customers c ON c.id=o.customer_id "
     "WHERE o.status='refunded' ORDER BY o.order_date DESC",
     {"type": "none", "x": None, "y": None}),
    (r"categor",
     "SELECT p.category, ROUND(SUM(oi.quantity*oi.unit_price),2) AS revenue "
     "FROM order_items oi JOIN products p ON p.id=oi.product_id GROUP BY p.category ORDER BY revenue DESC",
     {"type": "bar", "x": "category", "y": "revenue"}),
]
FALLBACK_SQL = ("SELECT o.id, o.order_date, o.status, c.name AS customer FROM orders o "
                "JOIN customers c ON c.id=o.customer_id ORDER BY o.order_date DESC LIMIT 20")


def nl2sql(question: str) -> tuple[str, dict, str]:
    """Returns (sql, chart_hint, generator). Multi-provider failover: Groq -> NVIDIA NIM -> Mistral Codestral -> Demo pattern matcher."""
    schema_txt = "\n".join(f"{t}({', '.join(cols)})" for t, cols in SCHEMA_DOC.items())
    sys_prompt = (
        "You write a single SQLite SELECT statement answering the user's analytics question. "
        f"Schema:\n{schema_txt}\nReturn ONLY the SQL, no markdown formatting or backticks."
    )
    
    # Provider 1: Groq Llama 3 70B
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            body = json.dumps({
                "model": "llama3-70b-8192",
                "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": question}],
                "temperature": 0,
            }).encode()
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions", data=body,
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                out = json.load(r)
            sql = out["choices"][0]["message"]["content"].strip().strip("`").replace("sql\n", "").strip()
            return sql, {"type": "none", "x": None, "y": None}, "llama3-70b (groq)"
        except Exception:
            pass  # rate limit or network issue -> failover to next provider

    # Provider 2: NVIDIA NIM (Llama 3.1 70B Instruct on H100)
    nvidia_key = os.environ.get("NVIDIA_API_KEY")
    if nvidia_key:
        try:
            body = json.dumps({
                "model": "meta/llama-3.1-70b-instruct",
                "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": question}],
                "temperature": 0,
            }).encode()
            req = urllib.request.Request(
                "https://integrate.api.nvidia.com/v1/chat/completions", data=body,
                headers={"Authorization": f"Bearer {nvidia_key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                out = json.load(r)
            sql = out["choices"][0]["message"]["content"].strip().strip("`").replace("sql\n", "").strip()
            return sql, {"type": "none", "x": None, "y": None}, "llama-3.1-70b (nvidia nim)"
        except Exception:
            pass

    # Provider 3: Mistral Codestral
    mistral_key = os.environ.get("MISTRAL_API_KEY")
    if mistral_key:
        try:
            body = json.dumps({
                "model": "codestral-latest",
                "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": question}],
                "temperature": 0,
            }).encode()
            req = urllib.request.Request(
                "https://api.mistral.ai/v1/chat/completions", data=body,
                headers={"Authorization": f"Bearer {mistral_key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                out = json.load(r)
            sql = out["choices"][0]["message"]["content"].strip().strip("`").replace("sql\n", "").strip()
            return sql, {"type": "none", "x": None, "y": None}, "codestral (mistral ai)"
        except Exception:
            pass

    # Demo Fallback
    q = (question or "").lower()
    for pat, sql, chart in DEMO_PATTERNS:
        if re.search(pat, q):
            return sql, chart, "demo pattern-matcher"
    return FALLBACK_SQL, {"type": "none", "x": None, "y": None}, "demo fallback"



# ---------------------------------------------------------------------------
# Audit log (in-memory per instance; documented swap to Postgres)
# ---------------------------------------------------------------------------
AUDIT: list[dict] = []


def audit(entry: dict) -> None:
    entry["at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    AUDIT.insert(0, entry)
    del AUDIT[500:]


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------
def run_guarded(sql: str, source: str, question: str | None, chart: dict, generator: str) -> dict:
    t0 = time.time()
    verdict = guard_sql(sql)
    if verdict["verdict"] == "BLOCKED":
        audit({"source": source, "question": question, "sql": sql,
               "verdict": "BLOCKED", "reason": verdict["reason"]})
        return {"question": question, "sql": sql, "ast_verdict": "BLOCKED",
                "reason": verdict["reason"], "columns": [], "rows": [], "row_count": 0,
                "chart": {"type": "none", "x": None, "y": None}, "generator": generator,
                "latency_ms": round((time.time() - t0) * 1000, 1)}
    safe_sql = verdict["safe_sql"]
    conn = ro_connection()
    try:
        cur = conn.execute(safe_sql)
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = [list(r) for r in cur.fetchall()]
    except sqlite3.Error as e:
        audit({"source": source, "question": question, "sql": safe_sql,
               "verdict": "BLOCKED", "reason": f"read-only DB rejected execution: {e}"})
        return {"question": question, "sql": safe_sql, "ast_verdict": "BLOCKED",
                "reason": f"read-only DB rejected execution: {e}", "columns": [], "rows": [],
                "row_count": 0, "chart": {"type": "none", "x": None, "y": None},
                "generator": generator, "latency_ms": round((time.time() - t0) * 1000, 1)}
    finally:
        conn.close()
    audit({"source": source, "question": question, "sql": safe_sql,
           "verdict": "APPROVED", "reason": verdict["reason"], "rows": len(rows)})
    if chart.get("type") == "bar" and (chart.get("x") not in columns or chart.get("y") not in columns):
        chart = {"type": "none", "x": None, "y": None}
    return {"question": question, "sql": safe_sql, "ast_verdict": "APPROVED",
            "reason": verdict["reason"], "columns": columns, "rows": rows, "row_count": len(rows),
            "chart": chart, "generator": generator,
            "latency_ms": round((time.time() - t0) * 1000, 1)}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
class QueryIn(BaseModel):
    question: str


class SqlIn(BaseModel):
    sql: str


@app.post("/api/query")
@app.post("/query")
def api_query(body: QueryIn):
    sql, chart, generator = nl2sql(body.question)
    return run_guarded(sql, source="nl", question=body.question, chart=chart, generator=generator)


@app.post("/api/sql")
@app.post("/sql")
def api_sql(body: SqlIn):
    """Raw SQL through the identical guard — the injection demo endpoint."""
    return run_guarded(body.sql, source="raw", question=None,
                       chart={"type": "none", "x": None, "y": None}, generator="user-supplied")


@app.get("/api/schema")
def api_schema():
    return {"tables": SCHEMA_DOC, "allow_list": sorted(ALLOWED_TABLES), "max_limit": MAX_LIMIT}


@app.get("/api/audit")
def api_audit():
    return {"entries": AUDIT, "count": len(AUDIT)}


@app.get("/api/health")
def api_health():
    seed_warehouse()
    conn = ro_connection()
    n = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    return {"service": "zerotrust-sql", "status": "ok",
            "mode": "live" if os.environ.get("GROQ_API_KEY") else "demo",
            "orders_in_warehouse": n, "allow_list": sorted(ALLOWED_TABLES), "max_limit": MAX_LIMIT}


@app.get("/")
def root():
    for p in [
        os.path.join(os.path.dirname(__file__), "..", "public", "index.html"),
        os.path.join(os.path.dirname(__file__), "public", "index.html"),
        "public/index.html"
    ]:
        if os.path.exists(p):
            return HTMLResponse(open(p, "r", encoding="utf-8").read())
    return JSONResponse({"service": "zerotrust-sql", "docs": "/docs"})


@app.api_route("/{path:path}", methods=["GET", "POST"])
def fallback_router(request: Request, path: str = ""):
    if "query" in path or "query" in str(request.url.path):
        return api_query(QueryIn(question="Show me top 5 customers"))
    return JSONResponse({"service": "zerotrust-sql", "status": "ok", "path": path})
