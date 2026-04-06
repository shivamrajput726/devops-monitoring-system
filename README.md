# DevOps Monitoring Project (Docker + Prometheus + Grafana)

A simple, resume-friendly DevOps monitoring stack using Docker Compose. It runs a small Python sample app that:
- continuously generates logs (INFO/WARN/ERROR) to stdout
- exposes Prometheus metrics at `/metrics`

Prometheus scrapes the app metrics, evaluates alerting rules, and forwards alerts to Alertmanager. Grafana is pre-provisioned with a Prometheus data source and **2 dashboards**.

---

## Architecture (text diagram)

```
                    +-------------------+
                    |     Grafana       |
                    |    :3000          |
                    | Dashboards (2)    |
                    +---------+---------+
                              |
                              | (PromQL)
                              v
+-------------------+   +-----+----------------+    +-------------------+
|   sample-app      |   |     Prometheus       |    |   Alertmanager    |
|   :8000           +--->     :9090            +--->     :9093          |
| /metrics, /, ...  |   |  Scrape + Alerts     |    | (null receiver)   |
+-------------------+   +----------------------+    +-------------------+
```

---

## Project structure

```
.
├─ app/                     # Python sample app + Dockerfile
├─ prometheus/              # Prometheus scrape config + alert rules
├─ alertmanager/            # Alertmanager config (no external notifications)
├─ grafana/
│  ├─ provisioning/         # Datasource + dashboard providers
│  └─ dashboards/           # 2 prebuilt dashboards (JSON)
└─ docker-compose.yml
```

---

## Tech stack

- Docker / Docker Compose
- Python (Flask) sample application
- Prometheus (metrics + alert rules)
- Alertmanager (alert routing; configured as “no-op” receiver)
- Grafana (dashboards + provisioning)

---

## Setup & run

### 1) Start the stack

```bash
docker compose up -d --build
```

### 2) Open UIs

- Sample app: http://localhost:8000
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093
- Grafana: http://localhost:3000
  - Username: `admin`
  - Password: `admin`

### 3) Generate some traffic (so graphs move)

```bash
curl http://localhost:8000/
curl http://localhost:8000/slow
curl http://localhost:8000/error
```

Tip: hit `/error` repeatedly to trigger the `High5xxRate` alert, and `/slow` to increase latency.

### 4) What to check

- Prometheus Targets: http://localhost:9090/targets (should show `sample-app` as UP)
- Prometheus Alerts: http://localhost:9090/alerts
- Grafana Dashboards:
  - Folder: **DevOps Monitoring**
  - Dashboards:
    - **Sample App Overview**
    - **Prometheus Overview**

---

## Prometheus alerts included

Defined in `prometheus/alerts.yml`:

- `SampleAppDown` — fires when Prometheus can’t scrape the app for 1 minute
- `High5xxRate` — fires when the app returns too many 5xx responses
- `P95LatencyHigh` — fires when p95 latency stays above 0.5s

---

## Example outputs

### Sample app response

```json
{"message":"Hello from the DevOps monitoring demo!","service":"sample-app"}
```

### Sample app logs (stdout)

```text
2026-04-07 12:00:01 INFO Starting sample-app on port 8000
2026-04-07 12:00:03 INFO Background job heartbeat
2026-04-07 12:00:06 WARNING Retrying failed operation
2026-04-07 12:00:10 ERROR Simulated error occurred
```

### Example metrics (Prometheus format)

```text
http_requests_total{method="GET",endpoint="/",status="200"} 12
app_log_messages_total{level="info"} 34
```

---

## Notes (for resume / interviews)

- Uses containerized monitoring stack with provisioning (repeatable setup).
- Demonstrates scrape configs, alert rules, and dashboarding with PromQL.
- Docker images use `:latest` for simplicity; pin versions in `docker-compose.yml` for fully reproducible builds.
- Easy extensions: add Loki for logs, add node-exporter, add Slack/Email receivers in Alertmanager.
