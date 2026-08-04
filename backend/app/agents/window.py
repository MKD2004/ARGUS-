"""Shared investigation time-window helper for Log/Metrics/Deploy agents."""

from datetime import datetime, timedelta

BEFORE = timedelta(minutes=15)
AFTER = timedelta(minutes=5)


def investigation_window(triggered_at: datetime) -> tuple[datetime, datetime]:
    return triggered_at - BEFORE, triggered_at + AFTER
