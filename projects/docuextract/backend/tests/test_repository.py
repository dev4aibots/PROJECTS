from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from uuid import UUID

from app.repository import PostgresRepository, Repository, build_repository

OWNER = UUID("00000000-0000-0000-0000-000000000001")
DOC = "10000000-0000-0000-0000-000000000001"


class FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, query, params=None):
        self.calls.append((" ".join(query.split()), params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def fetchall(self):
        rows, self.rows = self.rows, []
        return rows


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def transaction(self):
        return nullcontext()

    def cursor(self):
        return self._cursor


class FakePool:
    def __init__(self, cursor):
        self._connection = FakeConnection(cursor)

    def connection(self):
        return self._connection


ROW = (
    DOC,
    OWNER,
    "invoice.pdf",
    "application/pdf",
    128,
    f"{OWNER}/{DOC}/source.pdf",
    "uploaded",
    None,
    {},
    0,
)


def test_postgres_session_assumes_restricted_role_and_owner_identity():
    cursor = FakeCursor([ROW])
    repository = PostgresRepository("postgresql://example", pool=FakePool(cursor))
    document = repository.get(DOC, OWNER)
    assert document["id"] == DOC
    assert cursor.calls[0][0] == "SET LOCAL ROLE docuextract_api"
    assert "set_config('app.current_user_id'" in cursor.calls[1][0]
    assert cursor.calls[1][1] == (str(OWNER),)
    assert "WHERE id=%s" in cursor.calls[2][0]


def test_postgres_claim_reports_existing_processing_lease():
    cursor = FakeCursor([None, ("processing",)])
    repository = PostgresRepository("postgresql://example", pool=FakePool(cursor))
    assert repository.claim_processing(DOC, OWNER) == "busy"
    assert "status IN ('uploaded','failed_extraction')" in cursor.calls[2][0]


def test_memory_processing_claim_has_exactly_one_winner():
    repository = Repository()
    repository.create(
        "invoice.pdf",
        "application/pdf",
        10,
        OWNER,
        f"{OWNER}/{DOC}/source.pdf",
        DOC,
    )
    with ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(lambda _: repository.claim_processing(DOC, OWNER), range(8)))
    assert outcomes.count("claimed") == 1
    assert outcomes.count("busy") == 7


def test_completed_memory_process_is_idempotent():
    repository = Repository()
    repository.create("invoice.pdf", "application/pdf", 10, OWNER, "private/path", DOC)
    assert repository.claim_processing(DOC, OWNER) == "claimed"
    repository.update(DOC, OWNER, status="verified", invoice={"invoice_number": "I-1"})
    assert repository.claim_processing(DOC, OWNER) == "complete"


def test_local_factory_is_explicit():
    repository = build_repository("local")
    assert repository.mode == "memory"
    assert repository.readiness()["ready"] is True
