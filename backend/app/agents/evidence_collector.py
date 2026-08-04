"""Evidence Collector — fan-in synchronization node (AGENTS.md; DECISIONS.md D-013).

By the time this node runs, LangGraph has already merged the parallel
Log/Metrics/Deploy branches' Evidence writes into state.evidence via the
additive reducer declared on IncidentState.evidence. This node's job is to
verify the merge landed and advance the pipeline to hypothesis generation.
"""

from __future__ import annotations

import logging

from app.models.state import IncidentState

logger = logging.getLogger(__name__)


def evidence_collector_node(state: IncidentState) -> dict:
    if not state.evidence:
        logger.warning("Evidence Collector: no evidence gathered for incident %s", state.incident_id)
    return {"status": "validating_hypothesis"}
