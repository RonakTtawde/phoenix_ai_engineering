"""Routing policies for selecting among compatible provider/models."""

from __future__ import annotations

from abc import ABC, abstractmethod

from runtime.routing.models import CostTier, ProviderModel


class RoutingPolicy(ABC):
    policy_id: str = ""
    description: str = ""

    @abstractmethod
    def rank(self, candidates: list[ProviderModel]) -> list[ProviderModel]:
        """Return candidates sorted by preference (best first)."""


class DeterministicPolicy(RoutingPolicy):
    """Stable sort by provider_id then model_id. Reproducible across runs."""

    policy_id = "deterministic"
    description = "Deterministic ordering by provider and model ID"

    def rank(self, candidates: list[ProviderModel]) -> list[ProviderModel]:
        return sorted(candidates, key=lambda m: (m.provider_id, m.model_id))


class LowCostPolicy(RoutingPolicy):
    """Prefer cheapest models. Tie-break by provider/model ID."""

    policy_id = "low_cost"
    description = "Prefer lowest cost tier"

    _COST_ORDER = {
        CostTier.FREE: 0,
        CostTier.LOW: 1,
        CostTier.MEDIUM: 2,
        CostTier.HIGH: 3,
    }

    def rank(self, candidates: list[ProviderModel]) -> list[ProviderModel]:
        return sorted(
            candidates,
            key=lambda m: (self._COST_ORDER.get(m.cost_tier, 9), m.provider_id, m.model_id),
        )


class HighCapabilityPolicy(RoutingPolicy):
    """Prefer largest context window and most capabilities. Tie-break by ID."""

    policy_id = "high_capability"
    description = "Prefer models with largest context and most capabilities"

    def rank(self, candidates: list[ProviderModel]) -> list[ProviderModel]:
        return sorted(
            candidates,
            key=lambda m: (
                -len(m.capabilities),
                -m.context_window,
                m.provider_id,
                m.model_id,
            ),
        )


class BalancedPolicy(RoutingPolicy):
    """Score-based: balance cost (lower better) against capability (higher better).

    Score = capability_ratio - cost_weight
    capability_ratio = min(capabilities_count / 5, 1.0)
    cost_weight = cost_tier_normalized
    """

    policy_id = "balanced"
    description = "Balance cost and capability"

    _COST_ORDER = {
        CostTier.FREE: 0.0,
        CostTier.LOW: 0.25,
        CostTier.MEDIUM: 0.5,
        CostTier.HIGH: 1.0,
    }

    def _score(self, m: ProviderModel) -> float:
        cap_score = min(len(m.capabilities) / 5.0, 1.0)
        cost_score = self._COST_ORDER.get(m.cost_tier, 0.5)
        ctx_score = min(m.context_window / 200_000.0, 1.0) if m.context_window > 0 else 0.0
        return cap_score + ctx_score - cost_score

    def rank(self, candidates: list[ProviderModel]) -> list[ProviderModel]:
        return sorted(
            candidates,
            key=lambda m: (-self._score(m), m.provider_id, m.model_id),
        )


POLICIES: dict[str, RoutingPolicy] = {
    p.policy_id: p
    for p in [DeterministicPolicy(), LowCostPolicy(), HighCapabilityPolicy(), BalancedPolicy()]
}


def get_policy(policy_id: str) -> RoutingPolicy | None:
    return POLICIES.get(policy_id)


def list_policies() -> list[str]:
    return sorted(POLICIES.keys())
