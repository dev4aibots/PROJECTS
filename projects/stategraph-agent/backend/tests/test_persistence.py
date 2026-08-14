from concurrent.futures import ThreadPoolExecutor
from contextlib import AbstractContextManager
from uuid import UUID

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.graph import build_graph
from app.main import Approval, Status, Task
from app.persistence import GraphRuntime
from app.repository import InMemoryRepository


class FakeContext(AbstractContextManager):
    def __init__(self, saver):
        self.saver = saver
        self.closed = False

    def __enter__(self):
        return self.saver

    def __exit__(self, *_):
        self.closed = True


class SetupSaver(InMemorySaver):
    def __init__(self):
        super().__init__()
        self.setup_called = False

    def setup(self):
        self.setup_called = True


def test_live_runtime_runs_setup_and_closes_context():
    saver = SetupSaver()
    context = FakeContext(saver)
    runtime = GraphRuntime(
        mode="live",
        database_url="postgresql://example.invalid/db",
        postgres_factory=lambda _: context,
        agent_factory=lambda _: __import__("app.agents", fromlist=["build_agent_services"]).build_agent_services("local"),
    )

    runtime.open()
    assert saver.setup_called is True
    assert runtime.readiness() == {
        "ready": True,
        "mode": "live",
        "persistence": "postgres-checkpointer",
    }
    runtime.close()
    assert context.closed is True


def test_live_runtime_requires_database_url():
    try:
        GraphRuntime(mode="live", database_url="")
    except RuntimeError as exc:
        assert "DATABASE_URL" in str(exc)
    else:
        raise AssertionError("live mode accepted an empty database URL")


def test_reconstructed_graph_resumes_from_shared_checkpoint():
    saver = InMemorySaver()
    config = {"configurable": {"thread_id": "restart-proof"}}
    initial = {
        "title": "Risk review",
        "input": "Analyze sensitive financial risk",
        "memories": [],
        "events": [],
    }

    paused = build_graph(saver).invoke(initial, config=config)
    assert paused["__interrupt__"]

    resumed = build_graph(saver).invoke(
        Command(resume={"approved": True}), config=config)
    assert resumed["result"].startswith("# Risk review")
    assert [event["agent"] for event in resumed["events"]] == [
        "research", "analyst", "reviewer", "writer"]


def test_projection_repository_allows_only_one_concurrent_decision():
    repository = InMemoryRepository()
    user_id = UUID("00000000-0000-0000-0000-000000000001")
    task = Task(user_id=user_id, title="Risk review", input="Analyze sensitive financial risk")
    task.thread_id = task.run_id
    task.status = Status.awaiting_approval
    approval = Approval(task_run_id=task.run_id, reason="Human veto", risk_flags=["risk"])
    repository.save_task(task)
    repository.save_approval(approval, user_id)

    with ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(
            lambda accepted: repository.claim_decision(
                approval.id, user_id, accepted, "race")[0],
            [True, False] * 4,
        ))

    assert outcomes.count("claimed") == 1
    assert outcomes.count("noop") == 7
    assert repository.get_approval(approval.id, user_id).status in {"approved", "rejected"}
