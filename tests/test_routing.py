"""Tests for runtime/routing — models, router, policies, and backward compat."""

import pytest

from runtime.routing.models import (
    Complexity,
    CostTier,
    ProviderModel,
    RoutingDecision,
    TaskRequirements,
)
from runtime.routing.router import ProviderModelRouter
from runtime.routing.policy import (
    BalancedPolicy,
    DeterministicPolicy,
    HighCapabilityPolicy,
    LowCostPolicy,
    get_policy,
    list_policies,
)


# ---------------------------------------------------------------------------
# Fixtures — sample models
# ---------------------------------------------------------------------------

def _gemini_pro() -> ProviderModel:
    return ProviderModel(
        provider_id="gemini",
        model_id="gemini-3-pro",
        display_name="Gemini 3 Pro",
        capabilities=["code_generation", "analysis", "debugging", "reasoning", "multimodal"],
        cost_tier=CostTier.HIGH,
        context_window=200_000,
        available=True,
    )


def _gemini_flash() -> ProviderModel:
    return ProviderModel(
        provider_id="gemini",
        model_id="gemini-2-flash",
        display_name="Gemini 2 Flash",
        capabilities=["code_generation", "analysis", "debugging"],
        cost_tier=CostTier.LOW,
        context_window=100_000,
        available=True,
    )


def _openai_gpt4() -> ProviderModel:
    return ProviderModel(
        provider_id="openai",
        model_id="gpt-4",
        display_name="GPT-4",
        capabilities=["code_generation", "analysis", "reasoning"],
        cost_tier=CostTier.HIGH,
        context_window=128_000,
        available=True,
    )


def _openai_gpt35() -> ProviderModel:
    return ProviderModel(
        provider_id="openai",
        model_id="gpt-3.5-turbo",
        display_name="GPT-3.5 Turbo",
        capabilities=["code_generation"],
        cost_tier=CostTier.LOW,
        context_window=16_000,
        available=True,
    )


def _local_model() -> ProviderModel:
    return ProviderModel(
        provider_id="local",
        model_id="codellama-7b",
        display_name="CodeLlama 7B",
        capabilities=["code_generation"],
        cost_tier=CostTier.FREE,
        context_window=8_000,
        available=True,
    )


def _unavailable_model() -> ProviderModel:
    return ProviderModel(
        provider_id="deepseek",
        model_id="deepseek-v3",
        display_name="DeepSeek V3",
        capabilities=["code_generation", "analysis"],
        cost_tier=CostTier.MEDIUM,
        context_window=64_000,
        available=False,
    )


def _loaded_router() -> ProviderModelRouter:
    router = ProviderModelRouter()
    for m in [_gemini_pro(), _gemini_flash(), _openai_gpt4(), _openai_gpt35(), _local_model(), _unavailable_model()]:
        router.register(m)
    return router


# ---------------------------------------------------------------------------
# ProviderModel tests
# ---------------------------------------------------------------------------

class TestProviderModel:
    def test_full_id(self):
        m = _gemini_pro()
        assert m.full_id == "gemini/gemini-3-pro"

    def test_has_capability_true(self):
        assert _gemini_pro().has_capability("reasoning")

    def test_has_capability_false(self):
        assert not _local_model().has_capability("reasoning")

    def test_to_dict(self):
        d = _gemini_pro().to_dict()
        assert d["provider_id"] == "gemini"
        assert d["full_id"] == "gemini/gemini-3-pro"
        assert d["available"] is True
        assert isinstance(d["capabilities"], list)


# ---------------------------------------------------------------------------
# TaskRequirements tests
# ---------------------------------------------------------------------------

class TestTaskRequirements:
    def test_defaults(self):
        req = TaskRequirements()
        assert req.task_type == ""
        assert req.required_capabilities == []
        assert req.complexity == Complexity.MEDIUM
        assert req.preferred_provider is None
        assert req.preferred_model is None

    def test_to_dict(self):
        req = TaskRequirements(task_type="debugging", preferred_provider="gemini")
        d = req.to_dict()
        assert d["task_type"] == "debugging"
        assert d["preferred_provider"] == "gemini"
        assert d["max_cost_tier"] is None


# ---------------------------------------------------------------------------
# RoutingDecision tests
# ---------------------------------------------------------------------------

class TestRoutingDecision:
    def test_success_true(self):
        d = RoutingDecision(selected=_gemini_pro(), candidates=[], policy_used="test")
        assert d.success is True

    def test_success_false(self):
        d = RoutingDecision(selected=None, candidates=[], policy_used="test")
        assert d.success is False

    def test_to_dict_with_selection(self):
        d = RoutingDecision(
            selected=_gemini_flash(),
            candidates=[_gemini_flash()],
            policy_used="low_cost",
            reasons=["cheapest"],
        )
        result = d.to_dict()
        assert result["success"] is True
        assert result["selected"]["model_id"] == "gemini-2-flash"
        assert result["policy_used"] == "low_cost"

    def test_to_dict_no_selection(self):
        d = RoutingDecision(selected=None, candidates=[], policy_used="test")
        result = d.to_dict()
        assert result["success"] is False
        assert result["selected"] is None


# ---------------------------------------------------------------------------
# Router — model registration
# ---------------------------------------------------------------------------

class TestRouterRegistration:
    def test_register_and_resolve(self):
        router = ProviderModelRouter()
        router.register(_gemini_pro())
        resolved = router.resolve("gemini/gemini-3-pro")
        assert resolved is not None
        assert resolved.model_id == "gemini-3-pro"

    def test_resolve_nonexistent(self):
        router = ProviderModelRouter()
        assert router.resolve("nope/nope") is None

    def test_duplicate_rejected(self):
        router = ProviderModelRouter()
        router.register(_gemini_pro())
        with pytest.raises(ValueError, match="Duplicate model"):
            router.register(_gemini_pro())

    def test_len(self):
        router = ProviderModelRouter()
        assert len(router) == 0
        router.register(_gemini_pro())
        assert len(router) == 1

    def test_contains(self):
        router = ProviderModelRouter()
        router.register(_gemini_pro())
        assert "gemini/gemini-3-pro" in router
        assert "openai/gpt-4" not in router

    def test_list_all(self):
        router = _loaded_router()
        assert len(router.list_all()) == 6

    def test_list_available(self):
        router = _loaded_router()
        available = router.list_available()
        assert len(available) == 5
        ids = [m.full_id for m in available]
        assert "deepseek/deepseek-v3" not in ids


# ---------------------------------------------------------------------------
# Router — filtering
# ---------------------------------------------------------------------------

class TestRouterFiltering:
    def test_excludes_unavailable(self):
        router = _loaded_router()
        req = TaskRequirements(task_type="code_generation")
        decision = router.route(req)
        assert decision.selected is not None
        assert decision.selected.available is True
        assert any("unavailable" in r.lower() for r in decision.reasons)

    def test_filters_missing_capabilities(self):
        router = _loaded_router()
        req = TaskRequirements(
            task_type="analysis",
            required_capabilities=["reasoning", "multimodal"],
        )
        decision = router.route(req)
        assert decision.selected is not None
        assert decision.selected.model_id == "gemini-3-pro"
        assert decision.selected.has_capability("reasoning")
        assert decision.selected.has_capability("multimodal")

    def test_filters_context_window(self):
        router = _loaded_router()
        req = TaskRequirements(
            task_type="code_generation",
            min_context_window=150_000,
        )
        decision = router.route(req)
        assert decision.selected is not None
        assert decision.selected.context_window >= 150_000

    def test_filters_cost_tier(self):
        router = _loaded_router()
        req = TaskRequirements(
            task_type="code_generation",
            max_cost_tier=CostTier.LOW,
        )
        decision = router.route(req)
        assert decision.selected is not None
        assert decision.selected.cost_tier in (CostTier.FREE, CostTier.LOW)


# ---------------------------------------------------------------------------
# Router — preferences
# ---------------------------------------------------------------------------

class TestRouterPreferences:
    def test_preferred_provider(self):
        router = _loaded_router()
        req = TaskRequirements(
            task_type="code_generation",
            preferred_provider="openai",
        )
        decision = router.route(req)
        assert decision.selected is not None
        assert decision.selected.provider_id == "openai"

    def test_preferred_model(self):
        router = _loaded_router()
        req = TaskRequirements(
            task_type="code_generation",
            preferred_model="gpt-4",
        )
        decision = router.route(req)
        assert decision.selected is not None
        assert decision.selected.model_id == "gpt-4"

    def test_preferred_model_not_found_falls_back(self):
        router = _loaded_router()
        req = TaskRequirements(
            task_type="code_generation",
            preferred_model="nonexistent-model",
        )
        decision = router.route(req)
        assert decision.selected is not None
        assert any("falling back" in r.lower() for r in decision.reasons)

    def test_preferred_provider_not_found_falls_back(self):
        router = _loaded_router()
        req = TaskRequirements(
            task_type="code_generation",
            preferred_provider="nonexistent",
        )
        decision = router.route(req)
        assert decision.selected is not None
        assert any("falling back" in r.lower() for r in decision.reasons)


# ---------------------------------------------------------------------------
# Routing policies
# ---------------------------------------------------------------------------

class TestPolicies:
    def test_list_policies(self):
        policies = list_policies()
        assert "deterministic" in policies
        assert "low_cost" in policies
        assert "high_capability" in policies
        assert "balanced" in policies

    def test_get_policy(self):
        assert get_policy("deterministic") is not None
        assert get_policy("nonexistent") is None

    def test_deterministic_ranking(self):
        policy = DeterministicPolicy()
        models = [_openai_gpt4(), _gemini_pro(), _local_model()]
        ranked = policy.rank(models)
        ids = [m.full_id for m in ranked]
        assert ids == sorted(ids)

    def test_low_cost_ranking(self):
        policy = LowCostPolicy()
        models = [_gemini_pro(), _local_model(), _openai_gpt35()]
        ranked = policy.rank(models)
        assert ranked[0].cost_tier == CostTier.FREE
        assert ranked[1].cost_tier == CostTier.LOW
        assert ranked[2].cost_tier == CostTier.HIGH

    def test_high_capability_ranking(self):
        policy = HighCapabilityPolicy()
        models = [_local_model(), _openai_gpt35(), _gemini_pro()]
        ranked = policy.rank(models)
        assert ranked[0].model_id == "gemini-3-pro"

    def test_balanced_ranking(self):
        policy = BalancedPolicy()
        models = [_gemini_pro(), _gemini_flash(), _local_model()]
        ranked = policy.rank(models)
        assert len(ranked) == 3
        assert ranked[0].full_id in [m.full_id for m in models]


# ---------------------------------------------------------------------------
# Router — routing with each policy
# ---------------------------------------------------------------------------

class TestRouterPolicyRouting:
    def test_route_deterministic(self):
        router = _loaded_router()
        req = TaskRequirements(task_type="code_generation")
        decision = router.route(req, policy_id="deterministic")
        assert decision.policy_used == "deterministic"
        assert decision.success

    def test_route_low_cost(self):
        router = _loaded_router()
        req = TaskRequirements(task_type="code_generation")
        decision = router.route(req, policy_id="low_cost")
        assert decision.policy_used == "low_cost"
        assert decision.success
        assert decision.selected.cost_tier in (CostTier.FREE, CostTier.LOW)

    def test_route_high_capability(self):
        router = _loaded_router()
        req = TaskRequirements(task_type="code_generation")
        decision = router.route(req, policy_id="high_capability")
        assert decision.policy_used == "high_capability"
        assert decision.success

    def test_route_balanced(self):
        router = _loaded_router()
        req = TaskRequirements(task_type="code_generation")
        decision = router.route(req, policy_id="balanced")
        assert decision.policy_used == "balanced"
        assert decision.success

    def test_default_policy(self):
        router = ProviderModelRouter(default_policy="low_cost")
        router.register(_gemini_pro())
        router.register(_local_model())
        req = TaskRequirements(task_type="code_generation")
        decision = router.route(req)
        assert decision.policy_used == "low_cost"
        assert decision.selected.model_id == "codellama-7b"


# ---------------------------------------------------------------------------
# Router — no compatible model
# ---------------------------------------------------------------------------

class TestNoCompatibleModel:
    def test_no_match_all_unavailable(self):
        router = ProviderModelRouter()
        router.register(_unavailable_model())
        req = TaskRequirements(task_type="code_generation")
        decision = router.route(req)
        assert not decision.success
        assert decision.selected is None

    def test_no_match_capabilities(self):
        router = _loaded_router()
        req = TaskRequirements(
            task_type="unknown",
            required_capabilities=["nonexistent_capability"],
        )
        decision = router.route(req)
        assert not decision.success
        assert decision.selected is None

    def test_no_match_cost_filter(self):
        router = ProviderModelRouter()
        router.register(_gemini_pro())
        req = TaskRequirements(
            task_type="code_generation",
            max_cost_tier=CostTier.FREE,
        )
        decision = router.route(req)
        assert not decision.success


# ---------------------------------------------------------------------------
# Backward compatibility — orchestrator unchanged
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_orchestrator_still_works(self):
        from runtime.agents.placeholder import ALL_PLACEHOLDER_AGENTS
        from runtime.core.orchestrator import EngineeringOrchestrator
        from runtime.core.result import AgentStatus
        from runtime.core.task import Task

        orch = EngineeringOrchestrator(agents=ALL_PLACEHOLDER_AGENTS)
        task = Task(title="Test", objective="Obj", task_type="project_analysis")
        orch.accept_task(task)
        result = orch.execute(task)
        assert result.status == AgentStatus.SUCCESS
        orch.complete_task(task)
        assert task.status.value == "COMPLETED"

    def test_adapter_agents_still_work(self):
        from runtime.adapters.adapter_agent import AdapterAgent
        from runtime.adapters.base import AdapterCapability, AgentAdapter
        from runtime.core.orchestrator import EngineeringOrchestrator
        from runtime.core.result import AgentResult, AgentStatus
        from runtime.core.task import Task

        class LocalTestAdapter(AgentAdapter):
            adapter_id = "local-test"
            name = "Local Test Adapter"

            def check_availability(self) -> bool:
                return True

            def capabilities(self) -> AdapterCapability:
                return AdapterCapability(
                    task_types=["debugging"],
                    supports_dry_run=True,
                    supports_modification=False,
                )

            def execute(
                self,
                task: Task,
                dry_run: bool = False,
            ) -> AgentResult:
                return AgentResult(
                    status=AgentStatus.SUCCESS,
                    summary="Local adapter executed successfully",
                )

        agent = AdapterAgent(LocalTestAdapter())
        orch = EngineeringOrchestrator(agents={agent.agent_id: agent})
        task = Task(title="T", objective="O", task_type="debugging")
        orch.accept_task(task)
        result = orch.execute(task)
        assert result.status == AgentStatus.SUCCESS

    def test_routing_layer_independent(self):
        router = _loaded_router()
        req = TaskRequirements(
            task_type="code_generation",
            required_capabilities=["code_generation"],
            preferred_provider="gemini",
        )
        decision = router.route(req)
        assert decision.success
        assert decision.selected.provider_id == "gemini"
