"""Adapter registry for managing external coding-agent adapters.

Decoupled from orchestrator core — the orchestrator never imports this
module directly. Adapter selection is a separate concern from task routing.
"""

from __future__ import annotations

from runtime.adapters.base import AdapterCapability, AgentAdapter


class AdapterRegistry:
    """Central registry for agent adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, AgentAdapter] = {}

    def register(self, adapter: AgentAdapter) -> None:
        if adapter.adapter_id in self._adapters:
            raise ValueError(
                f"Duplicate adapter ID: '{adapter.adapter_id}' "
                f"(already registered: {self._adapters[adapter.adapter_id].name})"
            )
        self._adapters[adapter.adapter_id] = adapter

    def resolve(self, adapter_id: str) -> AgentAdapter | None:
        return self._adapters.get(adapter_id)

    def list_all(self) -> list[AgentAdapter]:
        return list(self._adapters.values())

    def list_available(self) -> list[AgentAdapter]:
        return [a for a in self._adapters.values() if a.check_availability()]

    def list_by_capability(self, task_type: str) -> list[AgentAdapter]:
        return [a for a in self._adapters.values() if a.can_handle(task_type)]

    def all_ids(self) -> list[str]:
        return sorted(self._adapters.keys())

    def __contains__(self, adapter_id: str) -> bool:
        return adapter_id in self._adapters

    def __len__(self) -> int:
        return len(self._adapters)
