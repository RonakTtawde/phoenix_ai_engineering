"""Base agent interface. Every registered agent implements this protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod

from runtime.core.result import AgentResult
from runtime.core.task import Task


class BaseAgent(ABC):
    """Abstract base for all Phoenix agents."""

    agent_id: str = ""
    name: str = ""
    category: str = ""
    allowed_task_types: list[str] = []
    modification_permission: bool = False
    review_permission: bool = False

    @abstractmethod
    def execute(self, task: Task) -> AgentResult:
        """Execute the assigned task and return a structured result."""

    def can_handle(self, task_type: str) -> bool:
        return task_type in self.allowed_task_types

    def validate_inputs(self, task: Task) -> list[str]:
        errors: list[str] = []
        if not task.task_id:
            errors.append("task_id is required")
        if not task.objective:
            errors.append("objective is required")
        return errors
