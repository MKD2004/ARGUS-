"""Pydantic implementation of the shared LangGraph state contract.

Field-for-field mirror of STATE_SCHEMA.md. That document is the source of
truth — if this drifts from it, the doc must be updated first per CLAUDE.md.
"""

from __future__ import annotations

import operator
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, model_validator

EvidenceSource = Literal["logs", "metrics", "deploy", "test", "incident_memory"]
HypothesisStatus = Literal["candidate", "accepted", "rejected"]
TestResult = Literal["pending", "passed", "failed"]
HumanDecision = Literal["pending", "approved", "rejected"]
IncidentStatus = Literal[
    "investigating",
    "validating_hypothesis",
    "retrieving_memory",
    "planning_fix",
    "generating_patch",
    "testing_patch",
    "awaiting_human_approval",
    "creating_pr",
    "creating_issue",
    "writing_postmortem",
    "notifying",
    "resolved",
]


class Evidence(BaseModel):
    id: str
    source: EvidenceSource
    claim: str
    timestamp: datetime
    supports_hypothesis_id: str | None = None
    contradicts_hypothesis_id: str | None = None

    @model_validator(mode="after")
    def _supports_xor_contradicts(self) -> "Evidence":
        # STATE_SCHEMA.md invariant 5: exactly one of supports/contradicts, or neither.
        if self.supports_hypothesis_id is not None and self.contradicts_hypothesis_id is not None:
            raise ValueError(
                "Evidence cannot both support and contradict a hypothesis "
                "(supports_hypothesis_id and contradicts_hypothesis_id are mutually exclusive)"
            )
        return self


class Hypothesis(BaseModel):
    id: str
    description: str
    status: HypothesisStatus
    supporting_evidence_ids: list[str] = []
    contradicting_evidence_ids: list[str] = []
    rejection_reason: str | None = None

    @model_validator(mode="after")
    def _rejection_reason_matches_status(self) -> "Hypothesis":
        # D-007: a rejected hypothesis always carries its reason; anything else never does.
        if self.status == "rejected" and not self.rejection_reason:
            raise ValueError("rejection_reason is required when status == 'rejected'")
        if self.status != "rejected" and self.rejection_reason is not None:
            raise ValueError("rejection_reason must be unset unless status == 'rejected'")
        return self


class SimilarIncident(BaseModel):
    incident_id: str
    similarity_score: float
    summary: str
    fix_applied: str
    recovery_time_minutes: float


class FixStrategy(BaseModel):
    id: str
    description: str
    tradeoffs: str
    rank: int


class Patch(BaseModel):
    id: str
    diff: str
    attempt_number: int
    test_result: TestResult
    failure_traceback: str | None = None


class IncidentState(BaseModel):
    incident_id: str
    alert_payload: dict
    service_name: str
    triggered_at: datetime

    # Investigation
    agents_dispatched: list[str] = []
    # Additive reducer: Log/Metrics/Deploy agents run in parallel and each
    # write their own Evidence entries — LangGraph needs this to merge
    # concurrent writes instead of raising a conflicting-update error.
    # See DECISIONS.md D-013.
    evidence: Annotated[list[Evidence], operator.add] = []

    # Hypothesis loop
    candidate_hypotheses: list[Hypothesis] = []
    rejected_hypotheses: list[Hypothesis] = []
    accepted_hypothesis: Hypothesis | None = None
    hypothesis_loop_iterations: int = 0
    max_hypothesis_iterations: int

    # Memory
    similar_incidents: list[SimilarIncident] = []

    # Fix loop
    candidate_fix_strategies: list[FixStrategy] = []
    chosen_fix_strategy: FixStrategy | None = None
    patches: list[Patch] = []
    patch_retry_count: int = 0
    max_patch_retries: int

    # Human gate
    human_decision: HumanDecision | None = None
    human_decision_by: str | None = None
    human_decision_at: datetime | None = None

    # Outputs
    github_pr_url: str | None = None
    github_issue_url: str | None = None
    postmortem: str | None = None
    slack_notifications_sent: list[str] = []

    # Status
    status: IncidentStatus

    @model_validator(mode="after")
    def _pr_requires_human_approval(self) -> "IncidentState":
        # STATE_SCHEMA.md invariant 3 / D-008: the only field that can unlock
        # github_pr_url is an explicit human_decision == "approved".
        if self.github_pr_url is not None and self.human_decision != "approved":
            raise ValueError("github_pr_url can only be set when human_decision == 'approved'")
        return self
