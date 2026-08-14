"""Deterministic seeded analytics database and read-only execution sandbox.

Local mode uses an in-memory SQLite database seeded with a fixed random seed so
every demo run has identical, non-trivial data. Hosted mode targets the
Postgres role created in ``migrations/001_zerotrust.sql`` (``nl_query_ro``,
SELECT on only the four allowlisted tables, statement_timeout=5s) — the same
defense-in-depth story, executed by the platform instead of this process.
"""
from __future__ import annotations

import os
import random
import sqlite3
import threading
import time
from contextlib import nullcontext
from typing import Any, Protocol

import sqlglot

from .allowlist import MAX_ROWS, STATEMENT_TIMEOUT_SECONDS


class QueryDatabase(Protocol):
    """Execution boundary used by the API after deterministic validation."""

    mode: str

    def execute(self, sql: str) -> dict[str, Any]: ...


SEED = 42
COUNTRIES = ["US", "DE", "GB", "FR", "BR", "JP", "IN", "CA", "AU", "NL"]
CITIES = {
    "US": ["New York", "Austin", "Seattle"], "DE": ["Berlin", "Munich"],
    "GB": ["London", "Leeds"], "FR": ["Paris", "Lyon"], "BR": ["Sao Paulo"],
    "JP": ["Tokyo", "Osaka"], "IN": ["Bengaluru", "Pune"], "CA": ["Toronto"],
    "AU": ["Sydney"], "NL": ["Amsterdam"],
}
FIRST = ["Ava", "Liam", "Noah", "Mia", "Zoe", "Kai", "Ivy", "Leo", "Ana", "Max",
         "Nina", "Omar", "Lena", "Hugo", "Sara"]
LAST = ["Reed", "Chen", "Silva", "Kumar", "Novak", "Sato", "Meyer", "Costa",
        "Khan", "Olsen", "Braun", "Diaz", "Ito", "Wolf", "Nash"]
CATEGORIES = ["Electronics", "Home", "Sports", "Books", "Toys", "Garden", "Office", "Beauty"]
STATUSES = ["completed", "completed", "completed", "shipped", "pending", "cancelled"]
SEGMENTS = ["consumer", "consumer", "smb", "enterprise"]


def _seed_rows(rng: random.Random):
    customers, products, orders, items = [], [], [], []
    for i in range(1, 151):
        country = rng.choice(COUNTRIES)
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        customers.append((
            i, name, f"user{i}@example.com", country, rng.choice(CITIES[country]),
            f"20{rng.randint(23, 24)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
            rng.choice(SEGMENTS),
        ))
    for i in range(1, 41):
        price = round(rng.uniform(8, 480), 2)
        products.append((
            i, f"{rng.choice(CATEGORIES)} Item {i}", rng.choice(CATEGORIES),
            price, round(price * rng.uniform(0.35, 0.8), 2), rng.random() > 0.1,
        ))
    item_id = 1
    for i in range(1, 801):
        cust = rng.randint(1, 150)
        month = rng.randint(1, 24)
        year, mon = (2023 + (month - 1) // 12), ((month - 1) % 12) + 1
        orders.append((
            i, cust, f"{year}-{mon:02d}-{rng.randint(1, 28):02d}",
            rng.choice(STATUSES), customers[cust - 1][3],
        ))
        for _ in range(rng.randint(1, 4)):
            pid = rng.randint(1, 40)
            items.append((item_id, i, pid, rng.randint(1, 5), products[pid - 1][3]))
            item_id += 1
    return customers, products, orders, items


class SandboxDatabase:
    """Read-only executor over the seeded database.

    Defense-in-depth beyond the validator:
    - the connection used for queries is opened in ``query_only`` mode so even
      a validator bug cannot write (mirrors the ``nl_query_ro`` role);
    - a progress-handler based timeout mirrors ``statement_timeout``;
    - the decoy table exists but querying it is denied at this layer too.
    """

    DENIED_TABLES = {"internal_credentials"}
    mode = "seeded-sqlite"

    def __init__(self) -> None:
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._lock = threading.Lock()
        self._build()

    def _build(self) -> None:
        c = self._conn
        c.executescript(
            """
            CREATE TABLE customers(id INTEGER PRIMARY KEY, name TEXT, email TEXT,
              country TEXT, city TEXT, signup_date TEXT, segment TEXT);
            CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, category TEXT,
              unit_price REAL, cost REAL, active INTEGER);
            CREATE TABLE orders(id INTEGER PRIMARY KEY, customer_id INTEGER,
              order_date TEXT, status TEXT, shipping_country TEXT);
            CREATE TABLE order_items(id INTEGER PRIMARY KEY, order_id INTEGER,
              product_id INTEGER, quantity INTEGER, unit_price REAL);
            CREATE TABLE internal_credentials(id INTEGER PRIMARY KEY,
              service TEXT, secret TEXT);
            """
        )
        rng = random.Random(SEED)
        customers, products, orders, items = _seed_rows(rng)
        c.executemany("INSERT INTO customers VALUES(?,?,?,?,?,?,?)", customers)
        c.executemany("INSERT INTO products VALUES(?,?,?,?,?,?)", products)
        c.executemany("INSERT INTO orders VALUES(?,?,?,?,?)", orders)
        c.executemany("INSERT INTO order_items VALUES(?,?,?,?,?)", items)
        c.execute("INSERT INTO internal_credentials VALUES(1,'payments-api','fake-secret-do-not-read')")
        c.commit()
        c.execute("PRAGMA query_only = ON")  # read-only from here on

    def execute(self, sql: str) -> dict:
        """Run validated SQL read-only with a timeout; returns the result shape."""
        lowered = sql.lower()
        for denied in self.DENIED_TABLES:
            if denied in lowered:
                raise PermissionError(f"role nl_query_ro has no grant on {denied}")
        # Local-mode dialect shim: the validated SQL is canonical Postgres;
        # transpile it to SQLite via sqlglot (hosted mode executes it as-is).
        try:
            sql = sqlglot.transpile(sql, read="postgres", write="sqlite")[0]
        except sqlglot.errors.SqlglotError:
            pass  # already validated; fall through to the original text
        deadline = time.monotonic() + STATEMENT_TIMEOUT_SECONDS
        self._conn.set_progress_handler(
            lambda: 1 if time.monotonic() > deadline else 0, 10_000)
        started = time.perf_counter()
        try:
            with self._lock:
                cur = self._conn.execute(sql)
                columns = [d[0] for d in cur.description] if cur.description else []
                rows = cur.fetchmany(MAX_ROWS)
        except sqlite3.OperationalError as err:
            if "interrupted" in str(err).lower():
                raise TimeoutError(
                    f"query exceeded the {STATEMENT_TIMEOUT_SECONDS}s time limit") from err
            raise
        finally:
            self._conn.set_progress_handler(None, 0)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "columns": columns,
            "rows": [list(r) for r in rows],
            "row_count": len(rows),
            "duration_ms": duration_ms,
        }


class PostgresDatabase:
    """Restricted Postgres executor selected when ``DATABASE_URL`` is set.

    The supplied login must be a member of ``nl_query_ro``. Every execution
    starts a read-only transaction, assumes that role locally, applies tight
    timeouts, fixes the search path, and caps rows again at the driver layer.
    The validator remains the first wall; database privileges are the second.
    """

    mode = "restricted-postgres"

    def __init__(self, database_url: str, pool: Any | None = None) -> None:
        if not database_url:
            raise ValueError("DATABASE_URL is required for Postgres mode")
        if pool is None:
            try:
                from psycopg_pool import ConnectionPool
            except ImportError as exc:  # pragma: no cover - deployment config
                raise RuntimeError(
                    "Postgres mode requires psycopg[binary,pool]") from exc
            pool = ConnectionPool(
                conninfo=database_url,
                min_size=0,
                max_size=int(os.getenv("DATABASE_POOL_MAX_SIZE", "3")),
                timeout=float(os.getenv("DATABASE_POOL_TIMEOUT_SECONDS", "5")),
                open=False,
            )
            pool.open(wait=True)
        self._pool = pool

    def execute(self, sql: str) -> dict[str, Any]:
        started = time.perf_counter()
        connection_context = self._pool.connection()
        with connection_context as conn:
            transaction = conn.transaction() if hasattr(conn, "transaction") else nullcontext()
            with transaction:
                with conn.cursor() as cur:
                    cur.execute("SET TRANSACTION READ ONLY")
                    cur.execute("SET LOCAL ROLE nl_query_ro")
                    cur.execute("SET LOCAL search_path TO public, pg_catalog")
                    cur.execute("SET LOCAL statement_timeout = '5s'")
                    cur.execute("SET LOCAL lock_timeout = '1s'")
                    cur.execute("SET LOCAL idle_in_transaction_session_timeout = '5s'")
                    try:
                        cur.execute(sql)
                        columns = [column.name for column in cur.description] if cur.description else []
                        rows = cur.fetchmany(MAX_ROWS)
                    except Exception as exc:
                        sqlstate = getattr(exc, "sqlstate", None)
                        if sqlstate == "57014":
                            raise TimeoutError(
                                f"query exceeded the {STATEMENT_TIMEOUT_SECONDS}s time limit") from exc
                        if sqlstate == "42501":
                            raise PermissionError("restricted database role denied access") from exc
                        raise
        return {
            "columns": columns,
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    def preflight(self) -> dict[str, Any]:
        """Verify every least-privilege capability required by live mode."""
        required_roles = ("nl_query_ro", "nl_audit_writer", "nl_rate_limiter")
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT current_user, "
                    "pg_has_role(current_user, 'nl_query_ro', 'member'), "
                    "pg_has_role(current_user, 'nl_audit_writer', 'member'), "
                    "pg_has_role(current_user, 'nl_rate_limiter', 'member')"
                )
                user, *memberships = cur.fetchone()
        missing = [
            role for role, is_member in zip(required_roles, memberships, strict=True)
            if not is_member
        ]
        if missing:
            raise PermissionError(
                "DATABASE_URL user lacks required role membership: " + ", ".join(missing)
            )
        return {
            "user": user,
            "role_memberships": {role: True for role in required_roles},
        }


def build_database(database_url: str | None = None) -> QueryDatabase:
    """Select live Postgres only through explicit configuration."""
    url = database_url if database_url is not None else os.getenv("DATABASE_URL", "")
    return PostgresDatabase(url) if url else SandboxDatabase()
