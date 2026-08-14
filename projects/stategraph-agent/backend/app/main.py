"""StateGraph API backed by an actual LangGraph StateGraph and checkpointer."""
from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from enum import Enum
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command
from pydantic import BaseModel, Field

from .agents import AgentDependencyError
from .auth import Principal, current_principal
from .persistence import GraphRuntime
from .repository import build_repository

runtime = GraphRuntime.from_environment()
store = build_repository()
logger = logging.getLogger("stategraph.api")


def now() -> datetime:
    return datetime.now(timezone.utc)


class Status(str, Enum):
    in_progress = "in_progress"
    awaiting_approval = "awaiting_approval"
    completed = "completed"
    failed = "failed"
    rejected = "rejected"
    canceled = "canceled"


class TaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    input: str = Field(min_length=8, max_length=8000)
    remember: bool = False


class Decision(BaseModel):
    note: str = Field(default="", max_length=500)


class Memory(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    content: str
    source_task_id: UUID | None = None
    created_at: datetime = Field(default_factory=now)
    expires_at: datetime = Field(default_factory=lambda: now() + timedelta(days=90))


class Event(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_run_id: UUID
    agent: str
    input_summary: str
    output_summary: str
    duration_ms: int
    created_at: datetime = Field(default_factory=now)


class Approval(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_run_id: UUID
    reason: str
    risk_flags: list[str]
    status: str = "pending"
    requested_at: datetime = Field(default_factory=now)
    resolved_at: datetime | None = None
    resolution_note: str = ""


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID = Field(default_factory=uuid4)
    thread_id: UUID | None = None
    user_id: UUID
    title: str
    input: str
    status: Status = Status.in_progress
    current_node: str = "research"
    result: str | None = None
    error: str | None = None
    remember: bool = False
    injected_memories: list[Memory] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)


def _sync_events(task: Task, state: dict, started: float) -> None:
    existing_count = len(store.list_events(task.id, task.user_id))
    new_events = [
        Event(
            task_run_id=task.run_id,
            agent=item["agent"],
            input_summary=task.input[:240],
            output_summary=item["output"][:500],
            duration_ms=max(1, int((perf_counter() - started) * 1000)),
        )
        for item in state.get("events", [])[existing_count:]
    ]
    store.add_events(task.id, task.user_id, new_events)


def run(task: Task, resume: dict | None = None, retry: bool = False) -> Task:
    started = perf_counter()
    config = {"configurable": {"thread_id": str(task.thread_id)}}
    if retry:
        payload = None
    elif resume is not None:
        payload = Command(resume=resume)
    else:
        payload = {
            "title": task.title,
            "input": task.input,
            "memories": [memory.content for memory in task.injected_memories],
            "events": [],
        }
    try:
        state = runtime.graph.invoke(payload, config=config)
    except AgentDependencyError:
        task.status = Status.failed
        task.error = "dependency_unavailable"
        task.updated_at = now()
        store.save_task(task)
        return task
    task.error = None
    _sync_events(task, state, started)
    interrupts = state.get("__interrupt__", ())
    if interrupts:
        value = interrupts[0].value
        approval = Approval(
            task_run_id=task.run_id,
            reason=value["reason"],
            risk_flags=value["risk_flags"],
        )
        store.save_approval(approval, task.user_id)
        task.status = Status.awaiting_approval
        task.current_node = "reviewer"
    elif state.get("rejected"):
        task.status = Status.rejected
        task.current_node = "end"
    else:
        task.result = state.get("result")
        task.status = Status.completed
        task.current_node = "end"
        if task.remember and not store.memory_exists_for_task(task.id, task.user_id):
            memory = Memory(
                user_id=task.user_id,
                content="Prefers tables" if "table" in task.input.lower() else f"Past task: {task.title}",
                source_task_id=task.id,
            )
            store.save_memory(memory)
    task.updated_at = now()
    store.save_task(task)
    return task


@asynccontextmanager
async def lifespan(_: FastAPI):
    runtime.open()
    store.open()
    try:
        yield
    finally:
        store.close()
        runtime.close()


app = FastAPI(
    title="StateGraph API",
    version="2.1.0",
    docs_url="/api/docs",
    lifespan=lifespan,
)
origins = [item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Demo-User-Id", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def privacy_safe_request_log(request: Request, call_next):
    """Log bounded request metadata without prompts, tokens, emails, or bodies."""
    supplied_id = request.headers.get("X-Request-ID", "")
    try:
        request_id = str(UUID(supplied_id)) if supplied_id else str(uuid4())
    except ValueError:
        request_id = str(uuid4())
    started = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(json.dumps({
            "event": "request_failed",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "duration_ms": int((perf_counter() - started) * 1000),
        }))
        raise
    response.headers["X-Request-ID"] = request_id
    logger.info(json.dumps({
        "event": "request_completed",
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": int((perf_counter() - started) * 1000),
    }))
    return response


@app.get("/api/health")
def health():
    return {"status": "ok", "orchestrator": "langgraph"}


@app.get("/api/readiness")
def readiness():
    graph_status = runtime.readiness()
    projection_status = store.readiness()
    return {
        "ready": bool(graph_status["ready"] and projection_status["ready"]),
        "mode": graph_status["mode"],
        "checkpoint_persistence": graph_status["persistence"],
        "projection_persistence": projection_status["persistence"],
    }


@app.get("/api/me")
def me(principal: Principal = Depends(current_principal)):
    return {"id": principal.user_id, "email": principal.email}


def owned_task(task_id: UUID, principal: Principal) -> Task:
    task = store.get_task(task_id, principal.user_id)
    if not task:
        raise HTTPException(404, detail={"code": "task_not_found"})
    return task


@app.post("/api/tasks", status_code=201)
def create(body: TaskCreate, principal: Principal = Depends(current_principal)):
    store.ensure_user(principal.user_id, principal.email)
    task = Task(
        user_id=principal.user_id,
        title=body.title,
        input=body.input,
        remember=body.remember,
    )
    task.thread_id = task.run_id
    task.injected_memories = store.list_memories(principal.user_id, limit=5)
    store.save_task(task)
    return run(task)


@app.get("/api/tasks")
def tasks(principal: Principal = Depends(current_principal)):
    return store.list_tasks(principal.user_id)


def checkpoint_values(task: Task) -> dict:
    """Return owner-authorized checkpoint output without exposing internals."""
    snapshot = runtime.graph.get_state({"configurable": {"thread_id": str(task.thread_id)}})
    values = snapshot.values if snapshot else {}
    return values if isinstance(values, dict) else {}


@app.get("/api/tasks/{task_id}")
def task_detail(task_id: UUID, principal: Principal = Depends(current_principal)):
    task = owned_task(task_id, principal)
    approval = store.get_approval_for_run(task.run_id, principal.user_id)
    state = checkpoint_values(task)
    return {
        **task.model_dump(),
        "approval": approval,
        "events": store.list_events(task.id, principal.user_id),
        "sources": state.get("sources", []),
        "risk_flags": state.get("risk_flags", []) or (approval.risk_flags if approval else []),
    }


@app.post("/api/tasks/{task_id}/resume")
def resume_task(task_id: UUID, principal: Principal = Depends(current_principal)):
    task = owned_task(task_id, principal)
    if task.status == Status.completed:
        return {"status": "noop", "task": task}
    if task.status == Status.failed:
        task.status = Status.in_progress
        task.error = None
        store.save_task(task)
        return run(task, retry=True)
    raise HTTPException(409, detail={"code": "not_resumable", "status": task.status})


@app.post("/api/tasks/{task_id}/cancel")
def cancel_task(task_id: UUID, principal: Principal = Depends(current_principal)):
    task = owned_task(task_id, principal)
    if task.status in {Status.completed, Status.rejected, Status.canceled}:
        return {"status": "noop", "task": task}
    task.status = Status.canceled
    task.current_node = "end"
    task.error = None
    task.updated_at = now()
    store.save_task(task)
    return task


@app.get("/api/tasks/{task_id}/events")
def events(task_id: UUID, principal: Principal = Depends(current_principal)):
    owned_task(task_id, principal)
    return store.list_events(task_id, principal.user_id)


@app.get("/api/memories")
def memories(principal: Principal = Depends(current_principal)):
    return store.list_memories(principal.user_id)


@app.get("/api/memories/export")
def export_memories(principal: Principal = Depends(current_principal)):
    return {
        "user_id": principal.user_id,
        "exported_at": now(),
        "memories": store.list_memories(principal.user_id),
    }


@app.delete("/api/memories/{memory_id}", status_code=204)
def prune(memory_id: UUID, principal: Principal = Depends(current_principal)):
    if not store.delete_memory(memory_id, principal.user_id):
        raise HTTPException(404, detail={"code": "memory_not_found"})


def decide(approval_id: UUID, body: Decision, accepted: bool, principal: Principal):
    outcome, _, task = store.claim_decision(
        approval_id, principal.user_id, accepted, body.note)
    if outcome == "missing":
        raise HTTPException(404, detail={"code": "approval_not_found"})
    if outcome == "noop":
        return {"status": "noop"}
    return run(task, {"approved": accepted})


@app.post("/api/approvals/{approval_id}/approve")
def approve(
    approval_id: UUID,
    body: Decision,
    principal: Principal = Depends(current_principal),
):
    return decide(approval_id, body, True, principal)


@app.post("/api/approvals/{approval_id}/reject")
def reject(
    approval_id: UUID,
    body: Decision,
    principal: Principal = Depends(current_principal),
):
    return decide(approval_id, body, False, principal)
