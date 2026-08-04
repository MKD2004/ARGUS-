"""Stub service for the demo microservices stack.

Health-checkable and Prometheus-scrapeable so the topology in
DEMO_ENVIRONMENT.md is real for the Log/Metrics agents to query against.
Business logic (and fault injection) is added when those scenarios are built.
"""

from fastapi import FastAPI
from prometheus_client import Counter, make_asgi_app

SERVICE_NAME = "payments"

app = FastAPI(title=SERVICE_NAME)
app.mount("/metrics", make_asgi_app())

requests_total = Counter("stub_requests_total", "Total requests handled", ["service"])


@app.get("/health")
def health() -> dict[str, str]:
    requests_total.labels(service=SERVICE_NAME).inc()
    return {"service": SERVICE_NAME, "status": "ok"}
