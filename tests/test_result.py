"""Tests for runtime/core/result.py"""

from runtime.core.result import AgentResult, AgentStatus


def test_agent_result_creation():
    result = AgentResult(status=AgentStatus.SUCCESS, summary="Done")
    assert result.status == AgentStatus.SUCCESS
    assert result.summary == "Done"
    assert result.artifacts == []
    assert result.validation_results == []
    assert result.blockers == []


def test_agent_result_is_success():
    assert AgentResult(status=AgentStatus.SUCCESS, summary="").is_success()
    assert AgentResult(status=AgentStatus.PARTIAL_SUCCESS, summary="").is_success()
    assert not AgentResult(status=AgentStatus.FAILED, summary="").is_success()
    assert not AgentResult(status=AgentStatus.BLOCKED, summary="").is_success()
    assert not AgentResult(status=AgentStatus.NEEDS_REVIEW, summary="").is_success()


def test_agent_result_to_dict():
    result = AgentResult(
        status=AgentStatus.SUCCESS,
        summary="Completed",
        artifacts=["a.md"],
        validation_results=["v1"],
        blockers=[],
        recommended_next_action="Review",
        agent_id="TEST-001",
    )
    d = result.to_dict()
    assert d["status"] == "SUCCESS"
    assert d["agent_id"] == "TEST-001"
    assert d["artifacts"] == ["a.md"]
    assert d["recommended_next_action"] == "Review"
