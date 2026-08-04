"""Supervisor Agent — pure routing logic over alert metadata (AGENTS.md).

Does not investigate anything itself; only decides which of Log/Metrics/
Deploy are relevant to the incoming alert.
"""

from __future__ import annotations

from app.models.state import IncidentState

ALL_AGENTS = ["log_agent", "metrics_agent", "deploy_agent"]


def supervisor_node(state: IncidentState) -> dict:
    """Dispatch all three investigation agents by default (PIPELINE.md #2:
    "normally all three"), unless the alert payload explicitly narrows this
    via a "relevant_agents" list. See DECISIONS.md D-014 — no fault-scenario-
    specific routing rules yet; those arrive with Phase 7 fault injection.
    """
    requested = state.alert_payload.get("relevant_agents")
    if requested:
        agents = [a for a in requested if a in ALL_AGENTS] or ALL_AGENTS
    else:
        agents = list(ALL_AGENTS)
    return {"agents_dispatched": agents, "status": "investigating"}
