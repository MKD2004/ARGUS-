"""Integration test: a full LangGraph run against a stubbed incident,
verifying state transitions end-to-end without external services
(TESTING_STRATEGY.md #2 "Integration" layer).
"""

from datetime import datetime, timezone
from unittest.mock import patch

from app.graph import build_graph
from app.models.state import IncidentState


def _stub_state(**overrides) -> IncidentState:
    base = dict(
        incident_id="inc-1",
        alert_payload={},
        service_name="payments",
        triggered_at=datetime.now(timezone.utc),
        max_hypothesis_iterations=5,
        max_patch_retries=3,
        status="investigating",
    )
    base.update(overrides)
    return IncidentState(**base)


def _patched_tools():
    return (
        patch(
            "app.agents.log_agent.query_logs",
            return_value=[{"timestamp": datetime.now(timezone.utc), "line": "log evidence", "labels": {}}],
        ),
        patch(
            "app.agents.metrics_agent.query_metrics",
            return_value=[
                {"metric": "stub_requests_total", "labels": {}, "values": [(datetime.now(timezone.utc), 1.0)]}
            ],
        ),
        patch(
            "app.agents.deploy_agent.query_deploys",
            return_value=[
                {"sha": "abc1234", "message": "deploy evidence", "author": "me", "timestamp": datetime.now(timezone.utc)}
            ],
        ),
        patch("app.agents.deploy_agent.GITHUB_REPO", "org/repo"),
    )


def test_full_investigation_merges_evidence_from_all_three_agents():
    graph = build_graph()
    p1, p2, p3, p4 = _patched_tools()
    with p1, p2, p3, p4:
        result = graph.invoke(_stub_state())

    assert result["status"] == "validating_hypothesis"
    assert sorted(e.source for e in result["evidence"]) == ["deploy", "logs", "metrics"]
    assert set(result["agents_dispatched"]) == {"log_agent", "metrics_agent", "deploy_agent"}


def test_conditional_fan_out_dispatches_only_requested_agent():
    graph = build_graph()
    p1, p2, p3, p4 = _patched_tools()
    with p1, p2, p3, p4:
        result = graph.invoke(_stub_state(alert_payload={"relevant_agents": ["log_agent"]}))

    assert result["agents_dispatched"] == ["log_agent"]
    assert [e.source for e in result["evidence"]] == ["logs"]
    assert result["status"] == "validating_hypothesis"
