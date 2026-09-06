"""Deterministic placeholder agents for MVP demonstration."""

from __future__ import annotations

from runtime.agents.base import BaseAgent
from runtime.core.result import AgentResult, AgentStatus
from runtime.core.task import Task


class PlaceholderAnalysisAgent(BaseAgent):
    agent_id = "ANALYSIS-001"
    name = "Project Analysis Agent"
    category = "analysis"
    allowed_task_types = [
        "project_analysis",
        "architecture_analysis",
        "dependency_analysis",
    ]
    modification_permission = False
    review_permission = True

    def execute(self, task: Task) -> AgentResult:
        return AgentResult(
            status=AgentStatus.SUCCESS,
            summary=f"Analysis completed for '{task.title}'. Found 3 modules, 2 dependencies.",
            artifacts=["analysis-report.md"],
            validation_results=["architecture reviewed", "dependencies mapped"],
        )


class PlaceholderPlanningAgent(BaseAgent):
    agent_id = "PLANNING-001"
    name = "Project Task Management Agent"
    category = "planning"
    allowed_task_types = [
        "task_planning",
        "task_breakdown",
        "prioritization",
        "dependency_mapping",
    ]
    modification_permission = False
    review_permission = True

    def execute(self, task: Task) -> AgentResult:
        return AgentResult(
            status=AgentStatus.SUCCESS,
            summary=f"Task plan created for '{task.title}'. 4 tasks generated.",
            artifacts=["task-plan.md"],
            validation_results=["dependencies resolved", "priorities assigned"],
        )


class PlaceholderDebuggingAgent(BaseAgent):
    agent_id = "DEBUG-001"
    name = "Code Debugging Agent"
    category = "development"
    allowed_task_types = ["debugging", "bug_fixing", "defect_analysis"]
    modification_permission = True
    review_permission = False

    def execute(self, task: Task) -> AgentResult:
        return AgentResult(
            status=AgentStatus.SUCCESS,
            summary=f"Defect resolved for '{task.title}'. Root cause identified and fixed.",
            artifacts=["fix.patch"],
            validation_results=["tests pass", "no regressions"],
        )


class PlaceholderBackendAgent(BaseAgent):
    agent_id = "BACKEND-001"
    name = "Backend Development Agent"
    category = "development"
    allowed_task_types = ["backend_development", "service_development"]
    modification_permission = True
    review_permission = False

    def execute(self, task: Task) -> AgentResult:
        return AgentResult(
            status=AgentStatus.SUCCESS,
            summary=f"Backend work completed for '{task.title}'.",
            artifacts=["service.py"],
            validation_results=["unit tests pass", "integration tests pass"],
        )


ALL_PLACEHOLDER_AGENTS: dict[str, BaseAgent] = {
    a.agent_id: a
    for a in [
        PlaceholderAnalysisAgent(),
        PlaceholderPlanningAgent(),
        PlaceholderDebuggingAgent(),
        PlaceholderBackendAgent(),
    ]
}
