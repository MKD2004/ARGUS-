"""Thin GitHub commits client for the Deploy Agent."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

import httpx

FetchFn = Callable[[str, dict, dict], list]


def _default_fetch(url: str, params: dict, headers: dict) -> list:
    response = httpx.get(url, params=params, headers=headers, timeout=10.0)
    response.raise_for_status()
    return response.json()


def query_deploys(
    owner: str,
    repo: str,
    start: datetime,
    end: datetime,
    token: str | None = None,
    fetch: FetchFn = _default_fetch,
) -> list[dict]:
    """Query GitHub for commits to `owner/repo` in [start, end].

    Returns raw entries: [{"sha": str, "message": str, "author": str, "timestamp": datetime}, ...]
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"since": start.isoformat(), "until": end.isoformat()}
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = fetch(url, params, headers)

    commits: list[dict] = []
    for item in data:
        commit = item.get("commit", {})
        author = commit.get("author", {})
        message = commit.get("message", "")
        raw_date = author.get("date")
        commits.append(
            {
                "sha": item.get("sha", "")[:7],
                "message": message.splitlines()[0] if message else "",
                "author": author.get("name", "unknown"),
                "timestamp": datetime.fromisoformat(raw_date.replace("Z", "+00:00")) if raw_date else start,
            }
        )
    return commits
