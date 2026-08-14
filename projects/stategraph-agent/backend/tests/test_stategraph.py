from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.agents import AgentDependencyError
from app.main import app, runtime, store

client = TestClient(app)
A = "00000000-0000-0000-0000-000000000001"
B = "00000000-0000-0000-0000-000000000002"


def headers(user=A):
    return {"X-Demo-User-Id": user}


def setup_function():
    store.reset()


def create(text="Build a competitor table", user=A, remember=False):
    return client.post(
        "/api/tasks",
        headers=headers(user),
        json={"title": "Market study", "input": text, "remember": remember},
    )


def test_safe_run_and_events():
    response = create()
    assert response.status_code == 201 and response.json()["status"] == "completed"
    task_id = response.json()["id"]
    assert len(client.get(f"/api/tasks/{task_id}/events", headers=headers()).json()) == 4


def test_local_browser_cors_allows_demo_identity_header():
    response = client.options(
        "/api/tasks",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-demo-user-id,x-request-id",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    allowed_headers = response.headers["access-control-allow-headers"].lower()
    assert "x-demo-user-id" in allowed_headers
    assert "x-request-id" in allowed_headers


def test_request_metadata_is_correlated_without_logging_sensitive_body(caplog):
    request_id = "11111111-1111-1111-1111-111111111111"
    sensitive = "Analyze financial risk for private-user@example.test"
    request_headers = {**headers(), "X-Request-ID": request_id}
    with caplog.at_level("INFO", logger="stategraph.api"):
        response = client.post(
            "/api/tasks",
            headers=request_headers,
            json={"title": "Market study", "input": sensitive, "remember": False},
        )
    assert response.headers["x-request-id"] == request_id
    records = [record.message for record in caplog.records if "request_completed" in record.message]
    assert records
    assert request_id in records[-1]
    assert sensitive not in "\n".join(records)
    assert "private-user@example.test" not in "\n".join(records)


def test_interrupt_approval_and_idempotency():
    task = create("Analyze sensitive financial risk").json()
    assert task["status"] == "awaiting_approval"
    detail = client.get(f"/api/tasks/{task['id']}", headers=headers()).json()
    approval_id = detail["approval"]["id"]
    result = client.post(
        f"/api/approvals/{approval_id}/approve", headers=headers(), json={}
    ).json()
    assert result["status"] == "completed"
    assert client.post(
        f"/api/approvals/{approval_id}/approve", headers=headers(), json={}
    ).json()["status"] == "noop"


def test_rejection_never_runs_writer():
    task = create("Give medical risk advice").json()
    detail = client.get(f"/api/tasks/{task['id']}", headers=headers()).json()
    approval_id = detail["approval"]["id"]
    client.post(f"/api/approvals/{approval_id}/reject", headers=headers(), json={})
    events = client.get(f"/api/tasks/{task['id']}/events", headers=headers()).json()
    assert all(event["agent"] != "writer" for event in events)


def test_memory_is_opt_in_and_owner_scoped():
    create(remember=False)
    assert client.get("/api/memories", headers=headers()).json() == []
    create(remember=True)
    memories = client.get("/api/memories", headers=headers()).json()
    assert memories and memories[0]["source_task_id"]
    assert memories[0]["expires_at"] > memories[0]["created_at"]
    exported = client.get("/api/memories/export", headers=headers()).json()
    assert exported["user_id"] == A and exported["memories"] == memories
    assert client.get("/api/memories", headers=headers(B)).json() == []
    assert client.delete(
        f"/api/memories/{memories[0]['id']}", headers=headers(B)
    ).status_code == 404


def test_cross_tenant_task_event_and_approval_access_is_hidden():
    task = create("Analyze sensitive financial risk", user=A).json()
    detail = client.get(f"/api/tasks/{task['id']}", headers=headers(A)).json()
    approval_id = detail["approval"]["id"]
    assert client.get(f"/api/tasks/{task['id']}", headers=headers(B)).status_code == 404
    assert client.get(f"/api/tasks/{task['id']}/events", headers=headers(B)).status_code == 404
    assert client.post(
        f"/api/tasks/{task['id']}/resume", headers=headers(B)
    ).status_code == 404
    assert client.post(
        f"/api/approvals/{approval_id}/approve", headers=headers(B), json={}
    ).status_code == 404
    assert client.get("/api/tasks", headers=headers(B)).json() == []


def test_missing_and_completed_resume():
    missing = "00000000-0000-0000-0000-000000000099"
    assert client.post(f"/api/tasks/{missing}/resume", headers=headers()).status_code == 404
    task = create().json()
    assert client.post(
        f"/api/tasks/{task['id']}/resume", headers=headers()
    ).json()["status"] == "noop"


def test_dependency_failure_is_sanitized_and_retryable(monkeypatch):
    original = runtime.graph

    class FlakyGraph:
        def __init__(self):
            self.calls = 0

        def invoke(self, payload, config):
            self.calls += 1
            if self.calls == 1:
                raise AgentDependencyError("secret provider detail")
            assert payload is None
            return {
                "events": [
                    {"agent": "research", "output": "Recovered search"},
                    {"agent": "analyst", "output": "Recovered analysis"},
                    {"agent": "reviewer", "output": "Review passed"},
                    {"agent": "writer", "output": "Recovered result"},
                ],
                "result": "# Recovered result",
            }

        def get_state(self, _config):
            return SimpleNamespace(values={})

    runtime.graph = FlakyGraph()
    try:
        failed = create().json()
        assert failed["status"] == "failed"
        assert failed["error"] == "dependency_unavailable"
        retried = client.post(
            f"/api/tasks/{failed['id']}/resume", headers=headers()
        ).json()
        assert retried["status"] == "completed"
        assert retried["error"] is None
        assert retried["result"] == "# Recovered result"
    finally:
        runtime.graph = original


def test_cancel_is_owner_scoped_idempotent_and_cannot_be_resumed_by_approval():
    task = create("Analyze sensitive financial risk").json()
    detail = client.get(f"/api/tasks/{task['id']}", headers=headers(A)).json()
    approval_id = detail["approval"]["id"]
    assert client.post(
        f"/api/tasks/{task['id']}/cancel", headers=headers(B)
    ).status_code == 404
    canceled = client.post(
        f"/api/tasks/{task['id']}/cancel", headers=headers(A)
    ).json()
    assert canceled["status"] == "canceled"
    assert client.post(
        f"/api/tasks/{task['id']}/cancel", headers=headers(A)
    ).json()["status"] == "noop"
    assert client.post(
        f"/api/approvals/{approval_id}/approve", headers=headers(A), json={}
    ).json()["status"] == "noop"
    persisted = client.get(f"/api/tasks/{task['id']}", headers=headers(A)).json()
    assert persisted["status"] == "canceled"
    assert all(event["agent"] != "writer" for event in persisted["events"])


def test_task_detail_includes_timeline_sources_and_risk_flags():
    task = create("Analyze sensitive financial risk").json()
    detail = client.get(f"/api/tasks/{task['id']}", headers=headers()).json()
    assert len(detail["events"]) == 2
    assert detail["sources"][0]["url"] == "https://example.com/research-fixture"
    assert "financial_domain" in detail["risk_flags"]


def test_identity_comes_from_header_not_body():
    response = client.post(
        "/api/tasks",
        headers=headers(B),
        json={
            "user_id": A,
            "title": "Valid",
            "input": "a valid long request",
        },
    )
    assert response.status_code == 201
    assert response.json()["user_id"] == B


def test_validation_and_invalid_local_identity():
    assert client.post(
        "/api/tasks",
        headers=headers(),
        json={"title": "x", "input": "short"},
    ).status_code == 422
    assert client.get("/api/tasks", headers={"X-Demo-User-Id": "bad"}).status_code == 400
