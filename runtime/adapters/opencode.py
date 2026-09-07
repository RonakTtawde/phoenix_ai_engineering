"""OpenCode adapter — executes Phoenix engineering tasks through OpenCode CLI."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
from dataclasses import dataclass, field

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

DEFAULT_MODEL = "openrouter/cohere/north-mini-code:free"

ALLOWED_REPOSITORY_ROOTS = (
    pathlib.Path("/mnt/d"),
    pathlib.Path("/workspace"),
)


@dataclass
class OpenCodeConfig:
    """Runtime configuration for the OpenCode adapter."""

    model: str = DEFAULT_MODEL
    timeout_seconds: int = 300
    working_directory: str | None = None
    safety_restrictions: list[str] = field(default_factory=list)


class OpenCodeAdapter(AgentAdapter):
    adapter_id = "opencode"
    name = "OpenCode CLI Adapter"

    def __init__(self, config: OpenCodeConfig | None = None) -> None:
        self.config = config or OpenCodeConfig()

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
                recommended_next_action="Install OpenCode or add it to PATH",
            )

        if self._has_destructive_flags(task):
            return AgentResult(
                status=AgentStatus.BLOCKED,
                summary="Task contains prohibited destructive command flags",
                blockers=["Destructive operations are not permitted"],
                recommended_next_action="Request human approval and revise the task",
            )

        if dry_run:
            return self._dry_run_result(task)

        try:
            working_dir = self._get_working_directory(task)
            self._validate_repository_path(working_dir)
        except ValueError as exc:
            return AgentResult(
                status=AgentStatus.BLOCKED,
                summary=str(exc),
                blockers=[str(exc)],
                recommended_next_action="Configure a valid allowed repository path",
            )

        prompt = self._build_prompt(task)

        command = [
            _OPENCODE_BIN,
            "run",
            "--pure",
            "--auto",
            "-m",
            self.config.model,
            prompt,
        ]

        try:
            result = subprocess.run(
                command,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return AgentResult(
                status=AgentStatus.BLOCKED,
                summary=(
                    f"OpenCode execution timed out after "
                    f"{self.config.timeout_seconds} seconds"
                ),
                blockers=["Execution timeout"],
                recommended_next_action="Increase timeout or simplify the task",
            )
        except OSError as exc:
            return AgentResult(
                status=AgentStatus.FAILED,
                summary=f"Unable to start OpenCode: {exc}",
                blockers=[str(exc)],
                recommended_next_action="Check OpenCode installation and permissions",
            )

        return self._process_result(result, task, working_dir)

    def _has_destructive_flags(self, task: Task) -> bool:
        text = f"{task.objective} {task.description}".lower()
        return any(
            f"--{command}" in text
            for command in DESTRUCTIVE_COMMANDS
        )

    def _dry_run_result(self, task: Task) -> AgentResult:
        context = self._build_task_context(task)
        return AgentResult(
            status=AgentStatus.SUCCESS,
            summary=(
                f"[DRY RUN] OpenCode would execute: {task.title}\n"
                f"Objective: {task.objective}\n"
                f"Prepared context fields: {len(context)}"
            ),
            artifacts=[],
            validation_results=["dry-run completed", "no side effects"],
            recommended_next_action="Review the task and execute when approved",
        )

    def _get_working_directory(self, task: Task) -> str:
        if self.config.working_directory:
            return str(pathlib.Path(self.config.working_directory).resolve())

        if task.relevant_files:
            first_path = pathlib.Path(task.relevant_files[0]).resolve()
            return str(
                first_path
                if first_path.is_dir()
                else first_path.parent
            )

        return os.getcwd()

    def _validate_repository_path(self, working_dir: str) -> None:
        path = pathlib.Path(working_dir).resolve()

        if not path.is_dir():
            raise ValueError(
                f"Working directory does not exist: {path}"
            )

        if not any(
            path.is_relative_to(root)
            for root in ALLOWED_REPOSITORY_ROOTS
        ):
            allowed = ", ".join(
                str(root) for root in ALLOWED_REPOSITORY_ROOTS
            )
            raise ValueError(
                f"Working directory '{path}' is outside allowed roots: "
                f"{allowed}"
            )

    def _build_prompt(self, task: Task) -> str:
        safety_restrictions = "\n".join(
            f"- {item}"
            for item in self.config.safety_restrictions
        )

        if not safety_restrictions:
            safety_restrictions = "- No additional restrictions configured"

        return (
            "You are executing one Phoenix engineering task in the current "
            "repository.\n\n"
            f"Task: {task.title}\n"
            f"Objective: {task.objective}\n"
            f"Description: {task.description}\n"
            f"Task type: {task.task_type}\n"
            f"Acceptance criteria: {', '.join(task.acceptance_criteria) or 'None specified'}\n"
            f"Relevant files: {', '.join(task.relevant_files) or 'Inspect repository as needed'}\n\n"
            "Constraints:\n"
            f"- Architecture: {', '.join(task.constraints.architecture_constraints) or 'None'}\n"
            f"- Technology: {', '.join(task.constraints.technology_constraints) or 'None'}\n"
            f"- Security: {', '.join(task.constraints.security_constraints) or 'None'}\n"
            f"- Time: {', '.join(task.constraints.time_constraints) or 'None'}\n\n"
            "Additional safety restrictions:\n"
            f"{safety_restrictions}\n\n"
            "Rules:\n"
            "- Work only inside the current repository.\n"
            "- Do not delete unrelated files.\n"
            "- Do not modify files outside task scope.\n"
            "- Do not commit or push changes.\n"
            "- Inspect existing code before modifying it.\n"
            "- Run relevant validation after making changes.\n"
            "- Report what changed and validation results.\n"
        )

    def _process_result(
        self,
        result: subprocess.CompletedProcess[str],
        task: Task,
        working_dir: str,
    ) -> AgentResult:
        output = "\n".join(
            part for part in (result.stdout, result.stderr) if part
        ).strip()

        artifacts = self._collect_changed_files(working_dir)

        if result.returncode == 0:
            validation_results = [
                "OpenCode execution completed successfully",
            ]

            if output:
                validation_results.append(
                    "OpenCode produced execution output"
                )

            return AgentResult(
                status=AgentStatus.SUCCESS,
                summary=(
                    f"OpenCode completed task: {task.title}"
                    + (
                        f"\n\n{output}"
                        if output
                        else ""
                    )
                ),
                artifacts=artifacts,
                validation_results=validation_results,
                recommended_next_action=(
                    "Review changes and validation results"
                ),
            )

        return AgentResult(
            status=AgentStatus.FAILED,
            summary=(
                f"OpenCode failed with exit code {result.returncode} "
                f"for task: {task.title}"
                + (
                    f"\n\n{output}"
                    if output
                    else ""
                )
            ),
            artifacts=artifacts,
            validation_results=[
                f"OpenCode exited with code {result.returncode}"
            ],
            blockers=[
                "OpenCode execution failed"
            ],
            recommended_next_action=(
                "Review OpenCode output and correct the task or configuration"
            ),
        )

    def _collect_changed_files(self, working_dir: str) -> list[str]:
        if not self._is_git_repo(working_dir):
            return []

        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            return []

        if result.returncode != 0:
            return []

        return [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

    def _is_git_repo(self, working_dir: str) -> bool:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False

        return (
            result.returncode == 0
            and result.stdout.strip() == "true"
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
                "architecture": (
                    task.constraints.architecture_constraints
                ),
                "technology": (
                    task.constraints.technology_constraints
                ),
                "security": (
                    task.constraints.security_constraints
                ),
            },
        }
