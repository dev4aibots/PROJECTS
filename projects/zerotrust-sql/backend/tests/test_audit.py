from contextlib import contextmanager
from datetime import datetime, timezone

from app.audit import AuditLog, PostgresAuditLog, build_audit_repository


@contextmanager
def _context(value):
    yield value


class FakeCursor:
    def __init__(self):
        self.executions = []
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, statement, parameters=None):
        self.executions.append((statement, parameters))
        if "RETURNING id" in statement:
            self.rows = [(7, datetime(2026, 8, 14, tzinfo=timezone.utc))]
        elif "WHERE id" in statement:
            self.rows = []
        elif "ORDER BY id" in statement:
            self.rows = []

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()

    def cursor(self):
        return self.cursor_instance

    def transaction(self):
        return _context(self)


class FakePool:
    def __init__(self):
        self.connection_instance = FakeConnection()

    def connection(self):
        return _context(self.connection_instance)


def test_memory_audit_can_store_hashes_without_raw_text(monkeypatch):
    monkeypatch.setenv("AUDIT_HASH_KEY", "test-only-hmac-key")
    repository = AuditLog(store_raw_text=False)

    entry = repository.record(
        question="private customer question",
        generated_sql="SELECT name FROM customers",
        final_sql="SELECT name FROM customers LIMIT 100",
        validation_status="allowed",
        principal_id="key:abc",
    )

    assert entry["question"] is None
    assert entry["generated_sql"] is None
    assert entry["final_sql"] is None
    assert len(entry["question_hash"]) == 64
    assert entry["question_hash"] != entry["generated_sql_hash"]
    assert repository.get(entry["id"])["principal_id"] == "key:abc"


def test_postgres_audit_uses_separate_writer_role_and_private_defaults(monkeypatch):
    monkeypatch.setenv("AUDIT_HASH_KEY", "test-only-hmac-key")
    pool = FakePool()
    repository = PostgresAuditLog(
        "postgresql://unused",
        pool=pool,
        store_raw_text=False,
    )

    entry = repository.record(
        question="sensitive question",
        generated_sql="SELECT email FROM customers",
        final_sql="SELECT email FROM customers LIMIT 10",
        validation_status="blocked",
        checks=[{"name": "policy", "passed": False}],
        principal_id="key:def",
        request_id="request-1",
    )

    executions = pool.connection_instance.cursor_instance.executions
    assert executions[0] == ("SET LOCAL ROLE nl_audit_writer", None)
    parameters = executions[1][1]
    assert parameters["question"] is None
    assert parameters["generated_sql"] is None
    assert parameters["final_sql"] is None
    assert parameters["question_hash"]
    assert entry["id"] == 7


def test_postgres_audit_reads_use_separate_capability_role():
    pool = FakePool()
    repository = PostgresAuditLog("postgresql://unused", pool=pool)

    assert repository.recent() == []
    executions = pool.connection_instance.cursor_instance.executions
    assert executions[0] == ("SET LOCAL ROLE nl_audit_writer", None)
    assert "ORDER BY id DESC" in executions[1][0]

    executions.clear()
    assert repository.get(99) is None
    assert executions[0] == ("SET LOCAL ROLE nl_audit_writer", None)
    assert "WHERE id = %s" in executions[1][0]


def test_audit_factory_is_memory_without_database_url():
    assert isinstance(build_audit_repository(""), AuditLog)
