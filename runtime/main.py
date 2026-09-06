"""Runnable CLI entry point demonstrating one complete task lifecycle."""

from __future__ import annotations

import json
import sys

from runtime.agents.placeholder import ALL_PLACEHOLDER_AGENTS
from runtime.core.orchestrator import EngineeringOrchestrator
from runtime.core.task import Task, TaskPriority, TaskStatus


def run_demo() -> None:
    print("=" * 60)
    print("Phoenix AI Engineering — MVP Runtime Demo")
    print("=" * 60)

    orchestrator = EngineeringOrchestrator(agents=ALL_PLACEHOLDER_AGENTS)
    print(f"\nRegistered agents: {list(ALL_PLACEHOLDER_AGENTS.keys())}")

    task = Task(
        title="Analyze authentication module",
        task_type="project_analysis",
        objective="Identify architecture patterns and security risks in auth module",
        description="Review the authentication module for compliance with security standards.",
        priority=TaskPriority.HIGH,
        acceptance_criteria=[
            "architecture reviewed",
            "dependencies mapped",
            "risks identified",
        ],
    )
    print(f"\nCreated task: {task.task_id}")
    print(f"  Title: {task.title}")
    print(f"  Type: {task.task_type}")
    print(f"  Status: {task.status.value}")

    orchestrator.accept_task(task)
    print(f"\nAfter accept: status={task.status.value}")

    result = orchestrator.execute(task)
    print(f"\nExecution result:")
    print(f"  Status: {result.status.value}")
    print(f"  Summary: {result.summary}")
    print(f"  Artifacts: {result.artifacts}")
    print(f"  Validation: {result.validation_results}")
    print(f"  Agent: {result.agent_id}")

    orchestrator.complete_task(task)
    print(f"\nAfter complete: status={task.status.value}")

    handoff = orchestrator.get_handoff(task.task_id)
    print(f"\nHandoff record:")
    print(json.dumps(handoff, indent=2))

    print(f"\nExecution log:")
    for entry in orchestrator.state.execution_log:
        print(f"  [{entry['event']}] {entry['detail']}")

    print("\n" + "=" * 60)
    print("Demo complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
