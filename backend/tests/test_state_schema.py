"""Contract-layer tests per TESTING_STRATEGY.md #2.

Verifies the Pydantic models in app/models/state.py construct correctly and
enforce the invariants documented in STATE_SCHEMA.md.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.state import Evidence, Hypothesis, IncidentState


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _minimal_incident(**overrides) -> dict:
    base = dict(
        incident_id="inc-1",
        alert_payload={"alert": "RedisConnectionsHigh"},
        service_name="payments",
        triggered_at=_now(),
        max_hypothesis_iterations=5,
        max_patch_retries=3,
        status="investigating",
    )
    base.update(overrides)
    return base


def test_incident_state_constructs_with_only_required_fields():
    state = IncidentState(**_minimal_incident())
    assert state.evidence == []
    assert state.rejected_hypotheses == []
    assert state.accepted_hypothesis is None
    assert state.status == "investigating"


def test_full_incident_state_constructs_with_nested_models():
    evidence = Evidence(
        id="ev-1",
        source="metrics",
        claim="Redis latency jumped 340% at 10:32",
        timestamp=_now(),
        supports_hypothesis_id="hyp-1",
    )
    hypothesis = Hypothesis(
        id="hyp-1",
        description="Redis connection pool exhausted",
        status="accepted",
        supporting_evidence_ids=["ev-1"],
    )
    state = IncidentState(
        **_minimal_incident(
            evidence=[evidence],
            candidate_hypotheses=[hypothesis],
            accepted_hypothesis=hypothesis,
        )
    )
    assert state.accepted_hypothesis.id == "hyp-1"
    assert state.evidence[0].supports_hypothesis_id == "hyp-1"


def test_evidence_cannot_both_support_and_contradict():
    with pytest.raises(ValidationError):
        Evidence(
            id="ev-1",
            source="logs",
            claim="ambiguous",
            timestamp=_now(),
            supports_hypothesis_id="hyp-1",
            contradicts_hypothesis_id="hyp-2",
        )


def test_evidence_may_support_neither_hypothesis():
    evidence = Evidence(id="ev-1", source="logs", claim="pre-hypothesis observation", timestamp=_now())
    assert evidence.supports_hypothesis_id is None
    assert evidence.contradicts_hypothesis_id is None


def test_rejected_hypothesis_requires_rejection_reason():
    with pytest.raises(ValidationError):
        Hypothesis(id="hyp-1", description="bad deploy", status="rejected")


def test_non_rejected_hypothesis_cannot_carry_rejection_reason():
    with pytest.raises(ValidationError):
        Hypothesis(
            id="hyp-1",
            description="bad deploy",
            status="candidate",
            rejection_reason="should not be set",
        )


def test_rejected_hypothesis_with_reason_is_valid():
    hypothesis = Hypothesis(
        id="hyp-1",
        description="bad deploy",
        status="rejected",
        rejection_reason="No deploy correlated with incident window",
    )
    assert hypothesis.rejection_reason


def test_github_pr_url_requires_human_approval():
    # D-008 / STATE_SCHEMA.md invariant 3, enforced structurally.
    with pytest.raises(ValidationError):
        IncidentState(
            **_minimal_incident(
                github_pr_url="https://github.com/org/repo/pull/1",
                human_decision="pending",
            )
        )


def test_github_pr_url_allowed_when_approved():
    state = IncidentState(
        **_minimal_incident(
            github_pr_url="https://github.com/org/repo/pull/1",
            human_decision="approved",
        )
    )
    assert state.github_pr_url is not None
