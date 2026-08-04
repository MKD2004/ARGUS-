"""Deploy Agent — looks up recent GitHub commits for the affected service (AGENTS.md)."""

from __future__ import annotations

import logging
from uuid import uuid4

from app.agents.window import investigation_window
from app.config import GITHUB_REPO, GITHUB_TOKEN
from app.models.state import Evidence, IncidentState
from app.tools.github_client import query_deploys

logger = logging.getLogger(__name__)


def deploy_agent_node(state: IncidentState) -> dict:
    if "/" not in GITHUB_REPO:
        logger.warning("Deploy Agent: GITHUB_REPO not configured, skipping")
        return {"evidence": []}
    owner, repo = GITHUB_REPO.split("/", 1)

    start, end = investigation_window(state.triggered_at)
    try:
        commits = query_deploys(owner, repo, start, end, GITHUB_TOKEN)
    except Exception:
        logger.exception("Deploy Agent: GitHub query failed for %s", state.service_name)
        return {"evidence": []}

    evidence = [
        Evidence(
            id=f"ev-deploy-{uuid4().hex[:8]}",
            source="deploy",
            claim=f"Commit {c['sha']} ({c['message']}) by {c['author']} at {c['timestamp'].isoformat()}",
            timestamp=c["timestamp"],
        )
        for c in commits
    ]
    return {"evidence": evidence}
