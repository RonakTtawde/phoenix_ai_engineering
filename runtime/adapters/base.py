"""Abstract adapter interface for external coding-agent systems.

An adapter wraps an external system (OpenCode CLI, future MCP servers, etc.)
into a form the Phoenix orchestrator can consume. Adapters do NOT replace
BaseAgent — they produce BaseAgent-compatible results that the orchestrator
already understands.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from runtime.core.result import AgentResult
from runtime.core.task import Task


@dataclass
class AdapterCapability:
    """Declares what an adapter can do."""

    task_types: list[str] = field(default_factory=list)
    description: str = ""
    supports_dry_run: bool = False
    supports_modification: bool = False


class AgentAdapter(ABC):
    """Abstract base for all Phoenix agent adapters.

    Subclasses implement check_availability(), capabilities(), and execute().
    The orchestrator never calls these directly — an AdapterAgent wrapper
    translates between BaseAgent and AgentAdapter.
    """

    adapter_id: str = ""
    name: str = ""

    @abstractmethod
    def check_availability(self) -> bool:
        """Return True if the external system is reachable/installed."""

    @abstractmethod
    def capabilities(self) -> AdapterCapability:
        """Declare what this adapter can handle."""

    @abstractmethod
    def execute(self, task: Task, dry_run: bool = False) -> AgentResult:
        """Execute the task against the external system.

        When dry_run=True, produce a result describing what *would* happen
        without performing any destructive or side-effecting operation.
        """

    def can_handle(self, task_type: str) -> bool:
        return task_type in self.capabilities().task_types
