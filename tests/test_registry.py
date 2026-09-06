"""Tests for runtime/core/registry.py"""

from pathlib import Path

from runtime.core.registry import (
    AgentRecord,
    AgentRegistry,
    parse_registry,
)

SAMPLE_REGISTRY = """# Phoenix AI Engineering — Agent Registry

## Registered Agents

### ANALYSIS-001 — Project Analysis Agent
- category: analysis
- status: planned
- primary_responsibility: Analyze project architecture.
- allowed_task_types: project_analysis, architecture_analysis
- modification_permission: no
- review_permission: yes
- specification_path: agents/analysis/project-analysis-agent.md

### DEBUG-001 — Code Debugging Agent
- category: development
- status: planned
- primary_responsibility: Diagnose defects.
- allowed_task_types: debugging, bug_fixing
- modification_permission: yes
- review_permission: no
- specification_path: agents/development/code-debugging-agent.md
"""


def test_parse_registry_agents_count():
    registry = parse_registry(SAMPLE_REGISTRY)
    assert len(registry) == 2


def test_parse_registry_agent_ids():
    registry = parse_registry(SAMPLE_REGISTRY)
    assert "ANALYSIS-001" in registry
    assert "DEBUG-001" in registry


def test_parse_registry_agent_fields():
    registry = parse_registry(SAMPLE_REGISTRY)
    analysis = registry.get("ANALYSIS-001")
    assert analysis is not None
    assert analysis.name == "Project Analysis Agent"
    assert analysis.category == "analysis"
    assert analysis.modification_permission is False
    assert analysis.review_permission is True
    assert analysis.allowed_task_types == ["project_analysis", "architecture_analysis"]


def test_parse_registry_debug_agent():
    registry = parse_registry(SAMPLE_REGISTRY)
    debug = registry.get("DEBUG-001")
    assert debug is not None
    assert debug.modification_permission is True
    assert debug.review_permission is False
    assert "debugging" in debug.allowed_task_types


def test_registry_get_by_category():
    registry = parse_registry(SAMPLE_REGISTRY)
    dev = registry.get_by_category("development")
    assert len(dev) == 1
    assert dev[0].agent_id == "DEBUG-001"


def test_registry_get_by_task_type():
    registry = parse_registry(SAMPLE_REGISTRY)
    agents = registry.get_by_task_type("debugging")
    assert len(agents) == 1
    assert agents[0].agent_id == "DEBUG-001"


def test_registry_get_modifiable_agents():
    registry = parse_registry(SAMPLE_REGISTRY)
    mods = registry.get_modifiable_agents()
    assert len(mods) == 1
    assert mods[0].agent_id == "DEBUG-001"


def test_registry_all_ids():
    registry = parse_registry(SAMPLE_REGISTRY)
    ids = registry.all_ids()
    assert ids == ["ANALYSIS-001", "DEBUG-001"]


def test_registry_contains():
    registry = parse_registry(SAMPLE_REGISTRY)
    assert "ANALYSIS-001" in registry
    assert "NONEXISTENT" not in registry


def test_parse_registry_empty():
    registry = parse_registry("# No agents\n")
    assert len(registry) == 0


def test_load_from_file():
    path = Path("agents/agent-registry.md")
    if path.exists():
        from runtime.core.registry import load_registry_from_file

        registry = load_registry_from_file(path)
        assert len(registry) > 0
        assert "ANALYSIS-001" in registry
