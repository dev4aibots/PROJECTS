"""Guard + NL→SQL + API tests for ZeroTrust-SQL (demo mode, no keys)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.pop("GROQ_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402
from api import index  # noqa: E402

client = TestClient(index.app)


# ---------------- guard: blocks ----------------
def test_blocks_drop():
    v = index.guard_sql("DROP TABLE orders")
    assert v["verdict"] == "BLOCKED" and "non-SELECT" in v["reason"]


def test_blocks_delete_update_insert():
    for sql in ("DELETE FROM orders", "UPDATE orders SET status='x'", "INSERT INTO orders VALUES (1,1,'x','y')"):
        assert index.guard_sql(sql)["verdict"] == "BLOCKED"


def test_blocks_multi_statement_injection():
    v = index.guard_sql("SELECT * FROM orders; DROP TABLE orders;")
    assert v["verdict"] == "BLOCKED" and "multi-statement" in v["reason"]


def test_blocks_comment_obfuscated_injection():
    v = index.guard_sql("SELECT * FROM orders /* harmless */; DELETE FROM orders --")
    assert v["verdict"] == "BLOCKED"


def test_blocks_disallowed_table():
    v = index.guard_sql("SELECT * FROM sqlite_master")
    assert v["verdict"] == "BLOCKED" and "allow-list" in v["reason"]


def test_blocks_pragma_and_attach():
    assert index.guard_sql("PRAGMA writable_schema=1")["verdict"] == "BLOCKED"
    assert index.guard_sql("ATTACH DATABASE '/tmp/x.db' AS x")["verdict"] == "BLOCKED"


def test_blocks_suspicious_function():
    v = index.guard_sql("SELECT load_extension('/tmp/evil.so')")
    assert v["verdict"] == "BLOCKED"


def test_blocks_unparseable_fail_closed():
    assert index.guard_sql("SELEKT ~~ garbage !!")["verdict"] == "BLOCKED"


# ---------------- guard: allows + LIMIT ----------------
def test_allows_valid_select():
    v = index.guard_sql("SELECT name, price FROM products WHERE price > 100 ORDER BY price DESC")
    assert v["verdict"] == "APPROVED"


def test_limit_injected_when_missing():
    v = index.guard_sql("SELECT * FROM orders")
    assert v["verdict"] == "APPROVED" and f"LIMIT {index.MAX_LIMIT}" in v["safe_sql"]


def test_limit_clamped_when_too_large():
    v = index.guard_sql("SELECT * FROM orders LIMIT 99999")
    assert v["verdict"] == "APPROVED" and f"LIMIT {index.MAX_LIMIT}" in v["safe_sql"]


def test_limit_respected_when_small():
    v = index.guard_sql("SELECT * FROM orders LIMIT 5")
    assert v["verdict"] == "APPROVED" and "LIMIT 5" in v["safe_sql"]


def test_allows_join_and_cte_on_allowed_tables():
    v = index.guard_sql(
        "WITH t AS (SELECT order_id, SUM(quantity*unit_price) rev FROM order_items GROUP BY order_id) "
        "SELECT o.id, t.rev FROM orders o JOIN t ON t.order_id=o.id LIMIT 10")
    assert v["verdict"] == "APPROVED"


# ---------------- NL→SQL demo + API ----------------
def test_demo_nl2sql_returns_rows():
    r = client.post("/api/query", json={"question": "What are the top selling products?"})
    d = r.json()
    assert r.status_code == 200 and d["ast_verdict"] == "APPROVED" and d["row_count"] > 0
    assert d["chart"]["type"] == "bar"


def test_api_sql_blocks_injection_and_audits():
    r = client.post("/api/sql", json={"sql": "SELECT * FROM orders; DROP TABLE orders;"})
    assert r.json()["ast_verdict"] == "BLOCKED"
    a = client.get("/api/audit").json()
    assert a["count"] >= 1 and any(e["verdict"] == "BLOCKED" for e in a["entries"])


def test_schema_and_health():
    s = client.get("/api/schema").json()
    assert set(s["tables"].keys()) == index.ALLOWED_TABLES
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["mode"] == "demo"
