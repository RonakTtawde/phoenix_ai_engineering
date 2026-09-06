# Phoenix AI Engineering — Agent Instructions

## Model Configuration

**CRITICAL ENFORCEMENT**: All agents MUST use Gemini models exclusively.
- Primary model: `gemini/gemini-3-pro-preview-pt`
- Small model: `gemini/gemini-2.0-flash`
- No other models (GPT-4, Claude, etc.) are permitted in this repository

## Principle 1: Gemini-Only with Built-in Tools

All operations MUST use Gemini models with built-in tools:
- Read/Write/Edit for file operations
- Bash for command execution (with permission controls)
- Task tool for subagent delegation
- Grep/Glob for code search

**Violation Prevention**:
- Never suggest or use non-Gemini models
- Never configure alternative providers
- All agent definitions in opencode.json must specify Gemini models

## Principle 2: Subagents for Heavy Lifting

The Orchestrator MUST delegate specialized work to subagents:

### Required Subagent Usage
| Task Type | Required Agent |
|-----------|----------------|
| Architecture analysis | `analysis` agent |
| Task planning | `planning` agent |
| Backend development | `backend` agent |
| Frontend development | `frontend` agent |
| Bug fixes | `debugging` agent |
| Infrastructure | `devops` agent |
| Test creation | `testing` agent |
| Code review | `reviewer` agent |

### Anti-Pattern Prevention
**GOTCHA**: Do not attempt to handle specialized tasks in the Orchestrator
**GOTCHA**: Do not skip the planning phase for complex tasks
**GOTCHA**: Do not implement code changes without review

## Principle 3: Parallel Execution and Real-time Monitoring

### Parallel Execution Patterns
- Use the `Task` tool for independent subagent operations
- Launch multiple agents concurrently when tasks are independent
- Use `rg --line-number` for streaming search results

### Monitoring Requirements
- Track agent execution status in real-time
- Log completion criteria for each subagent task
- Maintain execution evidence in workspace/retrospective-log.md

### Anti-Pattern Prevention
**GOTCHA**: Do not block on single agent when parallel execution is possible
**GOTCHA**: Do not skip monitoring of subagent progress
**GOTCHA**: Do not ignore streaming output for large searches

## Principle 4: Self-Improvement Feedback Loop

### Retrospective Requirements
After significant tasks, update `workspace/retrospective-log.md`:
- Document failures and root causes
- Record edge cases encountered
- Note process improvement suggestions
- Track efficiency metrics

### Efficiency Audit Requirements
Maintain `workspace/efficiency-audit.md` with:
- Task completion times
- Success/failure rates
- Resource utilization patterns
- Bottleneck identification

### Anti-Pattern Prevention
**GOTCHA**: Do not skip retrospective documentation
**GOTCHA**: Do not ignore recurring failure patterns
**GOTCHA**: Do not delay efficiency reviews

## Principle 5: Prevention of Anti-Patterns

### Universal Anti-Patterns
1. **Scope creep**: Never expand task scope without Orchestrator approval
2. **Secret exposure**: Never log or commit secrets/credentials
3. **Bypassing validation**: Never skip compliance checkpoints
4. **Unauthorized modifications**: Never modify code outside assigned scope
5. **Assumption-based decisions**: Always verify before assuming

### Agent-Specific Gotchas

#### Orchestrator
- Never implement features directly
- Never bypass validation gates
- Never approve production deployments without human consent

#### Analysis Agent
- Never modify application code
- Never make assumptions without evidence
- Never skip architecture analysis

#### Development Agents
- Never implement without planning approval
- Never skip testing
- Never ignore reviewer feedback

### Edge Case Prevention
- Document all edge cases encountered
- Create prevention strategies in retrospective-log.md
- Update agent specifications with new constraints

## Principle 6: Enforcement and Governance

### Compliance Checkpoints

#### Task Initiation
- [ ] Task contract exists and is valid
- [ ] Acceptance criteria defined
- [ ] Required resources identified
- [ ] Agent selection validated

#### Execution Gates
- [ ] Primary agent assigned and confirmed
- [ ] Supporting agents assigned if needed
- [ ] Artifact ownership defined
- [ ] Dependencies mapped

#### Completion Gates
- [ ] All acceptance criteria satisfied
- [ ] Validation tests pass
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Retrospective documented

### Quality Gates

#### Code Quality
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Tests pass
- [ ] No security vulnerabilities

#### Documentation Quality
- [ ] API documentation updated
- [ ] README updated if needed
- [ ] Architecture decisions documented

### Enforcement Mechanisms

1. **Pre-task validation**: Orchestrator validates task completeness
2. **Mid-execution monitoring**: Track agent progress and blockers
3. **Post-task review**: Reviewer agent validates quality
4. **Retrospective analysis**: Document lessons learned

## Workflow Execution Protocol

### Step 1: Task Receipt
1. Orchestrator receives task contract
2. Validate completeness and feasibility
3. Identify dependencies and risks

### Step 2: Agent Selection
1. Select primary agent based on task type
2. Assign supporting agents if needed
3. Assign reviewer agent for quality gates

### Step 3: Execution
1. Primary agent executes assigned work
2. Supporting agents assist with dependencies
3. Monitor progress and blockers

### Step 4: Validation
1. Run automated tests
2. Perform code review
3. Validate documentation

### Step 5: Completion
1. Update task status
2. Document retrospective
3. Produce final handoff

## Anti-Pattern Gotchas

### Critical Violations
- Using non-Gemini models → Immediate task failure
- Bypassing Orchestrator → Process violation
- Skipping validation → Quality gate failure

### Process Violations
- Implementing without planning → Scope creep risk
- Skipping code review → Quality risk
- Ignoring retrospective → Improvement stagnation

### Technical Violations
- Hardcoded secrets → Security vulnerability
- Bypassing permissions → Access control violation
- Ignoring streaming output → Performance degradation

## Monitoring and Compliance

### Real-time Monitoring
- Track agent execution status
- Monitor resource utilization
- Log completion criteria

### Compliance Auditing
- Regular review of retrospective logs
- Analysis of efficiency metrics
- Update of anti-pattern documentation

### Continuous Improvement
- Update agent specifications based on learnings
- Refine enforcement mechanisms
- Enhance prevention strategies

---

**Remember**: This framework exists to ensure safe, efficient, and high-quality AI-assisted software engineering. Every principle serves a purpose in preventing failures and ensuring consistent outcomes.
