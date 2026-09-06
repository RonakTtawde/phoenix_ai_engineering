"""Task data model compatible with shared/contracts/task-contract.md"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    BACKLOG = "BACKLOG"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    IN_REVIEW = "IN_REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class Constraints:
    architecture_constraints: list[str] = field(default_factory=list)
    technology_constraints: list[str] = field(default_factory=list)
    security_constraints: list[str] = field(default_factory=list)
    time_constraints: list[str] = field(default_factory=list)


@dataclass
class Assignment:
    assigned_agent: str | None = None
    supporting_agents: list[str] = field(default_factory=list)
    reviewer_agent: str | None = None


@dataclass
class ExecutionEvidence:
    work_summary: str = ""
    artifacts_changed: list[str] = field(default_factory=list)
    commands_or_actions_executed: list[str] = field(default_factory=list)
    validation_results: list[str] = field(default_factory=list)
    known_issues: list[str] = field(default_factory=list)


@dataclass
class Task:
    title: str
    objective: str
    description: str = ""
    project_id: str = "default"
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.BACKLOG
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    task_type: str = ""
    business_context: str = ""
    in_scope: list[str] = field(default_factory=list)
    out_of_scope: list[str] = field(default_factory=list)

    project_context: str = ""
    relevant_artifacts: list[str] = field(default_factory=list)
    relevant_files: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    acceptance_criteria: list[str] = field(default_factory=list)
    constraints: Constraints = field(default_factory=Constraints)
    assignment: Assignment = field(default_factory=Assignment)
    execution_evidence: ExecutionEvidence = field(default_factory=ExecutionEvidence)

    def transition(self, new_status: TaskStatus) -> None:
        allowed = _TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {self.status.value} -> {new_status.value}. "
                f"Allowed: {sorted(t.value for t in allowed)}"
            )
        self.status = new_status

    def category(self) -> str:
        return self.task_type

    def is_complete(self) -> bool:
        return (
            self.status == TaskStatus.COMPLETED
            and bool(self.execution_evidence.work_summary)
            and bool(self.execution_evidence.validation_results)
        )

    def to_handoff(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "current_status": self.status.value,
            "completed_work": self.execution_evidence.work_summary,
            "remaining_work": [],
            "blockers": (
                self.execution_evidence.known_issues
                if self.status == TaskStatus.BLOCKED
                else []
            ),
            "recommended_next_agent": None,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "objective": self.objective,
            "description": self.description,
            "project_id": self.project_id,
            "priority": self.priority.value,
            "status": self.status.value,
            "task_type": self.task_type,
            "acceptance_criteria": self.acceptance_criteria,
            "assignment": {
                "assigned_agent": self.assignment.assigned_agent,
                "supporting_agents": self.assignment.supporting_agents,
                "reviewer_agent": self.assignment.reviewer_agent,
            },
        }


_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.BACKLOG: {TaskStatus.READY},
    TaskStatus.READY: {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED},
    TaskStatus.IN_PROGRESS: {
        TaskStatus.BLOCKED,
        TaskStatus.IN_REVIEW,
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
    },
    TaskStatus.BLOCKED: {TaskStatus.READY, TaskStatus.IN_PROGRESS},
    TaskStatus.IN_REVIEW: {TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS, TaskStatus.FAILED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: {TaskStatus.READY},
}
