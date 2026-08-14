"""Credential-gated durability/isolation proof against disposable Postgres.

Set STATEGRAPH_TEST_DATABASE_URL only to an expendable pgvector-enabled database.
The suite applies every migration and creates/deletes uniquely identified rows.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from langgraph.types import Command

DATABASE_URL = os.getenv("STATEGRAPH_TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="STATEGRAPH_TEST_DATABASE_URL is not configured",
)


def apply_migrations() -> None:
    import psycopg

    root = Path(__file__).resolve().parents[2]
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        for path in sorted((root / "migrations").glob("*.sql")):
            conn.execute(path.read_text())


def test_process_restart_rls_and_atomic_approval() -> None:
    from app.agents import build_agent_services
    from app.main import Approval, Status, Task
    from app.persistence import GraphRuntime
    from app.repository import PostgresRepository

    apply_migrations()
    user_id = uuid4()
    other_user_id = uuid4()
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial = {
        "title": "Credential-gated restart proof",
        "input": "Analyze sensitive financial risk with human approval",
        "memories": [],
        "events": [],
    }
    local_agents = lambda _: build_agent_services("local")

    process_a = GraphRuntime(
        mode="live", database_url=DATABASE_URL, agent_factory=local_agents)
    process_a.open()
    try:
        paused = process_a.graph.invoke(initial, config=config)
        assert paused["__interrupt__"]
    finally:
        process_a.close()

    process_b = GraphRuntime(
        mode="live", database_url=DATABASE_URL, agent_factory=local_agents)
    process_b.open()
    try:
        resumed = process_b.graph.invoke(
            Command(resume={"approved": True}), config=config)
        assert resumed["result"].startswith("# Credential-gated restart proof")
    finally:
        process_b.close()

    repository = PostgresRepository(DATABASE_URL)
    repository.open()
    task = Task(
        user_id=user_id,
        title="Atomic approval proof",
        input="Analyze sensitive financial risk",
        status=Status.awaiting_approval,
    )
    task.thread_id = task.run_id
    approval = Approval(
        task_run_id=task.run_id,
        reason="Human veto",
        risk_flags=["financial"],
    )
    try:
        repository.ensure_user(user_id, "owner@example.test")
        repository.ensure_user(other_user_id, "other@example.test")
        repository.save_task(task)
        repository.save_approval(approval, user_id)

        assert repository.get_task(task.id, user_id) is not None
        assert repository.get_task(task.id, other_user_id) is None
        assert repository.get_approval(approval.id, other_user_id) is None

        with ThreadPoolExecutor(max_workers=8) as executor:
            outcomes = list(executor.map(
                lambda accepted: repository.claim_decision(
                    approval.id, user_id, accepted, "integration race")[0],
                [True, False] * 4,
            ))
        assert outcomes.count("claimed") == 1
        assert outcomes.count("noop") == 7
    finally:
        repository.close()
