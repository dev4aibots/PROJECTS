from fastapi.testclient import TestClient
from app.main import app,store
client=TestClient(app); A="00000000-0000-0000-0000-000000000001"; B="00000000-0000-0000-0000-000000000002"
def setup_function(): store.tasks.clear(); store.events.clear(); store.approvals.clear(); store.memories.clear()
def create(text="Build a competitor table"): return client.post('/api/tasks',json={'user_id':A,'title':'Market study','input':text})
def test_safe_run_and_events():
 r=create(); assert r.status_code==201 and r.json()['status']=='completed'; assert len(client.get(f"/api/tasks/{r.json()['id']}/events").json())==4
def test_interrupt_approval_and_idempotency():
 r=create('Analyze sensitive financial risk').json(); assert r['status']=='awaiting_approval'; aid=client.get(f"/api/tasks/{r['id']}").json()['approval']['id']; assert client.post(f'/api/approvals/{aid}/approve',json={}).json()['status']=='completed'; assert client.post(f'/api/approvals/{aid}/approve',json={}).json()['status']=='noop'
def test_rejection_never_runs_writer():
 r=create('Give medical risk advice').json(); aid=client.get(f"/api/tasks/{r['id']}").json()['approval']['id']; client.post(f'/api/approvals/{aid}/reject',json={}); assert all(e['agent']!='writer' for e in client.get(f"/api/tasks/{r['id']}/events").json())
def test_memory_isolation_and_owner_prune():
 create(); a=client.get(f'/api/users/{A}/memories').json(); assert a and client.get(f'/api/users/{B}/memories').json()==[]; assert client.delete(f"/api/memories/{a[0]['id']}?user_id={B}").status_code==404
def test_missing_and_completed_resume():
 assert client.post('/api/tasks/00000000-0000-0000-0000-000000000099/resume').status_code==404; r=create().json(); assert client.post(f"/api/tasks/{r['id']}/resume").json()['status']=='noop'
def test_validation_and_unknown_user():
 assert client.post('/api/tasks',json={'user_id':A,'title':'x','input':'short'}).status_code==422; assert client.post('/api/tasks',json={'user_id':'00000000-0000-0000-0000-000000000099','title':'Valid','input':'a valid long request'}).status_code==404
