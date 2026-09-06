"""Tests for runtime/core/task.py"""

import pytest

from runtime.core.task import (
    Assignment,
    Constraints,
    ExecutionEvidence,
    Task,
    TaskPriority,
    TaskStatus,
)


def test_task_creation():
    task = Task(title="Test task", objective="Test objective")
    assert task.title == "Test task"
    assert task.objective == "Test objective"
    assert task.status == TaskStatus.BACKLOG
    assert task.priority == TaskPriority.MEDIUM
    assert task.task_id  # non-empty


def test_task_default_values():
    task = Task(title="T", objective="O")
    assert task.project_id == "default"
    assert task.description == ""
    assert task.in_scope == []
    assert task.out_of_scope == []
    assert task.acceptance_criteria == []
    assert isinstance(task.constraints, Constraints)
    assert isinstance(task.assignment, Assignment)
    assert isinstance(task.execution_evidence, ExecutionEvidence)


def test_task_id_uniqueness():
    t1 = Task(title="A", objective="A")
    t2 = Task(title="B", objective="B")
    assert t1.task_id != t2.task_id


def test_task_valid_transition():
    task = Task(title="T", objective="O")
    assert task.status == TaskStatus.BACKLOG
    task.transition(TaskStatus.READY)
    assert task.status == TaskStatus.READY


def test_task_invalid_transition():
    task = Task(title="T", objective="O")
    with pytest.raises(ValueError, match="Invalid transition"):
        task.transition(TaskStatus.COMPLETED)


def test_task_full_lifecycle():
    task = Task(title="T", objective="O")
    task.transition(TaskStatus.READY)
    task.transition(TaskStatus.IN_PROGRESS)
    task.transition(TaskStatus.IN_REVIEW)
    task.transition(TaskStatus.COMPLETED)
    assert task.status == TaskStatus.COMPLETED


def test_task_blocked_lifecycle():
    task = Task(title="T", objective="O")
    task.transition(TaskStatus.READY)
    task.transition(TaskStatus.IN_PROGRESS)
    task.transition(TaskStatus.BLOCKED)
    assert task.status == TaskStatus.BLOCKED
    task.transition(TaskStatus.IN_PROGRESS)
    assert task.status == TaskStatus.IN_PROGRESS


def test_task_is_complete():
    task = Task(title="T", objective="O")
    task.transition(TaskStatus.READY)
    task.transition(TaskStatus.IN_PROGRESS)
    task.transition(TaskStatus.IN_REVIEW)
    task.transition(TaskStatus.COMPLETED)
    assert not task.is_complete()

    task.execution_evidence.work_summary = "Done"
    task.execution_evidence.validation_results = ["passed"]
    assert task.is_complete()


def test_task_to_handoff():
    task = Task(title="T", objective="O")
    task.task_id = "abc123"
    handoff = task.to_handoff()
    assert handoff["task_id"] == "abc123"
    assert handoff["current_status"] == "BACKLOG"
    assert handoff["completed_work"] == ""
    assert handoff["blockers"] == []


def test_task_to_dict():
    task = Task(title="T", objective="O", task_type="debugging")
    d = task.to_dict()
    assert d["title"] == "T"
    assert d["task_type"] == "debugging"
    assert "assignment" in d


def test_task_category():
    task = Task(title="T", objective="O", task_type="project_analysis")
    assert task.category() == "project_analysis"
