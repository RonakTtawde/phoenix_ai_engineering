"""Minimal Engineering Orchestrator per shared/contracts/orchestration-contract.md."""

from __future__ import annotations

from dataclasses import dataclass, field

from runtime.agents.base import BaseAgent
from runtime.core.result import AgentResult, AgentStatus
from runtime.core.task import Task, TaskStatus


@dataclass
class OrchestratorState:
    tasks: dict[str, Task] = field(default_factory=dict)
    results: dict[str, AgentResult] = field(default_factory=dict)
    execution_log: list[dict] = field(default_factory=list)


class EngineeringOrchestrator:
    """Minimal orchestrator that routes tasks to registered agents."""

    def __init__(self, agents: dict[str, BaseAgent]) -> None:
        self.agents = agents
        self.state = OrchestratorState()

    def accept_task(self, task: Task) -> None:
        self.state.tasks[task.task_id] = task
        self._log(task.task_id, "TASK_ACCEPTED", f"Task '{task.title}' accepted")
        if task.status == TaskStatus.BACKLOG:
            task.transition(TaskStatus.READY)

    def select_agent(self, task: Task) -> BaseAgent | None:
        assigned = task.assignment.assigned_agent
        if assigned and assigned in self.agents:
            return self.agents[assigned]

        for agent in self.agents.values():
            if agent.can_handle(task.category()):
                return agent

        for agent in self.agents.values():
            for task_type in task.acceptance_criteria:
                if agent.can_handle(task_type):
                    return agent

        return None

    def execute(self, task: Task) -> AgentResult:
        agent = self.select_agent(task)
        if agent is None:
            result = AgentResult(
                status=AgentStatus.FAILED,
                summary=f"No agent found for task '{task.title}'",
                recommended_next_action="Assign an agent manually",
            )
            self.state.results[task.task_id] = result
            self._log(task.task_id, "ROUTING_FAILED", "No matching agent found")
            return result

        task.assignment.assigned_agent = agent.agent_id
        task.transition(TaskStatus.IN_PROGRESS)
        self._log(
            task.task_id,
            "AGENT_ASSIGNED",
            f"Assigned to {agent.agent_id} ({agent.name})",
        )

        input_errors = agent.validate_inputs(task)
        if input_errors:
            result = AgentResult(
                status=AgentStatus.FAILED,
                summary=f"Input validation failed: {'; '.join(input_errors)}",
                blockers=input_errors,
            )
            self.state.results[task.task_id] = result
            task.transition(TaskStatus.FAILED)
            self._log(task.task_id, "VALIDATION_FAILED", str(input_errors))
            return result

        result = agent.execute(task)
        result.agent_id = agent.agent_id
        self.state.results[task.task_id] = result

        if result.status == AgentStatus.SUCCESS:
            task.execution_evidence.work_summary = result.summary
            task.execution_evidence.validation_results = result.validation_results
            task.execution_evidence.artifacts_changed = result.artifacts
            task.transition(TaskStatus.IN_REVIEW)
            self._log(task.task_id, "EXECUTION_SUCCESS", result.summary)
        elif result.status == AgentStatus.BLOCKED:
            task.execution_evidence.known_issues = result.blockers
            task.transition(TaskStatus.BLOCKED)
            self._log(task.task_id, "EXECUTION_BLOCKED", str(result.blockers))
        elif result.status == AgentStatus.PARTIAL_SUCCESS:
            task.execution_evidence.work_summary = result.summary
            task.transition(TaskStatus.IN_REVIEW)
            self._log(task.task_id, "EXECUTION_PARTIAL", result.summary)
        else:
            task.transition(TaskStatus.FAILED)
            self._log(task.task_id, "EXECUTION_FAILED", result.summary)

        return result

    def complete_task(self, task: Task) -> None:
        if task.status == TaskStatus.IN_REVIEW:
            task.transition(TaskStatus.COMPLETED)
            self._log(task.task_id, "TASK_COMPLETED", "Review passed, task completed")

    def get_task(self, task_id: str) -> Task | None:
        return self.state.tasks.get(task_id)

    def get_result(self, task_id: str) -> AgentResult | None:
        return self.state.results.get(task_id)

    def get_handoff(self, task_id: str) -> dict | None:
        task = self.state.tasks.get(task_id)
        if task is None:
            return None
        handoff = task.to_handoff()
        result = self.state.results.get(task_id)
        if result:
            handoff["recommended_next_agent"] = (
                result.recommended_next_action or None
            )
        return handoff

    def _log(self, task_id: str, event: str, detail: str) -> None:
        self.state.execution_log.append(
            {"task_id": task_id, "event": event, "detail": detail}
        )
