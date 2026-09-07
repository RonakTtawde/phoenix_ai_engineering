"""Tests for runtime/api/main.py — FastAPI deployment layer."""

import pytest
from fastapi.testclient import TestClient

from runtime.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestServiceInfo:
    def test_service_info(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "phoenix-ai-engineering"
        assert data["version"] == "0.1.0"
        assert data["status"] == "ok"

    def test_service_info_structure(self, client):
        data = client.get("/").json()
        assert set(data.keys()) == {"service", "version", "status"}


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /tasks
# ---------------------------------------------------------------------------

class TestCreateTask:
    def test_create_task_minimal(self, client):
        resp = client.post("/tasks", json={
            "title": "Analyze code",
            "objective": "Find bugs",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Analyze code"
        assert data["objective"] == "Find bugs"
        assert data["task_id"]
        # No task_type assigned, so orchestrator accepts but cannot execute
        assert data["status"] == "READY"

    def test_create_task_full(self, client):
        resp = client.post("/tasks", json={
            "title": "Debug login",
            "objective": "Fix timeout",
            "description": "Login times out after 30s",
            "project_id": "auth",
            "priority": "HIGH",
            "task_type": "debugging",
            "acceptance_criteria": ["tests pass"],
            "relevant_files": ["auth.py"],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["project_id"] == "auth"
        assert data["priority"] == "HIGH"
        assert data["task_type"] == "debugging"

    def test_create_task_assigns_agent(self, client):
        resp = client.post("/tasks", json={
            "title": "Analyze",
            "objective": "Analyze architecture",
            "task_type": "project_analysis",
        })
        data = resp.json()
        assert data["assigned_agent"] == "ANALYSIS-001"

    def test_create_task_returns_result(self, client):
        resp = client.post("/tasks", json={
            "title": "Debug",
            "objective": "Fix bug",
            "task_type": "debugging",
        })
        assert resp.status_code == 201
        task_id = resp.json()["task_id"]

        detail = client.get(f"/tasks/{task_id}").json()
        assert detail["result"] is not None
        assert detail["result"]["status"] == "SUCCESS"

    def test_create_task_invalid_priority_defaults(self, client):
        resp = client.post("/tasks", json={
            "title": "Test",
            "objective": "Test obj",
            "priority": "INVALID",
        })
        assert resp.status_code == 201
        assert resp.json()["priority"] == "MEDIUM"

    def test_create_task_missing_title_fails(self, client):
        resp = client.post("/tasks", json={
            "objective": "No title",
        })
        assert resp.status_code == 422

    def test_create_task_missing_objective_fails(self, client):
        resp = client.post("/tasks", json={
            "title": "No objective",
        })
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /tasks/{task_id}
# ---------------------------------------------------------------------------

class TestGetTask:
    def test_get_existing_task(self, client):
        create = client.post("/tasks", json={
            "title": "T",
            "objective": "O",
            "task_type": "project_analysis",
        })
        task_id = create.json()["task_id"]

        resp = client.get(f"/tasks/{task_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["task"]["task_id"] == task_id
        assert data["result"] is not None
        assert data["handoff"] is not None

    def test_get_nonexistent_task(self, client):
        resp = client.get("/tasks/nonexistent123")
        assert resp.status_code == 404

    def test_task_has_handoff(self, client):
        create = client.post("/tasks", json={
            "title": "T",
            "objective": "O",
            "task_type": "debugging",
        })
        task_id = create.json()["task_id"]
        detail = client.get(f"/tasks/{task_id}").json()

        handoff = detail["handoff"]
        assert handoff["task_id"] == task_id
        assert handoff["current_status"] in (
            "IN_REVIEW", "COMPLETED", "BLOCKED", "FAILED"
        )

    def test_task_result_has_agent_id(self, client):
        create = client.post("/tasks", json={
            "title": "T",
            "objective": "O",
            "task_type": "backend_development",
        })
        task_id = create.json()["task_id"]
        detail = client.get(f"/tasks/{task_id}").json()

        assert detail["result"]["agent_id"] == "BACKEND-001"

    def test_task_detail_structure(self, client):
        create = client.post("/tasks", json={
            "title": "T",
            "objective": "O",
            "task_type": "project_analysis",
        })
        task_id = create.json()["task_id"]
        detail = client.get(f"/tasks/{task_id}").json()

        assert set(detail.keys()) == {"task", "result", "handoff"}
        assert set(detail["task"].keys()) == {
            "task_id", "title", "objective", "description",
            "project_id", "priority", "status", "task_type",
            "acceptance_criteria", "dependencies", "assigned_agent",
        }
        assert set(detail["result"].keys()) == {
            "agent_id", "status", "summary", "artifacts",
            "validation_results", "blockers", "recommended_next_action",
        }


# ---------------------------------------------------------------------------
# Multiple tasks
# ---------------------------------------------------------------------------

class TestMultipleTasks:
    def test_create_and_list_multiple(self, client):
        ids = []
        for i in range(3):
            resp = client.post("/tasks", json={
                "title": f"Task {i}",
                "objective": f"Objective {i}",
                "task_type": "project_analysis",
            })
            assert resp.status_code == 201
            ids.append(resp.json()["task_id"])

        assert len(set(ids)) == 3

        for tid in ids:
            resp = client.get(f"/tasks/{tid}")
            assert resp.status_code == 200

    def test_different_task_types_different_agents(self, client):
        r1 = client.post("/tasks", json={
            "title": "Analyze",
            "objective": "A",
            "task_type": "project_analysis",
        })
        r2 = client.post("/tasks", json={
            "title": "Debug",
            "objective": "D",
            "task_type": "debugging",
        })
        assert r1.json()["assigned_agent"] == "ANALYSIS-001"
        assert r2.json()["assigned_agent"] == "DEBUG-001"


# ---------------------------------------------------------------------------
# OpenCode API routing
# ---------------------------------------------------------------------------

class TestOpenCodeApiRouting:
    def test_explicit_opencode_agent_routes_through_api(
        self,
        client,
        monkeypatch,
    ):
        from runtime.api import main as api_main
        from runtime.core.result import AgentResult, AgentStatus

        orch = api_main._get_orchestrator()
        opencode_agent = orch.agents["adapter:opencode"]

        def fake_execute(task):
            return AgentResult(
                status=AgentStatus.SUCCESS,
                summary="Mock OpenCode execution completed",
                artifacts=["runtime/adapters/opencode.py"],
                validation_results=["mock validation passed"],
            )

        monkeypatch.setattr(opencode_agent, "execute", fake_execute)

        resp = client.post(
            "/tasks",
            json={
                "title": "OpenCode API routing test",
                "objective": "Verify explicit OpenCode routing",
                "task_type": "code_review",
                "assigned_agent": "adapter:opencode",
                "relevant_files": [
                    "/mnt/d/phoenix_ai_engineering/runtime/adapters/opencode.py"
                ],
            },
        )

        assert resp.status_code == 201
        task_id = resp.json()["task_id"]
        assert resp.json()["assigned_agent"] == "adapter:opencode"

        detail = client.get(f"/tasks/{task_id}")
        assert detail.status_code == 200

        data = detail.json()
        assert data["result"]["agent_id"] == "adapter:opencode"
        assert data["result"]["status"] == "SUCCESS"
        assert data["result"]["summary"] == "Mock OpenCode execution completed"
