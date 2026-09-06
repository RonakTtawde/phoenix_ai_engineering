"""OpenCode adapter — bridges the OpenCode CLI into the Phoenix adapter layer.

Detects whether the opencode CLI is available, reports capabilities,
supports safe dry-run mode, and returns results compatible with AgentResult.
"""

from __future__ import annotations

import shutil
import subprocess

from runtime.adapters.base import AdapterCapability, AgentAdapter
from runtime.core.result import AgentResult, AgentStatus
from runtime.core.task import Task

_OPENCODE_BIN = "opencode"

DESTRUCTIVE_COMMANDS = frozenset(
    {
        "rm",
        "delete",
        "remove",
        "drop",
        "truncate",
        "destroy",
        "purge",
        "force",
    }
)


class OpenCodeAdapter(AgentAdapter):
    adapter_id = "opencode"
    name = "OpenCode CLI Adapter"

    def check_availability(self) -> bool:
        return shutil.which(_OPENCODE_BIN) is not None

    def capabilities(self) -> AdapterCapability:
        return AdapterCapability(
            task_types=[
                "code_generation",
                "code_review",
                "refactoring",
                "debugging",
                "testing",
                "documentation",
                "analysis",
            ],
            description="OpenCode CLI coding agent",
            supports_dry_run=True,
            supports_modification=True,
        )

    def execute(self, task: Task, dry_run: bool = False) -> AgentResult:
        if not self.check_availability():
            return AgentResult(
                status=AgentStatus.BLOCKED,
                summary="opencode CLI not found on PATH",
                blockers=["opencode binary not available"],
                recommended_next_action="Install opencode or add to PATH",
            )

        if self._has_destructive_flags(task):
            return AgentResult(
                status=AgentStatus.BLOCKED,
                summary="Task contains destructive command flags",
                blockers=["Destructive operations are not permitted through adapter"],
                recommended_next_action="Request human approval for destructive operations",
            )

        if dry_run:
            return self._dry_run_result(task)

        return self._prepare_execution_result(task)

    def _has_destructive_flags(self, task: Task) -> bool:
        text = f"{task.objective} {task.description}".lower()
        return any(f"--{cmd}" in text or f"-{cmd}" in text for cmd in DESTRUCTIVE_COMMANDS)

    def _dry_run_result(self, task: Task) -> AgentResult:
        context = self._build_task_context(task)
        return AgentResult(
            status=AgentStatus.SUCCESS,
            summary=(
                f"[DRY RUN] OpenCode would execute: {task.title}\n"
                f"Objective: {task.objective}\n"
                f"Prepared context: {len(context)} fields"
            ),
            artifacts=[],
            validation_results=["dry-run completed", "no side effects"],
            recommended_next_action="Review prepared context, then execute for real",
        )

    def _prepare_execution_result(self, task: Task) -> AgentResult:
        context = self._build_task_context(task)
        return AgentResult(
            status=AgentStatus.SUCCESS,
            summary=(
                f"OpenCode execution prepared for: {task.title}\n"
                f"Context fields: {list(context.keys())}"
            ),
            artifacts=[],
            validation_results=["context prepared", "ready for real execution"],
            recommended_next_action="Execute opencode CLI with prepared context",
        )

    def _build_task_context(self, task: Task) -> dict:
        return {
            "task_id": task.task_id,
            "title": task.title,
            "objective": task.objective,
            "description": task.description,
            "task_type": task.task_type,
            "priority": task.priority.value,
            "acceptance_criteria": task.acceptance_criteria,
            "relevant_files": task.relevant_files,
            "constraints": {
                "architecture": task.constraints.architecture_constraints,
                "technology": task.constraints.technology_constraints,
                "security": task.constraints.security_constraints,
            },
        }
