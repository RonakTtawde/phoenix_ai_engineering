# Phoenix AI Engineering — Agent Registry

## Registry Purpose

The Agent Registry is the central catalog of all available agents.

The Orchestrator uses this registry to determine:
- which agents are available
- each agent's responsibility
- whether the agent can modify artifacts
- which task categories it can accept
- which validation or review role it can perform

## Agent Entry Schema

Each registered agent must define:

- agent_id
- name
- category
- status
- primary_responsibility
- allowed_task_types
- modification_permission
- review_permission
- specification_path

## Registered Agents


### ORCH-001 — Engineering Orchestrator
- category: orchestration
- status: planned
- primary_responsibility: Coordinate tasks, agents, handoffs, validation, and workflow execution.
- allowed_task_types: orchestration, routing, coordination, escalation
- modification_permission: no
- review_permission: yes
- specification_path: orchestrator/engineering-orchestrator.md

### ANALYSIS-001 — Project Analysis Agent
- category: analysis
- status: planned
- primary_responsibility: Analyze project architecture, codebase, dependencies, risks, and current state.
- allowed_task_types: project_analysis, architecture_analysis, dependency_analysis
- modification_permission: no
- review_permission: yes
- specification_path: agents/analysis/project-analysis-agent.md

### PLANNING-001 — Project Task Management Agent
- category: planning
- status: planned
- primary_responsibility: Convert requirements and findings into structured, prioritized, dependency-aware tasks.
- allowed_task_types: task_planning, task_breakdown, prioritization, dependency_mapping
- modification_permission: no
- review_permission: yes
- specification_path: agents/planning/project-task-management-agent.md

### DEBUG-001 — Code Debugging Agent
- category: development
- status: planned
- primary_responsibility: Diagnose defects and implement minimal verified fixes within assigned scope.
- allowed_task_types: debugging, bug_fixing, defect_analysis
- modification_permission: yes
- review_permission: no
- specification_path: agents/development/code-debugging-agent.md

### BACKEND-001 — Backend Development Agent
- category: development
- status: planned
- primary_responsibility: Develop and modify backend services, business logic, persistence, and integrations.
- allowed_task_types: backend_development, service_development
- modification_permission: yes
- review_permission: no
- specification_path: agents/development/backend-development-agent.md

