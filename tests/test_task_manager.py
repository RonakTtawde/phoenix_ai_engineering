"""Tests for runtime/core/task_manager.py."""

import pytest

from runtime.agents.placeholder import (
    PlaceholderAnalysisAgent,
    PlaceholderDebuggingAgent,
)
from runtime.core.orchestrator import EngineeringOrchestrator
from runtime.core.result import AgentStatus
from runtime.core.task import Task, TaskStatus
from runtime.core.task_manager import TaskManager


def _make_manager() -> TaskManager:
    agents = {
        "ANALYSIS-001": PlaceholderAnalysisAgent(),
        "DEBUG-001": PlaceholderDebuggingAgent(),
    }
    return TaskManager(
        orchestrator=EngineeringOrchestrator(agents=agents)
    )


def test_add_task_registers_and_accepts_task():
    manager = _make_manager()
    task = Task(
        title="Analyze",
        objective="Analyze code",
        task_type="project_analysis",
    )

    manager.add_task(task)

    assert manager.get_task(task.task_id) is task
    assert task.status == TaskStatus.READY


def test_duplicate_task_rejected():
    manager = _make_manager()
    task = Task(
        title="Analyze",
        objective="Analyze code",
        task_type="project_analysis",
    )

    manager.add_task(task)

    with pytest.raises(ValueError, match="Duplicate task ID"):
        manager.add_task(task)


def test_task_without_dependencies_is_ready():
    manager = _make_manager()
    task = Task(
        title="Debug",
        objective="Debug code",
        task_type="debugging",
    )

    manager.add_task(task)

    assert manager.dependencies_satisfied(task)
    assert manager.get_ready_tasks() == [task]


def test_task_waits_for_dependency_completion():
    manager = _make_manager()

    first = Task(
        title="Analyze",
        objective="Analyze code",
        task_type="project_analysis",
    )

    second = Task(
        title="Debug",
        objective="Fix issue",
        task_type="debugging",
        dependencies=[first.task_id],
    )

    manager.add_task(first)
    manager.add_task(second)

    assert manager.dependencies_satisfied(first)
    assert not manager.dependencies_satisfied(second)
    assert manager.get_ready_tasks() == [first]


def test_dependency_becomes_ready_after_completion():
    manager = _make_manager()

    first = Task(
        title="Analyze",
        objective="Analyze code",
        task_type="project_analysis",
    )

    second = Task(
        title="Debug",
        objective="Fix issue",
        task_type="debugging",
        dependencies=[first.task_id],
    )

    manager.add_task(first)
    manager.add_task(second)

    result = manager.execute_task(first.task_id)

    assert result.status == AgentStatus.SUCCESS
    assert first.status == TaskStatus.COMPLETED
    assert manager.dependencies_satisfied(second)
    assert second.status == TaskStatus.COMPLETED
    assert manager.get_ready_tasks() == []


def test_execute_next_runs_first_ready_task():
    manager = _make_manager()

    first = Task(
        title="Analyze",
        objective="Analyze code",
        task_type="project_analysis",
    )

    second = Task(
        title="Debug",
        objective="Debug code",
        task_type="debugging",
    )

    manager.add_task(first)
    manager.add_task(second)

    result = manager.execute_next()

    assert result is not None
    assert result.status == AgentStatus.SUCCESS
    assert first.status == TaskStatus.COMPLETED
    assert second.status == TaskStatus.READY


def test_execute_next_returns_none_when_no_task_ready():
    manager = _make_manager()

    task = Task(
        title="Blocked",
        objective="Wait",
        task_type="debugging",
        dependencies=["missing-task"],
    )

    manager.add_task(task)

    assert manager.execute_next() is None


def test_execute_unknown_task_rejected():
    manager = _make_manager()

    with pytest.raises(KeyError, match="Unknown task ID"):
        manager.execute_task("missing")


def test_execute_task_with_incomplete_dependency_rejected():
    manager = _make_manager()

    first = Task(
        title="Analyze",
        objective="Analyze code",
        task_type="project_analysis",
    )

    second = Task(
        title="Debug",
        objective="Debug code",
        task_type="debugging",
        dependencies=[first.task_id],
    )

    manager.add_task(first)
    manager.add_task(second)

    with pytest.raises(ValueError, match="incomplete dependencies"):
        manager.execute_task(second.task_id)


def test_progress_reports_status_counts():
    manager = _make_manager()

    first = Task(
        title="Analyze",
        objective="Analyze code",
        task_type="project_analysis",
    )

    second = Task(
        title="Debug",
        objective="Debug code",
        task_type="debugging",
        dependencies=[first.task_id],
    )

    manager.add_task(first)
    manager.add_task(second)

    progress = manager.progress()

    assert progress["READY"] == 2
    assert progress["BACKLOG"] == 0
    assert progress["COMPLETED"] == 0

    manager.execute_task(first.task_id)

    progress = manager.progress()

    assert progress["COMPLETED"] == 2
    assert progress["READY"] == 0

# ---------------------------------------------------------------------------
# Automatic dependency progression
# ---------------------------------------------------------------------------

def test_completed_task_automatically_executes_unlocked_dependent():
    manager = _make_manager()

    first = Task(
        title="Analyze",
        objective="Analyze code",
        task_type="project_analysis",
    )

    second = Task(
        title="Debug",
        objective="Debug code",
        task_type="debugging",
        dependencies=[first.task_id],
    )

    manager.add_task(first)
    manager.add_task(second)

    result = manager.execute_task(first.task_id)

    assert result.status == AgentStatus.SUCCESS
    assert first.status == TaskStatus.COMPLETED
    assert second.status == TaskStatus.COMPLETED


def test_completed_task_automatically_progresses_dependency_chain():
    manager = _make_manager()

    first = Task(
        title="Analyze",
        objective="Analyze code",
        task_type="project_analysis",
    )

    second = Task(
        title="Debug",
        objective="Debug code",
        task_type="debugging",
        dependencies=[first.task_id],
    )

    third = Task(
        title="Analyze follow-up",
        objective="Analyze results",
        task_type="project_analysis",
        dependencies=[second.task_id],
    )

    manager.add_task(first)
    manager.add_task(second)
    manager.add_task(third)

    result = manager.execute_task(first.task_id)

    assert result.status == AgentStatus.SUCCESS
    assert first.status == TaskStatus.COMPLETED
    assert second.status == TaskStatus.COMPLETED
    assert third.status == TaskStatus.COMPLETED
