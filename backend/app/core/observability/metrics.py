"""Prometheus metrics (Phase 16)."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS = Counter(
    "agriflow_http_requests_total",
    "Total HTTP requests",
    ["method", "path_template", "status"],
)
HTTP_LATENCY = Histogram(
    "agriflow_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path_template"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
COPILOT_REQUESTS = Counter(
    "agriflow_copilot_requests_total",
    "Farm Copilot chat requests",
    ["mode"],
)


def metrics_payload() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
