"""Tests for the adapter layer: registry, OpenCode adapter, AdapterAgent, and backward compat."""

import pytest

from runtime.adapters.base import AdapterCapability, AgentAdapter
from runtime.adapters.registry import AdapterRegistry
from runtime.adapters.opencode import OpenCodeAdapter
from runtime.adapters.adapter_agent import AdapterAgent
from runtime.core.result import AgentResult, AgentStatus
from runtime.core.task import Task, TaskPriority, TaskStatus


# ---------------------------------------------------------------------------
# Stub adapter for testing
# ---------------------------------------------------------------------------

class StubAdapter(AgentAdapter):
    adapter_id = "stub"
    name = "Stub Adapter"

    def check_availability(self) -> bool:
        return True

    def capabilities(self) -> AdapterCapability:
        return AdapterCapability(
            task_types=["testing", "stub_work"],
            description="Test stub",
            supports_dry_run=True,
            supports_modification=False,
        )

    def execute(self, task: Task, dry_run: bool = False) -> AgentResult:
        return AgentResult(
            status=AgentStatus.SUCCESS,
            summary=f"Stub executed: {task.title}",
            artifacts=["stub-output.txt"],
            validation_results=["stub validation passed"],
        )


class UnavailableAdapter(AgentAdapter):
    adapter_id = "unavailable"
    name = "Unavailable Adapter"

    def check_availability(self) -> bool:
        return False

    def capabilities(self) -> AdapterCapability:
        return AdapterCapability(task_types=["impossible"])

    def execute(self, task: Task, dry_run: bool = False) -> AgentResult:
        return AgentResult(status=AgentStatus.FAILED, summary="Should not be called")


# ---------------------------------------------------------------------------
# AdapterRegistry tests
# ---------------------------------------------------------------------------

class TestAdapterRegistry:
    def test_register_adapter(self):
        reg = AdapterRegistry()
        reg.register(StubAdapter())
        assert len(reg) == 1
        assert "stub" in reg

    def test_duplicate_adapter_rejected(self):
        reg = AdapterRegistry()
        reg.register(StubAdapter())
        with pytest.raises(ValueError, match="Duplicate adapter ID"):
            reg.register(StubAdapter())

    def test_resolve_existing(self):
        reg = AdapterRegistry()
        stub = StubAdapter()
        reg.register(stub)
        assert reg.resolve("stub") is stub

    def test_resolve_nonexistent(self):
        reg = AdapterRegistry()
        assert reg.resolve("nope") is None

    def test_list_all(self):
        reg = AdapterRegistry()
        reg.register(StubAdapter())
        reg.register(UnavailableAdapter())
        assert len(reg.list_all()) == 2

    def test_list_available(self):
        reg = AdapterRegistry()
        reg.register(StubAdapter())
        reg.register(UnavailableAdapter())
        available = reg.list_available()
        assert len(available) == 1
        assert available[0].adapter_id == "stub"

    def test_list_by_capability(self):
        reg = AdapterRegistry()
        reg.register(StubAdapter())
        reg.register(UnavailableAdapter())
        by_type = reg.list_by_capability("testing")
        assert len(by_type) == 1
        assert by_type[0].adapter_id == "stub"

    def test_all_ids_sorted(self):
        reg = AdapterRegistry()
        reg.register(UnavailableAdapter())
        reg.register(StubAdapter())
        assert reg.all_ids() == ["stub", "unavailable"]

    def test_contains(self):
        reg = AdapterRegistry()
        reg.register(StubAdapter())
        assert "stub" in reg
        assert "missing" not in reg


# ---------------------------------------------------------------------------
# OpenCodeAdapter tests
# ---------------------------------------------------------------------------

class TestOpenCodeAdapter:
    def test_adapter_id(self):
        adapter = OpenCodeAdapter()
        assert adapter.adapter_id == "opencode"

    def test_capabilities(self):
        caps = OpenCodeAdapter().capabilities()
        assert "debugging" in caps.task_types
        assert caps.supports_dry_run is True
        assert caps.supports_modification is True

    def test_availability_detection(self):
        adapter = OpenCodeAdapter()
        result = adapter.check_availability()
        assert isinstance(result, bool)

    def test_dry_run_returns_success(self):
        adapter = OpenCodeAdapter()
        task = Task(title="Test", objective="Test obj", task_type="debugging")
        result = adapter.execute(task, dry_run=True)
        assert result.status == AgentStatus.SUCCESS
        assert "[DRY RUN]" in result.summary
        assert "dry-run completed" in result.validation_results

    def test_can_handle(self):
        adapter = OpenCodeAdapter()
        assert adapter.can_handle("debugging")
        assert adapter.can_handle("code_generation")
        assert not adapter.can_handle("nonexistent_type")

    def test_build_task_context(self):
        adapter = OpenCodeAdapter()
        task = Task(
            title="T",
            objective="O",
            task_type="testing",
            relevant_files=["a.py"],
            constraints=__import__("runtime.core.task", fromlist=["Constraints"]).Constraints(
                architecture_constraints=["no-sql"]
            ),
        )
        context = adapter._build_task_context(task)
        assert context["task_id"] == task.task_id
        assert context["relevant_files"] == ["a.py"]
        assert context["constraints"]["architecture"] == ["no-sql"]


# ---------------------------------------------------------------------------
# AdapterAgent tests
# ---------------------------------------------------------------------------

class TestAdapterAgent:
    def test_wraps_adapter(self):
        agent = AdapterAgent(StubAdapter())
        assert agent.agent_id == "adapter:stub"
        assert agent.name == "Stub Adapter"
        assert agent.category == "adapter"
        assert "testing" in agent.allowed_task_types

    def test_execute_delegates_to_adapter(self):
        agent = AdapterAgent(StubAdapter())
        task = Task(title="T", objective="O", task_type="testing")
        result = agent.execute(task)
        assert result.status == AgentStatus.SUCCESS
        assert "Stub executed" in result.summary

    def test_execute_dry_run(self):
        agent = AdapterAgent(StubAdapter())
        task = Task(title="T", objective="O", task_type="testing")
        result = agent.execute_dry_run(task)
        assert result.status == AgentStatus.SUCCESS

    def test_unavailable_adapter_blocked(self):
        agent = AdapterAgent(UnavailableAdapter())
        task = Task(title="T", objective="O", task_type="impossible")
        result = agent.execute(task)
        assert result.status == AgentStatus.BLOCKED

    def test_can_handle(self):
        agent = AdapterAgent(StubAdapter())
        assert agent.can_handle("testing")
        assert not agent.can_handle("nonexistent")


# ---------------------------------------------------------------------------
# Backward compatibility — orchestrator works unchanged with placeholder agents
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_orchestrator_with_placeholder_agents(self):
        from runtime.agents.placeholder import ALL_PLACEHOLDER_AGENTS
        from runtime.core.orchestrator import EngineeringOrchestrator

        orch = EngineeringOrchestrator(agents=ALL_PLACEHOLDER_AGENTS)
        task = Task(title="Analyze", objective="Analyze code", task_type="project_analysis")
        orch.accept_task(task)
        result = orch.execute(task)
        assert result.status == AgentStatus.SUCCESS
        orch.complete_task(task)
        assert task.status == TaskStatus.COMPLETED

    def test_orchestrator_with_adapter_agents(self):
        from runtime.agents.placeholder import PlaceholderAnalysisAgent
        from runtime.core.orchestrator import EngineeringOrchestrator

        agents = {
            "ANALYSIS-001": PlaceholderAnalysisAgent(),
            "adapter:stub": AdapterAgent(StubAdapter()),
        }
        orch = EngineeringOrchestrator(agents=agents)

        task = Task(title="Stub work", objective="Do stub", task_type="stub_work")
        orch.accept_task(task)
        result = orch.execute(task)
        assert result.status == AgentStatus.SUCCESS
        assert result.agent_id == "adapter:stub"

    def test_orchestrator_mixed_agents(self):
        from runtime.agents.placeholder import (
            PlaceholderAnalysisAgent,
            PlaceholderDebuggingAgent,
        )
        from runtime.core.orchestrator import EngineeringOrchestrator

        agents = {
            "ANALYSIS-001": PlaceholderAnalysisAgent(),
            "DEBUG-001": PlaceholderDebuggingAgent(),
            "adapter:stub": AdapterAgent(StubAdapter()),
        }
        orch = EngineeringOrchestrator(agents=agents)

        t1 = Task(title="Analyze", objective="A", task_type="project_analysis")
        orch.accept_task(t1)
        r1 = orch.execute(t1)
        assert r1.agent_id == "ANALYSIS-001"

        t2 = Task(title="Stub", objective="S", task_type="stub_work")
        orch.accept_task(t2)
        r2 = orch.execute(t2)
        assert r2.agent_id == "adapter:stub"

        t3 = Task(title="Debug", objective="D", task_type="debugging")
        orch.accept_task(t3)
        r3 = orch.execute(t3)
        assert r3.agent_id == "DEBUG-001"


# ---------------------------------------------------------------------------
# Integration: registry + adapter agent + orchestrator
# ---------------------------------------------------------------------------

class TestAdapterIntegration:
    def test_full_adapter_pipeline(self):
        reg = AdapterRegistry()
        reg.register(StubAdapter())
        reg.register(UnavailableAdapter())

        assert len(reg) == 2
        assert reg.list_available() == [reg.resolve("stub")]

        adapter = reg.resolve("stub")
        agent = AdapterAgent(adapter)

        from runtime.core.orchestrator import EngineeringOrchestrator

        orch = EngineeringOrchestrator(agents={agent.agent_id: agent})
        task = Task(title="Pipeline test", objective="Full pipeline", task_type="testing")
        orch.accept_task(task)
        result = orch.execute(task)
        assert result.status == AgentStatus.SUCCESS
        orch.complete_task(task)
        assert task.status == TaskStatus.COMPLETED
