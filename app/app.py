import logging
import os
import random
import threading
import time
from time import perf_counter

from flask import Flask, Response, g, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


PORT = int(os.getenv("PORT", "8000"))
LOG_INTERVAL_SECONDS = float(os.getenv("LOG_INTERVAL_SECONDS", "2"))


app = Flask(__name__)

LOG_MESSAGES_TOTAL = Counter(
    "app_log_messages_total",
    "Number of log messages emitted by level",
    ["level"],
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "HTTP requests total",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 1, 2, 5),
)


logger = logging.getLogger("sample-app")
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _log_generator() -> None:
    levels = [logging.INFO, logging.WARNING, logging.ERROR]
    messages = [
        "Background job heartbeat",
        "Processing batch of events",
        "Cache warm-up completed",
        "Retrying failed operation",
        "Simulated error occurred",
    ]

    while True:
        level = random.choices(levels, weights=[0.78, 0.18, 0.04], k=1)[0]
        message = random.choice(messages)

        if level == logging.INFO:
            LOG_MESSAGES_TOTAL.labels(level="info").inc()
        elif level == logging.WARNING:
            LOG_MESSAGES_TOTAL.labels(level="warning").inc()
        else:
            LOG_MESSAGES_TOTAL.labels(level="error").inc()

        logger.log(level, message)
        time.sleep(LOG_INTERVAL_SECONDS)


@app.before_request
def _before_request() -> None:
    g._start = perf_counter()


@app.after_request
def _after_request(response):
    endpoint = request.path
    duration = perf_counter() - getattr(g, "_start", perf_counter())

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code),
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(endpoint=endpoint).observe(duration)
    return response


@app.get("/")
def index():
    # Add a tiny random delay so latency graphs are more interesting.
    time.sleep(random.random() * 0.15)
    logger.info("GET / served")
    return {"service": "sample-app", "message": "Hello from the DevOps monitoring demo!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/slow")
def slow():
    time.sleep(0.8)
    logger.warning("GET /slow simulated slowness")
    return {"status": "slow", "sleep_seconds": 0.8}


@app.get("/error")
def error():
    logger.error("GET /error simulated failure")
    return {"status": "error", "message": "simulated failure"}, 500


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    threading.Thread(target=_log_generator, daemon=True).start()
    logger.info("Starting sample-app on port %s", PORT)
    app.run(host="0.0.0.0", port=PORT)

