"""StateGraph: deterministic, resumable four-agent reference service."""
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from time import perf_counter
from uuid import UUID, uuid4
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

def now(): return datetime.now(timezone.utc)
class Status(str,Enum):
    in_progress="in_progress"; awaiting_approval="awaiting_approval"; completed="completed"; failed="failed"; rejected="rejected"
class TaskCreate(BaseModel):
    user_id:UUID; title:str=Field(min_length=2,max_length=120); input:str=Field(min_length=8,max_length=8000)
class Decision(BaseModel): note:str=Field(default="",max_length=500)
class Memory(BaseModel):
    id:UUID=Field(default_factory=uuid4); user_id:UUID; content:str; source_task_id:UUID|None=None; created_at:datetime=Field(default_factory=now)
class Event(BaseModel):
    id:UUID=Field(default_factory=uuid4); task_run_id:UUID; agent:str; input_summary:str; output_summary:str; duration_ms:int; created_at:datetime=Field(default_factory=now)
class Approval(BaseModel):
    id:UUID=Field(default_factory=uuid4); task_run_id:UUID; reason:str; risk_flags:list[str]; status:str="pending"; requested_at:datetime=Field(default_factory=now); resolved_at:datetime|None=None; resolution_note:str=""
class Task(BaseModel):
    id:UUID=Field(default_factory=uuid4); run_id:UUID=Field(default_factory=uuid4); thread_id:UUID|None=None; user_id:UUID; title:str; input:str; status:Status=Status.in_progress; current_node:str="research"; result:str|None=None; error:str|None=None; injected_memories:list[Memory]=Field(default_factory=list); created_at:datetime=Field(default_factory=now); updated_at:datetime=Field(default_factory=now)
class Store:
    def __init__(self):
        self.users={UUID("00000000-0000-0000-0000-000000000001"):"Avery",UUID("00000000-0000-0000-0000-000000000002"):"Blake"}; self.tasks={}; self.events={}; self.approvals={}; self.memories={}; self.lock=Lock()
store=Store()
def event(task,agent,output,started): store.events.setdefault(task.id,[]).append(Event(task_run_id=task.run_id,agent=agent,input_summary=task.input[:240],output_summary=output[:500],duration_ms=max(1,int((perf_counter()-started)*1000))))
def run(task):
    while task.status==Status.in_progress:
        started=perf_counter(); node=task.current_node
        if node=="research": out=f"Structured notes for {task.title}; model-knowledge only; prior context: "+("; ".join(m.content for m in task.injected_memories) or "none"); task.current_node="analyst"
        elif node=="analyst": out="Comparisons, risks, and confidence 0.72; verify current facts."; task.current_node="reviewer"
        elif node=="reviewer":
            flags=["sensitive_or_low_confidence_claim"] if any(x in task.input.lower() for x in ("risk","medical","legal","financial","sensitive","uncertain")) else []
            out="Review passed" if not flags else "Human review required"; event(task,node,out,started)
            if flags:
                approval=Approval(task_run_id=task.run_id,reason="Risk policy requires a human veto",risk_flags=flags); store.approvals[approval.id]=approval; task.status=Status.awaiting_approval; task.current_node="writer"; return task
            task.current_node="writer"; continue
        elif node=="writer":
            out="Final markdown deliverable created"; task.result=f"# {task.title}\n\n{task.input}\n\n- Evidence should be independently verified.\n- This demo has no live web search."; task.status=Status.completed; task.current_node="end"; memory=Memory(user_id=task.user_id,content="Prefers tables" if "table" in task.input.lower() else f"Past task: {task.title}",source_task_id=task.id); store.memories[memory.id]=memory
        else: break
        event(task,node,out,started); task.updated_at=now()
    return task
app=FastAPI(title="StateGraph API",version="1.0.0",docs_url="/api/docs")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:3000"],allow_methods=["*"],allow_headers=["*"])
@app.get("/api/health")
def health(): return {"status":"ok","mode":"deterministic","persistence":"memory","live_integrations_configured":False}
@app.get("/api/users")
def users(): return [{"id":k,"name":v} for k,v in store.users.items()]
@app.post("/api/tasks",status_code=201)
def create(body:TaskCreate):
    if body.user_id not in store.users: raise HTTPException(404,detail={"code":"user_not_found"})
    task=Task(user_id=body.user_id,title=body.title,input=body.input); task.thread_id=task.run_id; task.injected_memories=[m for m in store.memories.values() if m.user_id==body.user_id][:5]; store.tasks[task.id]=task; return run(task)
@app.get("/api/tasks")
def tasks(user_id:UUID=Query(...)): return [t for t in store.tasks.values() if t.user_id==user_id]
@app.get("/api/tasks/{task_id}")
def task(task_id:UUID):
    if task_id not in store.tasks: raise HTTPException(404,detail={"code":"task_not_found"})
    t=store.tasks[task_id]; approval=next((a for a in store.approvals.values() if a.task_run_id==t.run_id),None); return {**t.model_dump(),"approval":approval}
@app.post("/api/tasks/{task_id}/resume")
def resume(task_id:UUID):
    with store.lock:
        t=store.tasks.get(task_id)
        if not t: raise HTTPException(404,detail={"code":"task_not_found"})
        if t.status==Status.completed: return {"status":"noop","task":t}
        if t.status!=Status.in_progress: raise HTTPException(409,detail={"code":"not_resumable","status":t.status})
        return {"status":"resumed","task":run(t)}
@app.get("/api/tasks/{task_id}/events")
def events(task_id:UUID):
    if task_id not in store.tasks: raise HTTPException(404,detail={"code":"task_not_found"})
    return store.events.get(task_id,[])
@app.get("/api/users/{user_id}/memories")
def memories(user_id:UUID): return [m for m in store.memories.values() if m.user_id==user_id]
@app.delete("/api/memories/{memory_id}",status_code=204)
def prune(memory_id:UUID,user_id:UUID=Query(...)):
    m=store.memories.get(memory_id)
    if not m or m.user_id!=user_id: raise HTTPException(404,detail={"code":"memory_not_found"})
    del store.memories[memory_id]
def decide(approval_id,body,accepted):
    with store.lock:
        a=store.approvals.get(approval_id)
        if not a: raise HTTPException(404,detail={"code":"approval_not_found"})
        if a.status!="pending": return {"status":"noop"}
        a.status="approved" if accepted else "rejected"; a.resolved_at=now(); a.resolution_note=body.note; t=next(t for t in store.tasks.values() if t.run_id==a.task_run_id)
        if accepted: t.status=Status.in_progress; return run(t)
        t.status=Status.rejected; t.current_node="end"; return t
@app.post("/api/approvals/{approval_id}/approve")
def approve(approval_id:UUID,body:Decision): return decide(approval_id,body,True)
@app.post("/api/approvals/{approval_id}/reject")
def reject(approval_id:UUID,body:Decision): return decide(approval_id,body,False)
