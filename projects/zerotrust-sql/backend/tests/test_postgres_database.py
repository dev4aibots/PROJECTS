from contextlib import contextmanager

from app.database import PostgresDatabase, SandboxDatabase, build_database


class Column:
    def __init__(self, name):
        self.name = name


class FakeCursor:
    def __init__(self):
        self.statements = []
        self.description = None
        self.fetchone_value = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, statement):
        self.statements.append(statement)
        if statement.startswith("SELECT id"):
            self.description = [Column("id")]
        elif statement.startswith("SELECT current_user"):
            self.fetchone_value = ("app_login", True, True, True)

    def fetchone(self):
        return self.fetchone_value

    def fetchmany(self, limit):
        assert limit == 100
        return [(1,)]


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()

    def cursor(self):
        return self.cursor_instance

    def transaction(self):
        return _context(self)


@contextmanager
def _context(value):
    yield value


class FakePool:
    def __init__(self):
        self.connection_instance = FakeConnection()

    def connection(self):
        return _context(self.connection_instance)


def test_factory_keeps_secret_free_local_mode():
    assert isinstance(build_database(""), SandboxDatabase)


def test_postgres_executor_applies_read_only_role_and_timeouts():
    pool = FakePool()
    database = PostgresDatabase("postgresql://unused", pool=pool)

    result = database.execute("SELECT id FROM customers LIMIT 1")

    assert result["columns"] == ["id"]
    assert result["rows"] == [[1]]
    statements = pool.connection_instance.cursor_instance.statements
    assert statements[:6] == [
        "SET TRANSACTION READ ONLY",
        "SET LOCAL ROLE nl_query_ro",
        "SET LOCAL search_path TO public, pg_catalog",
        "SET LOCAL statement_timeout = '5s'",
        "SET LOCAL lock_timeout = '1s'",
        "SET LOCAL idle_in_transaction_session_timeout = '5s'",
    ]
    assert statements[-1] == "SELECT id FROM customers LIMIT 1"


def test_postgres_preflight_requires_all_capability_roles():
    pool = FakePool()
    database = PostgresDatabase("postgresql://unused", pool=pool)

    result = database.preflight()

    assert result == {
        "user": "app_login",
        "role_memberships": {
            "nl_query_ro": True,
            "nl_audit_writer": True,
            "nl_rate_limiter": True,
        },
    }
    assert "pg_has_role(current_user, 'nl_rate_limiter', 'member')" in (
        pool.connection_instance.cursor_instance.statements[-1]
    )
