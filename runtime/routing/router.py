"""Provider/model router — selects models based on task requirements and policies."""

from __future__ import annotations

from runtime.routing.models import (
    CostTier,
    ProviderModel,
    RoutingDecision,
    TaskRequirements,
)
from runtime.routing.policy import DeterministicPolicy, RoutingPolicy, get_policy


class ProviderModelRouter:
    """Registers available provider/models and routes task requirements to them."""

    def __init__(self, default_policy: str = "deterministic") -> None:
        self._models: dict[str, ProviderModel] = {}
        self._default_policy = default_policy

    @property
    def default_policy(self) -> str:
        return self._default_policy

    def register(self, model: ProviderModel) -> None:
        key = model.full_id
        if key in self._models:
            raise ValueError(
                f"Duplicate model: '{key}' "
                f"(already registered: {self._models[key].display_name})"
            )
        self._models[key] = model

    def resolve(self, full_id: str) -> ProviderModel | None:
        return self._models.get(full_id)

    def list_all(self) -> list[ProviderModel]:
        return list(self._models.values())

    def list_available(self) -> list[ProviderModel]:
        return [m for m in self._models.values() if m.available]

    def __contains__(self, full_id: str) -> bool:
        return full_id in self._models

    def __len__(self) -> int:
        return len(self._models)

    def route(
        self,
        requirements: TaskRequirements,
        policy_id: str | None = None,
    ) -> RoutingDecision:
        pid = policy_id or self._default_policy
        policy = get_policy(pid) or DeterministicPolicy()

        reasons: list[str] = []

        candidates = self._filter_available(reasons)
        candidates = self._filter_capabilities(candidates, requirements, reasons)
        candidates = self._filter_context(candidates, requirements, reasons)
        candidates = self._filter_cost(candidates, requirements, reasons)
        candidates = self._apply_preferences(candidates, requirements, reasons)

        ranked = policy.rank(candidates)

        selected = ranked[0] if ranked else None
        if selected:
            reasons.append(f"Selected {selected.full_id} via '{pid}' policy")
        else:
            reasons.append("No compatible model found")

        return RoutingDecision(
            selected=selected,
            candidates=ranked,
            policy_used=pid,
            reasons=reasons,
        )

    def _filter_available(self, reasons: list[str]) -> list[ProviderModel]:
        available = self.list_available()
        excluded = len(self._models) - len(available)
        if excluded:
            reasons.append(f"Excluded {excluded} unavailable model(s)")
        return available

    def _filter_capabilities(
        self,
        candidates: list[ProviderModel],
        req: TaskRequirements,
        reasons: list[str],
    ) -> list[ProviderModel]:
        if not req.required_capabilities:
            return candidates

        result = []
        for m in candidates:
            if all(m.has_capability(c) for c in req.required_capabilities):
                result.append(m)

        filtered = len(candidates) - len(result)
        if filtered:
            reasons.append(
                f"Excluded {filtered} model(s) missing required capabilities"
            )
        return result

    def _filter_context(
        self,
        candidates: list[ProviderModel],
        req: TaskRequirements,
        reasons: list[str],
    ) -> list[ProviderModel]:
        if req.min_context_window <= 0:
            return candidates

        result = [m for m in candidates if m.context_window >= req.min_context_window]
        filtered = len(candidates) - len(result)
        if filtered:
            reasons.append(
                f"Excluded {filtered} model(s) below min context window "
                f"({req.min_context_window})"
            )
        return result

    def _filter_cost(
        self,
        candidates: list[ProviderModel],
        req: TaskRequirements,
        reasons: list[str],
    ) -> list[ProviderModel]:
        if req.max_cost_tier is None:
            return candidates

        max_ord = _COST_ORDER[req.max_cost_tier]
        result = [
            m for m in candidates if _COST_ORDER.get(m.cost_tier, 9) <= max_ord
        ]
        filtered = len(candidates) - len(result)
        if filtered:
            reasons.append(
                f"Excluded {filtered} model(s) above max cost tier "
                f"({req.max_cost_tier.value})"
            )
        return result

    def _apply_preferences(
        self,
        candidates: list[ProviderModel],
        req: TaskRequirements,
        reasons: list[str],
    ) -> list[ProviderModel]:
        if req.preferred_model:
            exact = [m for m in candidates if m.model_id == req.preferred_model]
            if exact:
                reasons.append(f"Matched preferred model '{req.preferred_model}'")
                return exact
            reasons.append(
                f"Preferred model '{req.preferred_model}' not in candidates, "
                "falling back"
            )

        if req.preferred_provider:
            provider_match = [
                m for m in candidates if m.provider_id == req.preferred_provider
            ]
            if provider_match:
                reasons.append(
                    f"Filtered to provider '{req.preferred_provider}'"
                )
                return provider_match
            reasons.append(
                f"Preferred provider '{req.preferred_provider}' not in candidates, "
                "falling back"
            )

        return candidates


_COST_ORDER = {
    CostTier.FREE: 0,
    CostTier.LOW: 1,
    CostTier.MEDIUM: 2,
    CostTier.HIGH: 3,
}
