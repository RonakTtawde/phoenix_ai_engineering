"""Tests for runtime/core/orchestrator.py"""

from runtime.agents.placeholder import (
    PlaceholderAnalysisAgent,
    PlaceholderDebuggingAgent,
)
from runtime.core.orchestrator import EngineeringOrchestrator
from runtime.core.result import AgentStatus
from runtime.core.task import Task, TaskPriority, TaskStatus


def _make_orchestrator():
    agents = {
        "ANALYSIS-001": PlaceholderAnalysisAgent(),
        "DEBUG-001": PlaceholderDebuggingAgent(),
    }
    return EngineeringOrchestrator(agents=agents)


def test_orchestrator_accept_task():
    orch = _make_orchestrator()
    task = Task(title="Test", objective="Test obj")
    assert task.status == TaskStatus.BACKLOG

    orch.accept_task(task)
    assert task.status == TaskStatus.READY
    assert task.task_id in orch.state.tasks


def test_orchestrator_select_agent_by_assignment():
    orch = _make_orchestrator()
    task = Task(title="Test", objective="Obj", task_type="project_analysis")
    task.assignment.assigned_agent = "ANALYSIS-001"
    orch.accept_task(task)

    agent = orch.select_agent(task)
    assert agent is not None
    assert agent.agent_id == "ANALYSIS-001"


def test_orchestrator_select_agent_by_task_type():
    orch = _make_orchestrator()
    task = Task(title="Debug", objective="Fix bug", task_type="debugging")
    orch.accept_task(task)

    agent = orch.select_agent(task)
    assert agent is not None
    assert agent.agent_id == "DEBUG-001"


def test_orchestrator_execute_success():
    orch = _make_orchestrator()
    task = Task(title="Analyze", objective="Analyze code", task_type="project_analysis")
    orch.accept_task(task)

    result = orch.execute(task)
    assert result.status == AgentStatus.SUCCESS
    assert result.agent_id == "ANALYSIS-001"
    assert len(result.validation_results) > 0
    assert task.status == TaskStatus.IN_REVIEW


def test_orchestrator_execute_no_agent():
    orch = _make_orchestrator()
    task = Task(title="Unknown", objective="Do something", task_type="nonexistent")
    orch.accept_task(task)

    result = orch.execute(task)
    assert result.status == AgentStatus.FAILED
    assert "No agent found" in result.summary


def test_orchestrator_complete_task():
    orch = _make_orchestrator()
    task = Task(title="Analyze", objective="Analyze", task_type="project_analysis")
    orch.accept_task(task)
    orch.execute(task)

    orch.complete_task(task)
    assert task.status == TaskStatus.COMPLETED


def test_orchestrator_get_handoff():
    orch = _make_orchestrator()
    task = Task(title="T", objective="O", task_type="project_analysis")
    orch.accept_task(task)
    orch.execute(task)

    handoff = orch.get_handoff(task.task_id)
    assert handoff is not None
    assert handoff["task_id"] == task.task_id
    assert handoff["current_status"] == "IN_REVIEW"


def test_orchestrator_get_handoff_nonexistent():
    orch = _make_orchestrator()
    assert orch.get_handoff("nonexistent") is None


def test_orchestrator_execution_log():
    orch = _make_orchestrator()
    task = Task(title="T", objective="O", task_type="project_analysis")
    orch.accept_task(task)
    orch.execute(task)

    log = orch.state.execution_log
    events = [e["event"] for e in log]
    assert "TASK_ACCEPTED" in events
    assert "AGENT_ASSIGNED" in events
    assert "EXECUTION_SUCCESS" in events


def test_orchestrator_result_stored():
    orch = _make_orchestrator()
    task = Task(title="T", objective="O", task_type="debugging")
    orch.accept_task(task)
    result = orch.execute(task)

    stored = orch.get_result(task.task_id)
    assert stored is not None
    assert stored.status == result.status


def test_orchestrator_full_lifecycle():
    orch = _make_orchestrator()
    task = Task(title="Analyze", objective="Full lifecycle", task_type="project_analysis")
    orch.accept_task(task)
    result = orch.execute(task)
    orch.complete_task(task)

    assert task.status == TaskStatus.COMPLETED
    assert result.is_success()
    handoff = orch.get_handoff(task.task_id)
    assert handoff["current_status"] == "COMPLETED"
