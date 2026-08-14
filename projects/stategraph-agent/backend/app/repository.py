"""Projection repositories for tasks, approvals, events, users, and memories.

LangGraph owns execution checkpoints. This module owns queryable API projections.
The live implementation uses database compare-and-set for approval decisions so
multiple API workers cannot resume the same checkpoint twice.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Protocol
from uuid import UUID


DEMO_USERS = {
    UUID("00000000-0000-0000-0000-000000000001"): "Avery",
    UUID("00000000-0000-0000-0000-000000000002"): "Blake",
}


class ProjectionRepository(Protocol):
    mode: str

    def open(self) -> None: ...
    def close(self) -> None: ...
    def readiness(self) -> dict[str, str | bool]: ...
    def list_users(self) -> dict[UUID, str]: ...
    def ensure_user(self, user_id: UUID, email: str | None = None) -> None: ...
    def save_task(self, task: Any) -> None: ...
    def get_task(self, task_id: UUID, user_id: UUID) -> Any | None: ...
    def get_task_by_run(self, run_id: UUID, user_id: UUID) -> Any | None: ...
    def list_tasks(self, user_id: UUID) -> list[Any]: ...
    def add_events(self, task_id: UUID, user_id: UUID, events: list[Any]) -> None: ...
    def list_events(self, task_id: UUID, user_id: UUID) -> list[Any]: ...
    def save_approval(self, approval: Any, user_id: UUID) -> None: ...
    def get_approval(self, approval_id: UUID, user_id: UUID) -> Any | None: ...
    def get_approval_for_run(self, run_id: UUID, user_id: UUID) -> Any | None: ...
    def claim_decision(self, approval_id: UUID, user_id: UUID, accepted: bool, note: str) -> tuple[str, Any | None, Any | None]: ...
    def save_memory(self, memory: Any) -> None: ...
    def list_memories(self, user_id: UUID, limit: int | None = None) -> list[Any]: ...
    def memory_exists_for_task(self, task_id: UUID, user_id: UUID) -> bool: ...
    def delete_memory(self, memory_id: UUID, user_id: UUID) -> bool: ...


class InMemoryRepository:
    """Deterministic local repository with the same atomic decision contract."""

    mode = "memory-projections"

    def __init__(self) -> None:
        self.users = dict(DEMO_USERS)
        self.tasks: dict[UUID, Any] = {}
        self.events: dict[UUID, list[Any]] = {}
        self.approvals: dict[UUID, Any] = {}
        self.memories: dict[UUID, Any] = {}
        self.lock = Lock()

    def open(self) -> None:
        return None

    def close(self) -> None:
        return None

    def readiness(self) -> dict[str, str | bool]:
        return {"ready": True, "persistence": self.mode}

    def reset(self) -> None:
        self.tasks.clear(); self.events.clear(); self.approvals.clear(); self.memories.clear()

    def list_users(self) -> dict[UUID, str]:
        return dict(self.users)

    def ensure_user(self, user_id: UUID, email: str | None = None) -> None:
        self.users.setdefault(user_id, email or "Portfolio user")

    def save_task(self, task: Any) -> None:
        self.tasks[task.id] = task.model_copy(deep=True)

    def get_task(self, task_id: UUID, user_id: UUID) -> Any | None:
        task = self.tasks.get(task_id)
        return task.model_copy(deep=True) if task and task.user_id == user_id else None

    def get_task_by_run(self, run_id: UUID, user_id: UUID) -> Any | None:
        task = next((item for item in self.tasks.values()
                     if item.run_id == run_id and item.user_id == user_id), None)
        return task.model_copy(deep=True) if task else None

    def list_tasks(self, user_id: UUID) -> list[Any]:
        return [item.model_copy(deep=True) for item in self.tasks.values() if item.user_id == user_id]

    def add_events(self, task_id: UUID, user_id: UUID, events: list[Any]) -> None:
        if self.get_task(task_id, user_id) is None:
            return
        target = self.events.setdefault(task_id, [])
        known = {item.id for item in target}
        target.extend(item.model_copy(deep=True) for item in events if item.id not in known)

    def list_events(self, task_id: UUID, user_id: UUID) -> list[Any]:
        if self.get_task(task_id, user_id) is None:
            return []
        return [item.model_copy(deep=True) for item in self.events.get(task_id, [])]

    def save_approval(self, approval: Any, user_id: UUID) -> None:
        if self.get_task_by_run(approval.task_run_id, user_id) is not None:
            self.approvals[approval.id] = approval.model_copy(deep=True)

    def get_approval(self, approval_id: UUID, user_id: UUID) -> Any | None:
        item = self.approvals.get(approval_id)
        if not item or self.get_task_by_run(item.task_run_id, user_id) is None:
            return None
        return item.model_copy(deep=True)

    def get_approval_for_run(self, run_id: UUID, user_id: UUID) -> Any | None:
        if self.get_task_by_run(run_id, user_id) is None:
            return None
        item = next((value for value in self.approvals.values() if value.task_run_id == run_id), None)
        return item.model_copy(deep=True) if item else None

    def claim_decision(self, approval_id: UUID, user_id: UUID, accepted: bool, note: str):
        from .main import Status, now
        with self.lock:
            approval = self.approvals.get(approval_id)
            if not approval:
                return "missing", None, None
            task = next(item for item in self.tasks.values() if item.run_id == approval.task_run_id)
            if task.user_id != user_id:
                return "missing", None, None
            if approval.status != "pending" or task.status != Status.awaiting_approval:
                return "noop", approval.model_copy(deep=True), None
            approval.status = "approved" if accepted else "rejected"
            approval.resolved_at = now()
            approval.resolution_note = note
            task.status = Status.in_progress
            task.updated_at = now()
            return "claimed", approval.model_copy(deep=True), task.model_copy(deep=True)

    def save_memory(self, memory: Any) -> None:
        self.memories[memory.id] = memory.model_copy(deep=True)

    def list_memories(self, user_id: UUID, limit: int | None = None) -> list[Any]:
        current = datetime.now(timezone.utc)
        values = [
            item.model_copy(deep=True) for item in self.memories.values()
            if item.user_id == user_id and item.expires_at > current
        ]
        return values[:limit] if limit is not None else values

    def memory_exists_for_task(self, task_id: UUID, user_id: UUID) -> bool:
        return any(item.source_task_id == task_id and item.user_id == user_id
                   for item in self.memories.values())

    def delete_memory(self, memory_id: UUID, user_id: UUID) -> bool:
        item = self.memories.get(memory_id)
        if not item or item.user_id != user_id:
            return False
        del self.memories[memory_id]
        return True


class PostgresRepository:
    """Durable projection repository for horizontally scaled API workers."""

    mode = "postgres-projections"

    def __init__(self, database_url: str, pool: Any | None = None) -> None:
        if not database_url:
            raise RuntimeError("DATABASE_URL is required for Postgres projections")
        self.database_url = database_url
        self.pool = pool
        self._owns_pool = pool is None

    def open(self) -> None:
        if self.pool is not None:
            return
        from psycopg_pool import ConnectionPool
        self.pool = ConnectionPool(
            conninfo=self.database_url,
            min_size=0,
            max_size=int(os.getenv("DATABASE_POOL_MAX_SIZE", "5")),
            timeout=float(os.getenv("DATABASE_POOL_TIMEOUT_SECONDS", "5")),
            open=True,
        )

    def close(self) -> None:
        if self._owns_pool and self.pool is not None:
            self.pool.close()
            self.pool = None

    @contextmanager
    def _session(self, user_id: UUID):
        """Assume the least-privilege role and bind RLS identity locally."""
        if self.pool is None:
            raise RuntimeError("Postgres projection pool is not open")
        with self.pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
            cur.execute("SET LOCAL ROLE stategraph_api")
            cur.execute("SELECT set_config('app.current_user_id', %s, true)", (str(user_id),))
            yield cur

    def readiness(self) -> dict[str, str | bool]:
        if self.pool is None:
            return {"ready": False, "persistence": self.mode}
        try:
            with self.pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """SELECT pg_has_role(current_user, 'stategraph_api', 'member'),
                              has_table_privilege('stategraph_api', 'tasks', 'SELECT')""")
                role_member, table_access = cur.fetchone()
                if not role_member or not table_access:
                    return {"ready": False, "persistence": self.mode}
            return {"ready": True, "persistence": self.mode}
        except Exception:
            return {"ready": False, "persistence": self.mode}

    def list_users(self) -> dict[UUID, str]:
        raise RuntimeError("list_users is unavailable without a verified principal")

    def ensure_user(self, user_id: UUID, email: str | None = None) -> None:
        display_name = (email or "Portfolio user").split("@", 1)[0][:80]
        with self._session(user_id) as cur:
            cur.execute(
                """INSERT INTO demo_users(id,name) VALUES(%s,%s)
                   ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name""",
                (user_id, display_name),
            )

    def save_task(self, task: Any) -> None:
        completed_at = task.updated_at if task.status.value in {"completed", "failed", "rejected", "canceled"} else None
        with self._session(task.user_id) as cur:
            cur.execute(
                """INSERT INTO tasks(id,user_id,title,input,status,result,error,remember,created_at,updated_at)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(id) DO UPDATE SET status=EXCLUDED.status,result=EXCLUDED.result,
                     error=EXCLUDED.error,remember=EXCLUDED.remember,updated_at=EXCLUDED.updated_at""",
                (task.id, task.user_id, task.title, task.input, task.status.value,
                 task.result, task.error, task.remember, task.created_at, task.updated_at),
            )
            cur.execute(
                """INSERT INTO task_runs(id,task_id,thread_id,current_node,status,error,started_at,completed_at)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(id) DO UPDATE SET current_node=EXCLUDED.current_node,
                     status=EXCLUDED.status,error=EXCLUDED.error,completed_at=EXCLUDED.completed_at""",
                (task.run_id, task.id, task.thread_id, task.current_node, task.status.value,
                 task.error, task.created_at, completed_at),
            )

    @staticmethod
    def _task(row: tuple) -> Any:
        from .main import Task
        return Task(id=row[0], run_id=row[1], thread_id=row[2], user_id=row[3], title=row[4],
                    input=row[5], status=row[6], current_node=row[7], result=row[8], error=row[9],
                    remember=row[10], created_at=row[11], updated_at=row[12])

    _TASK_SELECT = """SELECT t.id,r.id,r.thread_id,t.user_id,t.title,t.input,t.status,
        r.current_node,t.result,t.error,t.remember,t.created_at,t.updated_at
        FROM tasks t JOIN task_runs r ON r.task_id=t.id"""

    def get_task(self, task_id: UUID, user_id: UUID) -> Any | None:
        with self._session(user_id) as cur:
            cur.execute(self._TASK_SELECT + " WHERE t.id=%s", (task_id,))
            row = cur.fetchone()
            return self._task(row) if row else None

    def get_task_by_run(self, run_id: UUID, user_id: UUID) -> Any | None:
        with self._session(user_id) as cur:
            cur.execute(self._TASK_SELECT + " WHERE r.id=%s", (run_id,))
            row = cur.fetchone()
            return self._task(row) if row else None

    def list_tasks(self, user_id: UUID) -> list[Any]:
        with self._session(user_id) as cur:
            cur.execute(self._TASK_SELECT + " WHERE t.user_id=%s ORDER BY t.created_at DESC", (user_id,))
            return [self._task(row) for row in cur.fetchall()]

    def add_events(self, task_id: UUID, user_id: UUID, events: list[Any]) -> None:
        if not events:
            return
        with self._session(user_id) as cur:
            for event in events:
                cur.execute(
                    """INSERT INTO agent_events(id,task_run_id,agent,event_type,input_summary,
                       output_summary,duration_ms,created_at) VALUES(%s,%s,%s,'node_completed',%s,%s,%s,%s)
                       ON CONFLICT(id) DO NOTHING""",
                    (event.id, event.task_run_id, event.agent, event.input_summary,
                     event.output_summary, event.duration_ms, event.created_at),
                )

    @staticmethod
    def _event(row: tuple) -> Any:
        from .main import Event
        return Event(id=row[0], task_run_id=row[1], agent=row[2], input_summary=row[3],
                     output_summary=row[4], duration_ms=row[5], created_at=row[6])

    def list_events(self, task_id: UUID, user_id: UUID) -> list[Any]:
        with self._session(user_id) as cur:
            cur.execute("""SELECT e.id,e.task_run_id,e.agent,e.input_summary,e.output_summary,
                        e.duration_ms,e.created_at FROM agent_events e JOIN task_runs r
                        ON r.id=e.task_run_id WHERE r.task_id=%s ORDER BY e.created_at""", (task_id,))
            return [self._event(row) for row in cur.fetchall()]

    def save_approval(self, approval: Any, user_id: UUID) -> None:
        with self._session(user_id) as cur:
            cur.execute(
                """INSERT INTO approvals(id,task_run_id,reason,risk_flags,status,requested_at,resolved_at,resolution_note)
                   VALUES(%s,%s,%s,%s::jsonb,%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING""",
                (approval.id, approval.task_run_id, approval.reason,
                 __import__('json').dumps(approval.risk_flags), approval.status,
                 approval.requested_at, approval.resolved_at, approval.resolution_note),
            )

    @staticmethod
    def _approval(row: tuple) -> Any:
        from .main import Approval
        return Approval(id=row[0], task_run_id=row[1], reason=row[2], risk_flags=row[3],
                        status=row[4], requested_at=row[5], resolved_at=row[6], resolution_note=row[7] or "")

    _APPROVAL_SELECT = "SELECT id,task_run_id,reason,risk_flags,status,requested_at,resolved_at,resolution_note FROM approvals"

    def get_approval(self, approval_id: UUID, user_id: UUID) -> Any | None:
        with self._session(user_id) as cur:
            cur.execute(self._APPROVAL_SELECT + " WHERE id=%s", (approval_id,))
            row = cur.fetchone()
            return self._approval(row) if row else None

    def get_approval_for_run(self, run_id: UUID, user_id: UUID) -> Any | None:
        with self._session(user_id) as cur:
            cur.execute(self._APPROVAL_SELECT + " WHERE task_run_id=%s ORDER BY requested_at DESC LIMIT 1", (run_id,))
            row = cur.fetchone()
            return self._approval(row) if row else None

    def claim_decision(self, approval_id: UUID, user_id: UUID, accepted: bool, note: str):
        status = "approved" if accepted else "rejected"
        with self._session(user_id) as cur:
            cur.execute(
                """UPDATE approvals a SET status=%s,resolved_at=now(),resolution_note=%s
                   FROM task_runs r JOIN tasks t ON t.id=r.task_id
                   WHERE a.id=%s AND a.status='pending' AND r.id=a.task_run_id
                     AND t.user_id=%s AND t.status='awaiting_approval'
                   RETURNING a.id,a.task_run_id,a.reason,a.risk_flags,a.status,
                     a.requested_at,a.resolved_at,a.resolution_note""",
                (status, note, approval_id, user_id),
            )
            row = cur.fetchone()
            if row:
                approval = self._approval(row)
                cur.execute("UPDATE task_runs SET status='in_progress' WHERE id=%s", (approval.task_run_id,))
                cur.execute("UPDATE tasks SET status='in_progress',updated_at=now() WHERE id=(SELECT task_id FROM task_runs WHERE id=%s)", (approval.task_run_id,))
                cur.execute(self._TASK_SELECT + " WHERE r.id=%s", (approval.task_run_id,))
                return "claimed", approval, self._task(cur.fetchone())
            cur.execute(
                """SELECT a.id,a.task_run_id,a.reason,a.risk_flags,a.status,a.requested_at,
                          a.resolved_at,a.resolution_note
                   FROM approvals a JOIN task_runs r ON r.id=a.task_run_id
                   JOIN tasks t ON t.id=r.task_id WHERE a.id=%s AND t.user_id=%s""",
                (approval_id, user_id),
            )
            existing = cur.fetchone()
            return ("noop", self._approval(existing), None) if existing else ("missing", None, None)

    def save_memory(self, memory: Any) -> None:
        with self._session(memory.user_id) as cur:
            cur.execute(
                """INSERT INTO memories(id,user_id,memory_type,content,source_task_id,created_at,expires_at)
                   VALUES(%s,%s,'preference',%s,%s,%s,%s) ON CONFLICT(id) DO NOTHING""",
                (memory.id, memory.user_id, memory.content, memory.source_task_id,
                 memory.created_at, memory.expires_at),
            )

    @staticmethod
    def _memory(row: tuple) -> Any:
        from .main import Memory
        return Memory(id=row[0], user_id=row[1], content=row[2], source_task_id=row[3],
                      created_at=row[4], expires_at=row[5])

    def list_memories(self, user_id: UUID, limit: int | None = None) -> list[Any]:
        sql = """SELECT id,user_id,content,source_task_id,created_at,expires_at
                 FROM memories WHERE user_id=%s AND expires_at>now() ORDER BY created_at DESC"""
        params: tuple[Any, ...] = (user_id,)
        if limit is not None:
            sql += " LIMIT %s"; params += (limit,)
        with self._session(user_id) as cur:
            cur.execute(sql, params)
            return [self._memory(row) for row in cur.fetchall()]

    def memory_exists_for_task(self, task_id: UUID, user_id: UUID) -> bool:
        with self._session(user_id) as cur:
            cur.execute("SELECT EXISTS(SELECT 1 FROM memories WHERE source_task_id=%s)", (task_id,))
            return bool(cur.fetchone()[0])

    def delete_memory(self, memory_id: UUID, user_id: UUID) -> bool:
        with self._session(user_id) as cur:
            cur.execute("DELETE FROM memories WHERE id=%s AND user_id=%s", (memory_id, user_id))
            return cur.rowcount == 1


def build_repository(mode: str | None = None, database_url: str | None = None) -> ProjectionRepository:
    selected = (mode or os.getenv("APP_MODE", "local")).strip().lower()
    if selected == "local":
        return InMemoryRepository()
    if selected == "live":
        return PostgresRepository(database_url if database_url is not None else os.getenv("DATABASE_URL", ""))
    raise RuntimeError("APP_MODE must be local or live")
