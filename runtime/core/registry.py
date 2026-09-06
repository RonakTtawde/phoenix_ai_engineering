"""Agent registry loader. Parses agents/agent-registry.md into structured records."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_REGISTRY_PATH = Path("agents/agent-registry.md")


@dataclass
class AgentRecord:
    agent_id: str
    name: str
    category: str
    status: str
    primary_responsibility: str
    allowed_task_types: list[str]
    modification_permission: bool
    review_permission: bool
    specification_path: str


@dataclass
class AgentRegistry:
    agents: dict[str, AgentRecord] = field(default_factory=dict)

    def get(self, agent_id: str) -> AgentRecord | None:
        return self.agents.get(agent_id)

    def get_by_category(self, category: str) -> list[AgentRecord]:
        return [a for a in self.agents.values() if a.category == category]

    def get_by_task_type(self, task_type: str) -> list[AgentRecord]:
        return [a for a in self.agents.values() if task_type in a.allowed_task_types]

    def get_modifiable_agents(self) -> list[AgentRecord]:
        return [a for a in self.agents.values() if a.modification_permission]

    def all_ids(self) -> list[str]:
        return sorted(self.agents.keys())

    def __len__(self) -> int:
        return len(self.agents)

    def __contains__(self, agent_id: str) -> bool:
        return agent_id in self.agents


def _parse_bool(value: str) -> bool:
    return value.strip().lower() == "yes"


def _parse_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_registry(text: str) -> AgentRegistry:
    registry = AgentRegistry()
    agent_blocks = re.split(r"^### ", text, flags=re.MULTILINE)

    for block in agent_blocks:
        if not block.strip():
            continue

        header_match = re.match(r"(\S+)\s*[—–-]\s*(.+)", block)
        if not header_match:
            continue

        agent_id = header_match.group(1).strip()
        name = header_match.group(2).strip()

        fields: dict[str, str] = {}
        for line in block.splitlines():
            line = line.strip()
            kv = re.match(r"^-\s+(\w+):\s*(.+)$", line)
            if kv:
                fields[kv.group(1)] = kv.group(2)

        allowed = []
        raw_types = fields.get("allowed_task_types", "")
        if raw_types:
            allowed = _parse_list(raw_types)

        record = AgentRecord(
            agent_id=agent_id,
            name=name,
            category=fields.get("category", ""),
            status=fields.get("status", ""),
            primary_responsibility=fields.get("primary_responsibility", ""),
            allowed_task_types=allowed,
            modification_permission=_parse_bool(
                fields.get("modification_permission", "no")
            ),
            review_permission=_parse_bool(fields.get("review_permission", "no")),
            specification_path=fields.get("specification_path", ""),
        )
        registry.agents[agent_id] = record

    return registry


def load_registry_from_file(path: Path | str = _REGISTRY_PATH) -> AgentRegistry:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Agent registry not found: {p}")
    return parse_registry(p.read_text())
