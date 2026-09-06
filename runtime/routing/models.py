"""Data structures for provider/model routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CostTier(str, Enum):
    FREE = "FREE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Complexity(str, Enum):
    TRIVIAL = "TRIVIAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ProviderModel:
    provider_id: str
    model_id: str
    display_name: str
    capabilities: list[str] = field(default_factory=list)
    cost_tier: CostTier = CostTier.MEDIUM
    context_window: int = 0
    available: bool = True

    @property
    def full_id(self) -> str:
        return f"{self.provider_id}/{self.model_id}"

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "display_name": self.display_name,
            "full_id": self.full_id,
            "capabilities": self.capabilities,
            "cost_tier": self.cost_tier.value,
            "context_window": self.context_window,
            "available": self.available,
        }


@dataclass
class TaskRequirements:
    task_type: str = ""
    required_capabilities: list[str] = field(default_factory=list)
    complexity: Complexity = Complexity.MEDIUM
    min_context_window: int = 0
    preferred_provider: str | None = None
    preferred_model: str | None = None
    max_cost_tier: CostTier | None = None

    def to_dict(self) -> dict:
        return {
            "task_type": self.task_type,
            "required_capabilities": self.required_capabilities,
            "complexity": self.complexity.value,
            "min_context_window": self.min_context_window,
            "preferred_provider": self.preferred_provider,
            "preferred_model": self.preferred_model,
            "max_cost_tier": self.max_cost_tier.value if self.max_cost_tier else None,
        }


@dataclass
class RoutingDecision:
    selected: ProviderModel | None
    candidates: list[ProviderModel]
    policy_used: str
    reasons: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.selected is not None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "selected": self.selected.to_dict() if self.selected else None,
            "candidates_count": len(self.candidates),
            "policy_used": self.policy_used,
            "reasons": self.reasons,
        }
