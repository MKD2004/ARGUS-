"""Unit tests for the tool clients — parsing logic only, no live services.

Fetch functions are monkeypatched with fixture data (TESTING_STRATEGY.md #3:
external services must be mockable without live credentials).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from app.tools.github_client import query_deploys
from app.tools.loki_client import query_logs
from app.tools.metrics_client import query_metrics

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text())


def test_query_logs_parses_streams_into_entries():
    fixture = _load("loki_response.json")
    entries = query_logs(
        "payments",
        datetime.now(timezone.utc),
        datetime.now(timezone.utc),
        "http://loki:3100",
        fetch=lambda url, params: fixture,
    )
    assert len(entries) == 2
    assert entries[0]["line"] == "ERROR redis connection pool exhausted"
    assert entries[0]["labels"] == {"container": "demo-env-payments-1"}
    assert isinstance(entries[0]["timestamp"], datetime)


def test_query_metrics_parses_matrix_into_series():
    fixture = _load("prometheus_response.json")
    series_list = query_metrics(
        "payments",
        datetime.now(timezone.utc),
        datetime.now(timezone.utc),
        "http://prometheus:9090",
        fetch=lambda url, params: fixture,
    )
    assert len(series_list) == 1
    series = series_list[0]
    assert series["metric"] == "stub_requests_total"
    assert len(series["values"]) == 2
    assert series["values"][-1][1] == 18.0


def test_query_deploys_parses_commits():
    fixture = _load("github_commits.json")
    commits = query_deploys(
        "org",
        "repo",
        datetime.now(timezone.utc),
        datetime.now(timezone.utc),
        token=None,
        fetch=lambda url, params, headers: fixture,
    )
    assert len(commits) == 1
    commit = commits[0]
    assert commit["sha"] == "abc1234"
    assert commit["message"] == "Lower redis max-connections for load test"
    assert commit["author"] == "Jane Doe"
    assert commit["timestamp"] == datetime(2026, 8, 4, 10, 30, 0, tzinfo=timezone.utc)
