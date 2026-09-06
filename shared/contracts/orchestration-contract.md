# Phoenix AI Engineering — Orchestration Contract

## 1. Orchestrator Authority
The Orchestrator is responsible for:
- receiving or selecting tasks
- analyzing task requirements
- selecting the appropriate agent or agents
- assigning execution order
- managing dependencies
- coordinating handoffs
- enforcing validation and review gates
- determining final task status

## 2. Agent Execution Model
Agents do not independently expand their assigned scope.

Every agent must:
1. receive an explicit task
2. validate task inputs
3. execute only within assigned scope
4. produce execution evidence
5. report completion or blockage
6. hand control back to the Orchestrator

## 3. Task Routing
The Orchestrator determines:
- primary execution agent
- supporting agents
- reviewer agent
- execution sequence
- retry strategy when validation fails

## 4. Modification Ownership
For each task, the Orchestrator must define ownership of:
- files
- modules
- services
- infrastructure resources

Only the assigned execution agent may modify owned artifacts during an active task unless the Orchestrator explicitly reassigns ownership.

## 5. Validation Gates
A task follows this lifecycle:

BACKLOG
→ READY
→ IN_PROGRESS
→ VALIDATION
→ IN_REVIEW
→ COMPLETED

If validation fails:

VALIDATION
→ BLOCKED or IN_PROGRESS

## 6. Handoff Rules
Every handoff must include:
- task_id
- current_status
- completed_work
- changed_artifacts
- validation_evidence
- blockers
- remaining_work
- recommended_next_agent

## 7. Agent Conflict Resolution
If agents produce conflicting recommendations or changes:

1. Stop conflicting execution.
2. Preserve evidence from each agent.
3. Return the conflict to the Orchestrator.
4. Re-evaluate task scope and acceptance criteria.
5. Assign a single decision or reviewer agent.

## 8. Failure Handling
When an agent fails:

- record the failure
- preserve logs and evidence
- determine whether retry is appropriate
- avoid repeating the same failed strategy without change
- escalate when dependencies or requirements are unclear

## 9. Completion Authority
An execution agent cannot independently declare the overall workflow complete.

The Orchestrator may mark a task as COMPLETED only after:
- acceptance criteria are satisfied
- required validation passes
- required review passes
- evidence is recorded
- no blocking issue remains

## 10. Human Control
The human owner retains final authority.

The system must support human approval for:
- major architecture changes
- production deployments
- destructive operations
- security-sensitive changes
- scope expansion
