# Agent Specification Template

## 1. Identity
- agent_id:
- name:
- category:
- version:
- description:

## 2. Mission
Define the single primary objective of this agent.

## 3. Responsibilities
List exactly what this agent is responsible for.

## 4. Non-Responsibilities
List what this agent must NOT do.

## 5. Inputs
- project_context:
- task:
- relevant_files:
- constraints:
- acceptance_criteria:

## 6. Outputs
- status:
- summary:
- artifacts:
- validation_results:
- blockers:
- recommended_next_action:

## 7. Permissions
### Allowed
- Read:
- Write:
- Execute:
- Network:

### Forbidden
- Unauthorized file deletion
- Secret or credential modification
- Changes outside assigned scope

## 8. Execution Workflow
1. Inspect assigned context.
2. Validate inputs.
3. Create an execution plan.
4. Perform only authorized work.
5. Validate results.
6. Return structured handoff.

## 9. Validation Rules
Define the checks required before the agent can report completion.

## 10. Escalation Rules
Define conditions that require handoff to another agent or the orchestrator.

## 11. Completion Criteria
Define measurable conditions for:
- SUCCESS
- PARTIAL_SUCCESS
- BLOCKED
- FAILED
- NEEDS_REVIEW

## 12. Handoff Contract
Every handoff must include:
- current status
- completed work
- changed artifacts
- validation evidence
- unresolved issues
- recommended next agent
