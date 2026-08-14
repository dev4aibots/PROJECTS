"""Checkpoint runtime selection for local tests and durable deployments."""
from __future__ import annotations

import os
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Callable

from langgraph.checkpoint.memory import InMemorySaver

from .agents import build_agent_services
from .graph import build_graph


@dataclass
class GraphRuntime:
    """Own the checkpointer lifecycle and currently compiled graph.

    Local mode is intentionally explicit and process-local. Live mode opens a
    PostgresSaver for the whole FastAPI lifespan and runs its idempotent schema
    setup before accepting traffic.
    """

    mode: str = "local"
    database_url: str = ""
    postgres_factory: Callable[[str], AbstractContextManager] | None = None
    agent_factory: Callable[[str], Any] = build_agent_services

    def __post_init__(self) -> None:
        if self.mode not in {"local", "live"}:
            raise RuntimeError("APP_MODE must be local or live")
        if self.mode == "live" and not self.database_url:
            raise RuntimeError("DATABASE_URL is required when APP_MODE=live")
        self._context: AbstractContextManager | None = None
        self.checkpointer: Any = InMemorySaver()
        self.graph = build_graph(self.checkpointer, self.agent_factory("local"))
        self.persistence = "memory-checkpointer"

    @classmethod
    def from_environment(cls) -> "GraphRuntime":
        return cls(
            mode=os.getenv("APP_MODE", "local").strip().lower(),
            database_url=os.getenv("DATABASE_URL", "").strip(),
        )

    def open(self) -> "GraphRuntime":
        if self.mode == "local":
            return self
        factory = self.postgres_factory
        if factory is None:
            from langgraph.checkpoint.postgres import PostgresSaver

            factory = PostgresSaver.from_conn_string
        self._context = factory(self.database_url)
        self.checkpointer = self._context.__enter__()
        self.checkpointer.setup()
        self.graph = build_graph(self.checkpointer, self.agent_factory("live"))
        self.persistence = "postgres-checkpointer"
        return self

    def close(self) -> None:
        if self._context is not None:
            self._context.__exit__(None, None, None)
            self._context = None

    def readiness(self) -> dict[str, str | bool]:
        return {
            "ready": self.mode == "local" or self.persistence == "postgres-checkpointer",
            "mode": self.mode,
            "persistence": self.persistence,
        }
