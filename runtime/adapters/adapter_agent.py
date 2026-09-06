"""AdapterAgent — wraps an AgentAdapter into a BaseAgent for orchestrator use.

This is the bridge between the adapter layer and the orchestrator core.
The orchestrator never imports adapter modules directly; it only sees BaseAgent.
"""

from __future__ import annotations

from runtime.adapters.base import AgentAdapter
from runtime.agents.base import BaseAgent
from runtime.core.result import AgentResult, AgentStatus
from runtime.core.task import Task


class AdapterAgent(BaseAgent):
    """Wraps an AgentAdapter so the orchestrator can use it as a BaseAgent."""

    def __init__(self, adapter: AgentAdapter) -> None:
        self._adapter = adapter
        caps = adapter.capabilities()
        self.agent_id = f"adapter:{adapter.adapter_id}"
        self.name = adapter.name
        self.category = "adapter"
        self.allowed_task_types = list(caps.task_types)
        self.modification_permission = caps.supports_modification
        self.review_permission = False

    @property
    def adapter(self) -> AgentAdapter:
        return self._adapter

    def execute(self, task: Task) -> AgentResult:
        if not self._adapter.check_availability():
            return AgentResult(
                status=AgentStatus.BLOCKED,
                summary=f"Adapter '{self._adapter.adapter_id}' is not available",
                blockers=[f"{self._adapter.name} unavailable"],
            )
        return self._adapter.execute(task, dry_run=False)

    def execute_dry_run(self, task: Task) -> AgentResult:
        if not self._adapter.check_availability():
            return AgentResult(
                status=AgentStatus.BLOCKED,
                summary=f"Adapter '{self._adapter.adapter_id}' is not available",
                blockers=[f"{self._adapter.name} unavailable"],
            )
        return self._adapter.execute(task, dry_run=True)
