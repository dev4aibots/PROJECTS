from contextlib import AbstractContextManager
from uuid import UUID

from app.repository import PostgresRepository


class Context(AbstractContextManager):
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self.value

    def __exit__(self, *_):
        return None


class FakeCursor:
    def __init__(self):
        self.statements = []

    def execute(self, sql, params=None):
        self.statements.append((" ".join(sql.split()), params))

    def fetchone(self):
        return (True, True)


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def transaction(self):
        return Context(self)

    def cursor(self):
        return Context(self._cursor)


class FakePool:
    def __init__(self):
        self.cursor = FakeCursor()
        self.connection_value = FakeConnection(self.cursor)

    def connection(self):
        return Context(self.connection_value)


def test_projection_session_assumes_role_and_binds_verified_subject():
    pool = FakePool()
    repository = PostgresRepository("postgresql://unused", pool=pool)
    user_id = UUID("00000000-0000-0000-0000-000000000099")

    repository.ensure_user(user_id, "owner@example.test")

    statements = pool.cursor.statements
    assert statements[0] == ("SET LOCAL ROLE stategraph_api", None)
    assert statements[1] == (
        "SELECT set_config('app.current_user_id', %s, true)",
        (str(user_id),),
    )
    assert statements[2][0].startswith("INSERT INTO demo_users")
    assert statements[2][1] == (user_id, "owner")


def test_readiness_requires_role_membership_and_table_privilege():
    repository = PostgresRepository("postgresql://unused", pool=FakePool())
    assert repository.readiness() == {
        "ready": True,
        "persistence": "postgres-projections",
    }
