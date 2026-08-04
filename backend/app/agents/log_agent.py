"""Log Agent — queries Loki for logs around the incident window (AGENTS.md)."""

from __future__ import annotations

import logging
from uuid import uuid4

from app.agents.window import investigation_window
from app.config import LOKI_URL
from app.models.state import Evidence, IncidentState
from app.tools.loki_client import query_logs

logger = logging.getLogger(__name__)


def log_agent_node(state: IncidentState) -> dict:
    start, end = investigation_window(state.triggered_at)
    try:
        entries = query_logs(state.service_name, start, end, LOKI_URL)
    except Exception:
        logger.exception("Log Agent: Loki query failed for %s", state.service_name)
        return {"evidence": []}

    evidence = [
        Evidence(
            id=f"ev-logs-{uuid4().hex[:8]}",
            source="logs",
            claim=entry["line"],
            timestamp=entry["timestamp"],
        )
        for entry in entries
    ]
    return {"evidence": evidence}
