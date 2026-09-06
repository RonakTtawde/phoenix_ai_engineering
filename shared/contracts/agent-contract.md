# Phoenix AI Engineering — Agent Contract

## 1. Agent Identity
Every agent must have:
- agent_id
- name
- category
- version
- description

## 2. Mission
The agent must have one clearly defined responsibility and must not perform unrelated work.

## 3. Inputs
Every agent must explicitly declare:
- project context
- task definition
- relevant files
- constraints
- acceptance criteria

## 4. Outputs
Every agent must return:
- status
- summary
- artifacts created or modified
- validation results
- blockers
- recommended next action

## 5. Execution Rules
Every agent must:
- inspect before modifying
- avoid unnecessary changes
- preserve existing architecture
- follow project conventions
- work only within authorized scope
- validate its own output

## 6. Safety Rules
An agent must not:
- delete project data without explicit authorization
- overwrite unrelated work
- modify secrets or credentials
- bypass tests or quality gates
- claim success without verification

## 7. Completion States
Allowed states:
- SUCCESS
- PARTIAL_SUCCESS
- BLOCKED
- FAILED
- NEEDS_REVIEW

## 8. Handoff
Every completed task must provide sufficient context for another agent to continue the work without rediscovering the entire project.
