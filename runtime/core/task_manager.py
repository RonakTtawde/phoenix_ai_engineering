"""Task management layer for coordinating dependent engineering tasks."""

from __future__ import annotations

from dataclasses import dataclass, field

from runtime.core.orchestrator import EngineeringOrchestrator
from runtime.core.result import AgentResult
from runtime.core.task import Task, TaskStatus


@dataclass
class TaskManager:
    """Coordinates task dependencies and execution through an orchestrator."""

    orchestrator: EngineeringOrchestrator
    tasks: dict[str, Task] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        """Register a task and make it available to the orchestrator."""
        if task.task_id in self.tasks:
            raise ValueError(f"Duplicate task ID: {task.task_id}")

        self.tasks[task.task_id] = task
        self.orchestrator.accept_task(task)

    def get_task(self, task_id: str) -> Task | None:
        """Return a task by ID."""
        return self.tasks.get(task_id)

    def dependencies_satisfied(self, task: Task) -> bool:
        """Return True only when all dependencies are completed."""
        for dependency_id in task.dependencies:
            dependency = self.tasks.get(dependency_id)

            if dependency is None:
                return False

            if dependency.status != TaskStatus.COMPLETED:
                return False

        return True

    def get_ready_tasks(self) -> list[Task]:
        """Return executable tasks whose dependencies are satisfied."""
        return [
            task
            for task in self.tasks.values()
            if task.status == TaskStatus.READY
            and self.dependencies_satisfied(task)
        ]

    def execute_task(self, task_id: str) -> AgentResult:
        """Execute one specific task when its dependencies are satisfied."""
        task = self.tasks.get(task_id)

        if task is None:
            raise KeyError(f"Unknown task ID: {task_id}")

        if task.status != TaskStatus.READY:
            raise ValueError(
                f"Task '{task_id}' is not ready for execution: "
                f"{task.status.value}"
            )

        if not self.dependencies_satisfied(task):
            raise ValueError(
                f"Task '{task_id}' has incomplete dependencies"
            )

        result = self.orchestrator.execute(task)

        if task.status == TaskStatus.IN_REVIEW:
            self.orchestrator.complete_task(task)

        return result

    def execute_next(self) -> AgentResult | None:
        """Execute the next ready task in registration order."""
        ready_tasks = self.get_ready_tasks()

        if not ready_tasks:
            return None

        return self.execute_task(ready_tasks[0].task_id)

    def complete_reviewed_tasks(self) -> list[str]:
        """Complete all tasks currently waiting in review."""
        completed: list[str] = []

        for task in self.tasks.values():
            if task.status == TaskStatus.IN_REVIEW:
                self.orchestrator.complete_task(task)
                completed.append(task.task_id)

        return completed

    def progress(self) -> dict[str, int]:
        """Return task counts grouped by lifecycle status."""
        counts = {
            status.value: 0
            for status in TaskStatus
        }

        for task in self.tasks.values():
            counts[task.status.value] += 1

        return counts