# Retrospective Log

## Purpose
Document failures, root causes, edge cases, and process improvement suggestions to enable continuous improvement of the AI workflow system.

## Entry Format

### [Date] — Task/Incident Summary

**Status**: SUCCESS | PARTIAL_SUCCESS | FAILED | BLOCKED

**Task ID**: [if applicable]

**Description**: [Brief description of the task or incident]

**What Happened**:
- [Sequence of events]

**Root Cause**:
- [Primary cause]
- [Contributing factors]

**Edge Cases Encountered**:
- [List any unexpected scenarios]

**Resolution**:
- [How it was resolved or worked around]

**Lessons Learned**:
- [Key takeaways]

**Process Improvements**:
- [Suggestions for preventing similar issues]

**Efficiency Impact**:
- Time spent: [estimate]
- Resources used: [description]
- Alternative approach: [if applicable]

---

## Recent Entries

### [Pending — No entries yet]

To add an entry, copy the format above and fill in the details.

## Anti-Pattern Registry

### Documented Anti-Patterns

| ID | Anti-Pattern | Impact | Prevention Strategy |
|----|--------------|--------|---------------------|
| AP-001 | Using non-Gemini models | Critical violation of Principle 1 | Always verify model configuration in opencode.json |
| AP-002 | Orchestrator implementing directly | Scope creep, bypasses subagent expertise | Delegate to specialized agents |
| AP-003 | Skipping planning phase | Incomplete task understanding, poor execution | Enforce planning agent assignment |
| AP-004 | Bypassing validation gates | Quality issues reach production | Mandatory validation checkpoints |
| AP-005 | Ignoring retrospective | Repeated failures, no improvement | Document after every significant task |
| AP-006 | Hardcoded secrets | Security vulnerabilities | Use environment variables, never log secrets |
| AP-007 | Assumption-based decisions | Incorrect implementations | Always verify with evidence |
| AP-008 | Blocking on single agent | Performance degradation | Use parallel execution when possible |

## Edge Case Registry

### Documented Edge Cases

| ID | Edge Case | Occurrence | Prevention Strategy |
|----|-----------|------------|---------------------|
| EC-001 | [To be documented] | | |

## Process Improvement Suggestions

### Pending Review

- [ ] [Add suggestions as they are identified]

### Implemented

- [ ] [Document improvements that have been implemented]

### Rejected

- [ ] [Document improvements that were considered but rejected, with rationale]

## Efficiency Metrics

### Task Completion Statistics

| Metric | Value | Last Updated |
|--------|-------|--------------|
| Total tasks completed | 0 | |
| Average completion time | N/A | |
| Success rate | N/A | |
| Failure rate | N/A | |

### Resource Utilization

| Resource | Usage Pattern | Optimization Notes |
|----------|---------------|-------------------|
| Gemini models | Primary | Monitor for cost efficiency |
| Subagent delegation | Active | Track parallel execution gains |

---

**Last Updated**: [Date]
**Next Review**: [Date]
