"""Structured agent execution result per shared/contracts/agent-contract.md §4 and §7."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AgentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass
class AgentResult:
    status: AgentStatus
    summary: str
    artifacts: list[str] = field(default_factory=list)
    validation_results: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    recommended_next_action: str = ""
    agent_id: str = ""

    def is_success(self) -> bool:
        return self.status in (AgentStatus.SUCCESS, AgentStatus.PARTIAL_SUCCESS)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "summary": self.summary,
            "artifacts": self.artifacts,
            "validation_results": self.validation_results,
            "blockers": self.blockers,
            "recommended_next_action": self.recommended_next_action,
        }
