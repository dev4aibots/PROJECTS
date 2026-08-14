"""Execution sandbox tests: read-only enforcement, timeout, deterministic seed."""
import sqlite3

import pytest

from app.database import SandboxDatabase


@pytest.fixture(scope="module")
def db():
    return SandboxDatabase()


def test_seed_counts_deterministic(db):
    assert db.execute("SELECT COUNT(id) FROM customers LIMIT 1")["rows"][0][0] == 150
    assert db.execute("SELECT COUNT(id) FROM products LIMIT 1")["rows"][0][0] == 40
    assert db.execute("SELECT COUNT(id) FROM orders LIMIT 1")["rows"][0][0] == 800


def test_two_instances_identical(db):
    other = SandboxDatabase()
    q = ("SELECT c.name, SUM(oi.quantity * oi.unit_price) AS revenue "
         "FROM customers c JOIN orders o ON o.customer_id = c.id "
         "JOIN order_items oi ON oi.order_id = o.id "
         "WHERE o.status = 'completed' GROUP BY c.name ORDER BY revenue DESC LIMIT 3")
    assert db.execute(q)["rows"] == other.execute(q)["rows"]


def test_connection_is_read_only(db):
    with pytest.raises(sqlite3.OperationalError):
        db.execute("DELETE FROM customers")


def test_decoy_table_denied_at_execution_layer(db):
    with pytest.raises(PermissionError):
        db.execute("SELECT * FROM internal_credentials")


def test_row_cap_enforced(db):
    res = db.execute("SELECT id FROM order_items")
    assert res["row_count"] == 100  # fetchmany(MAX_ROWS)


def test_timeout_raises(db):
    heavy = ("SELECT COUNT(*) FROM order_items a, order_items b, "
             "order_items c, order_items d")
    with pytest.raises(TimeoutError):
        db.execute(heavy)


def test_result_shape(db):
    res = db.execute("SELECT name, country FROM customers LIMIT 5")
    assert res["columns"] == ["name", "country"]
    assert res["row_count"] == 5
    assert isinstance(res["duration_ms"], float)


def test_revenue_distribution_non_trivial(db):
    res = db.execute(
        "SELECT c.name, SUM(oi.quantity * oi.unit_price) AS revenue "
        "FROM customers c JOIN orders o ON o.customer_id = c.id "
        "JOIN order_items oi ON oi.order_id = o.id "
        "WHERE o.status = 'completed' GROUP BY c.name ORDER BY revenue DESC LIMIT 10")
    assert res["row_count"] == 10
    top = res["rows"][0][1]
    assert top > 1000  # non-trivial revenue distribution
