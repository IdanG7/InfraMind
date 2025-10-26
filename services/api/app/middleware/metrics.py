"""Prometheus metrics for API monitoring"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import time

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method", "endpoint"]
)

# Application metrics
optimization_requests_total = Counter(
    "optimization_requests_total",
    "Total optimization requests",
    ["pipeline"]
)

optimization_duration_seconds = Histogram(
    "optimization_duration_seconds",
    "Time to generate optimization suggestions",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

build_runs_processed_total = Counter(
    "build_runs_processed_total",
    "Total build runs processed",
    ["pipeline", "status"]
)

model_predictions_total = Counter(
    "model_predictions_total",
    "Total ML model predictions",
    ["model_version"]
)

model_prediction_errors_total = Counter(
    "model_prediction_errors_total",
    "Total ML model prediction errors",
    ["error_type"]
)

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query duration",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

redis_operations_total = Counter(
    "redis_operations_total",
    "Total Redis operations",
    ["operation", "status"]
)


async def metrics_middleware(request: Request, call_next):
    """Middleware to track request metrics"""
    # Skip metrics for the metrics endpoint itself
    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method
    endpoint = request.url.path

    # Track in-progress requests
    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

    # Track request duration
    start_time = time.time()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        status_code = 500
        raise
    finally:
        duration = time.time() - start_time

        # Record metrics
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).dec()

    return response


async def metrics_endpoint():
    """Endpoint to expose Prometheus metrics"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
