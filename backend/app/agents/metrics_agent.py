"""Metrics Agent — queries Prometheus for metrics around the incident window (AGENTS.md)."""

from __future__ import annotations

import logging
from uuid import uuid4

from app.agents.window import investigation_window
from app.config import PROMETHEUS_URL
from app.models.state import Evidence, IncidentState
from app.tools.metrics_client import query_metrics

logger = logging.getLogger(__name__)


def metrics_agent_node(state: IncidentState) -> dict:
    start, end = investigation_window(state.triggered_at)
    try:
        series_list = query_metrics(state.service_name, start, end, PROMETHEUS_URL)
    except Exception:
        logger.exception("Metrics Agent: Prometheus query failed for %s", state.service_name)
        return {"evidence": []}

    evidence: list[Evidence] = []
    for series in series_list:
        if not series["values"]:
            continue
        latest_ts, latest_val = series["values"][-1]
        evidence.append(
            Evidence(
                id=f"ev-metrics-{uuid4().hex[:8]}",
                source="metrics",
                claim=f"{series['metric']} = {latest_val} for {state.service_name} at {latest_ts.isoformat()}",
                timestamp=latest_ts,
            )
        )
    return {"evidence": evidence}
