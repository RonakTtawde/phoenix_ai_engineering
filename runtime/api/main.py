"""Minimal FastAPI deployment layer for Phoenix AI Engineering.

Endpoints:
  GET  /           — service info
  GET  /health     — health check
  POST /tasks      — create and execute a task
  GET  /tasks/{id} — retrieve task status, result, handoff
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from runtime.agents.placeholder import ALL_PLACEHOLDER_AGENTS
from runtime.core.orchestrator import EngineeringOrchestrator
from runtime.core.result import AgentStatus
from runtime.core.task import Task, TaskPriority, TaskStatus
from runtime.core.task_manager import TaskManager

SERVICE_NAME = "phoenix-ai-engineering"
SERVICE_VERSION = "0.1.0"

_orchestrator: EngineeringOrchestrator | None = None
_task_manager: TaskManager | None = None


def _get_orchestrator() -> EngineeringOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EngineeringOrchestrator(agents=ALL_PLACEHOLDER_AGENTS)
    return _orchestrator


def _get_task_manager() -> TaskManager:
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager(orchestrator=_get_orchestrator())
    return _task_manager


app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CreateTaskRequest(BaseModel):
    title: str
    objective: str
    description: str = ""
    project_id: str = "default"
    priority: str = "MEDIUM"
    task_type: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    relevant_files: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    assigned_agent: str | None = None


class TaskResponse(BaseModel):
    task_id: str
    title: str
    objective: str
    description: str
    project_id: str
    priority: str
    status: str
    task_type: str
    acceptance_criteria: list[str]
    dependencies: list[str]
    assigned_agent: str | None


class ExecutionResultResponse(BaseModel):
    agent_id: str
    status: str
    summary: str
    artifacts: list[str]
    validation_results: list[str]
    blockers: list[str]
    recommended_next_action: str


class HandoffResponse(BaseModel):
    task_id: str
    current_status: str
    completed_work: str
    remaining_work: list[str]
    blockers: list[str]
    recommended_next_agent: str | None


class TaskDetailResponse(BaseModel):
    task: TaskResponse
    result: ExecutionResultResponse | None = None
    handoff: HandoffResponse | None = None


class ServiceInfoResponse(BaseModel):
    service: str
    version: str
    status: str


class HealthResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _task_to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        task_id=task.task_id,
        title=task.title,
        objective=task.objective,
        description=task.description,
        project_id=task.project_id,
        priority=task.priority.value,
        status=task.status.value,
        task_type=task.task_type,
        acceptance_criteria=task.acceptance_criteria,
        dependencies=task.dependencies,
        assigned_agent=task.assignment.assigned_agent,
    )


def _result_to_response(result) -> ExecutionResultResponse | None:
    if result is None:
        return None
    return ExecutionResultResponse(
        agent_id=result.agent_id,
        status=result.status.value,
        summary=result.summary,
        artifacts=result.artifacts,
        validation_results=result.validation_results,
        blockers=result.blockers,
        recommended_next_action=result.recommended_next_action,
    )


def _handoff_to_response(handoff) -> HandoffResponse | None:
    if handoff is None:
        return None
    return HandoffResponse(
        task_id=handoff["task_id"],
        current_status=handoff["current_status"],
        completed_work=handoff["completed_work"],
        remaining_work=handoff.get("remaining_work", []),
        blockers=handoff.get("blockers", []),
        recommended_next_agent=handoff.get("recommended_next_agent"),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", response_model=ServiceInfoResponse)
def service_info():
    return ServiceInfoResponse(
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        status="ok",
    )


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")


@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(req: CreateTaskRequest):
    orch = _get_orchestrator()

    priority_map = {p.value: p for p in TaskPriority}
    priority = priority_map.get(req.priority, TaskPriority.MEDIUM)

    task = Task(
        title=req.title,
        objective=req.objective,
        description=req.description,
        project_id=req.project_id,
        priority=priority,
        task_type=req.task_type,
        acceptance_criteria=req.acceptance_criteria,
        relevant_files=req.relevant_files,
        dependencies=req.dependencies,
    )
    if req.assigned_agent:
        task.assignment.assigned_agent = req.assigned_agent

    manager = _get_task_manager()
    manager.add_task(task)

    if manager.dependencies_satisfied(task):
        manager.execute_task(task.task_id)

    return _task_to_response(task)


@app.get("/tasks/{task_id}", response_model=TaskDetailResponse)
def get_task(task_id: str):
    orch = _get_orchestrator()

    task = orch.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    result = orch.get_result(task_id)
    handoff = orch.get_handoff(task_id)

    return TaskDetailResponse(
        task=_task_to_response(task),
        result=_result_to_response(result),
        handoff=_handoff_to_response(handoff),
    )
