# Task: Implement SLO Monitoring for a Payment Processing API

## Background

A payment processing API needs SLO (Service Level Objective) monitoring with SLI measurement, error budget tracking, multi-window burn-rate alerting, and a Grafana SLO dashboard. The API has three critical endpoints: `POST /payments`, `GET /payments/{id}`, and `POST /payments/{id}/refund`. Each endpoint has different availability and latency SLO targets. The implementation uses Prometheus recording rules, alerting rules, and Grafana dashboards.

## Files to Create/Modify

- `slo/slo-definitions.yaml` (create) — SLO specification document defining SLIs, targets, and error budgets for each endpoint
- `slo/prometheus/recording-rules.yaml` (create) — Prometheus RecordingRule for SLI computation over 5m, 1h, 6h, 1d, and 28d windows
- `slo/prometheus/alerting-rules.yaml` (create) — Multi-window burn-rate alerting rules per Google SRE methodology
- `slo/grafana/slo-dashboard.json` (create) — Grafana dashboard with SLI tracking, error budget burn-down, and burn rate panels
- `slo/error-budget-policy.md` (create) — Error budget policy document defining actions at different budget thresholds

## Requirements

### SLO Definitions (`slo/slo-definitions.yaml`)

Define SLOs for each endpoint:

```yaml
slos:
  - name: payments_create_availability
    description: "POST /payments successful response rate"
    sli:
      type: availability
      good_events: 'http_requests_total{handler="/payments", method="POST", status!~"5.."}'
      total_events: 'http_requests_total{handler="/payments", method="POST"}'
    target: 99.95
    window: 28d
    error_budget_minutes: 12.1  # 0.05% of 28 days in minutes

  - name: payments_create_latency
    description: "POST /payments P99 under 1 second"
    sli:
      type: latency
      good_events: 'http_request_duration_seconds_bucket{handler="/payments", method="POST", le="1.0"}'
      total_events: 'http_request_duration_seconds_count{handler="/payments", method="POST"}'
    target: 99.0
    window: 28d

  - name: payments_get_availability
    description: "GET /payments/{id} successful response rate"
    sli:
      type: availability
      good_events: 'http_requests_total{handler="/payments/:id", method="GET", status!~"5.."}'
      total_events: 'http_requests_total{handler="/payments/:id", method="GET"}'
    target: 99.99
    window: 28d
    error_budget_minutes: 4.03

  - name: payments_get_latency
    description: "GET /payments/{id} P99 under 200ms"
    sli:
      type: latency
      good_events: 'http_request_duration_seconds_bucket{handler="/payments/:id", method="GET", le="0.2"}'
      total_events: 'http_request_duration_seconds_count{handler="/payments/:id", method="GET"}'
    target: 99.5
    window: 28d

  - name: payments_refund_availability
    description: "POST /payments/{id}/refund successful response rate"
    sli:
      type: availability
      good_events: 'http_requests_total{handler="/payments/:id/refund", method="POST", status!~"5.."}'
      total_events: 'http_requests_total{handler="/payments/:id/refund", method="POST"}'
    target: 99.9
    window: 28d
    error_budget_minutes: 40.3
```

### Recording Rules (`slo/prometheus/recording-rules.yaml`)

- `apiVersion: monitoring.coreos.com/v1`, kind `PrometheusRule`.
- Groups:

**Group: slo_sli_recording (interval 30s)**

For each SLO, compute SLI over multiple windows:

```yaml
# Availability SLIs
- record: sli:payments_create_availability:ratio_rate5m
  expr: |
    sum(rate(http_requests_total{handler="/payments", method="POST", status!~"5.."}[5m]))
    / sum(rate(http_requests_total{handler="/payments", method="POST"}[5m]))

- record: sli:payments_create_availability:ratio_rate1h
  expr: # same with [1h] window

- record: sli:payments_create_availability:ratio_rate6h
  expr: # same with [6h] window

- record: sli:payments_create_availability:ratio_rate1d
  expr: # same with [1d] window

- record: sli:payments_create_availability:ratio_rate28d
  expr: # same with [28d] window

# Latency SLIs
- record: sli:payments_create_latency:ratio_rate5m
  expr: |
    sum(rate(http_request_duration_seconds_bucket{handler="/payments", method="POST", le="1.0"}[5m]))
    / sum(rate(http_request_duration_seconds_count{handler="/payments", method="POST"}[5m]))

# ... same pattern for all 5 SLOs across all 5 windows
```

**Group: slo_error_budget (interval 1m)**

```yaml
# Remaining error budget ratio (1.0 = 100% remaining, 0.0 = exhausted)
- record: slo:payments_create_availability:error_budget_remaining
  expr: |
    1 - (
      (1 - sli:payments_create_availability:ratio_rate28d)
      / (1 - 0.9995)
    )
```

### Alerting Rules (`slo/prometheus/alerting-rules.yaml`)

Multi-window burn-rate alerting per Google SRE book:

| Severity | Short Window | Long Window | Burn Rate Factor | Budget Consumed at Fire |
|----------|-------------|-------------|------------------|------------------------|
| Page (critical) | 5m | 1h | 14.4x | 2% in 1h |
| Page (critical) | 30m | 6h | 6x | 5% in 6h |
| Ticket (warning) | 2h | 1d | 3x | 10% in 1d |
| Ticket (warning) | 6h | 3d | 1x | 10% in 3d |

For `payments_create_availability` (target 99.95%, error tolerance 0.0005):

```yaml
- alert: PaymentsCreateBurnRateCritical
  expr: |
    (1 - sli:payments_create_availability:ratio_rate5m) > (14.4 * 0.0005)
    and
    (1 - sli:payments_create_availability:ratio_rate1h) > (14.4 * 0.0005)
  for: 2m
  labels:
    severity: critical
    slo: payments_create_availability
  annotations:
    summary: "POST /payments burn rate is 14.4x the error budget"
    description: "At current error rate, the 28-day error budget will be exhausted in {{ $value | humanizeDuration }}"
    runbook: "https://runbooks.internal/payments-availability"

- alert: PaymentsCreateBurnRateHigh
  expr: |
    (1 - sli:payments_create_availability:ratio_rate30m) > (6 * 0.0005)
    and
    (1 - sli:payments_create_availability:ratio_rate6h) > (6 * 0.0005)
  for: 5m
  labels:
    severity: critical
    slo: payments_create_availability

- alert: PaymentsCreateBurnRateWarning
  expr: |
    (1 - sli:payments_create_availability:ratio_rate2h) > (3 * 0.0005)
    and
    (1 - sli:payments_create_availability:ratio_rate1d) > (3 * 0.0005)
  for: 10m
  labels:
    severity: warning
    slo: payments_create_availability
```

Same pattern for all 5 SLOs with endpoint-specific error tolerance values.

### Grafana Dashboard (`slo/grafana/slo-dashboard.json`)

- Dashboard title: `"Payment API SLOs"`, uid: `"payment-slos"`.
- Template variable: `$slo` (dropdown: `payments_create_availability`, `payments_create_latency`, `payments_get_availability`, etc.).
- Rows:
  1. **SLO Summary** (5 stat panels, one per SLO):
     - Current 28d SLI percentage, colored green (>= target), yellow (>= target-0.5%), red (< target-0.5%).
     - Threshold lines from SLO target.
  2. **Error Budget Burn-Down** (1 timeseries panel):
     - Query: `slo:${slo}:error_budget_remaining * 100`.
     - Y-axis: 0-100%.
     - Threshold at 0% (red), 10% (yellow), 50% (green).
     - Annotation: mark when error budget policy thresholds are crossed.
  3. **Burn Rate** (1 timeseries panel):
     - Overlay 4 window burn rates for the selected SLO (5m, 1h, 6h, 1d).
     - Threshold lines at 14.4x, 6x, 3x, 1x.
  4. **SLI Over Time** (1 timeseries panel):
     - 5-minute SLI ratio over the last 28 days.
     - Target line from SLO definition.
  5. **Error Budget by Endpoint** (1 bar gauge panel):
     - Horizontal bars showing remaining error budget percentage per SLO.

### Error Budget Policy (`slo/error-budget-policy.md`)

Markdown document with thresholds:
- `> 50% remaining`: Normal development velocity. Deploy freely.
- `25-50% remaining`: Heightened awareness. Every deploy must have rollback plan.
- `10-25% remaining`: Slow down. Only ship reliability improvements and critical bug fixes.
- `1-10% remaining`: Feature freeze. Only reliability work. Page on-call for new incidents.
- `0% remaining (exhausted)`: Full freeze. All engineering effort goes to reliability. Post-incident review required before resuming feature work.

Include: escalation contacts, exception process, and reset cadence (budget resets every 28 days).

### Expected Functionality

- `POST /payments` returns 503 for 0.06% of requests over 28 days → SLI is 99.94%, below 99.95% target → error budget exhausted → `PaymentsCreateBurnRateCritical` alert fires.
- `GET /payments/{id}` P99 latency spikes to 300ms → latency SLI drops below 99.5% target → alert fires.
- Grafana dashboard shows real-time error budget remaining at 73%, burn rate at 1.2x (within budget).
- Error budget drops to 8% → policy requires feature freeze, dashboard shows red status.

## Acceptance Criteria

- SLOs define availability and latency targets for all 3 payment endpoints with explicit error budget calculations.
- Recording rules compute SLI ratios across 5 time windows (5m, 1h, 6h, 1d, 28d) for each SLO.
- Error budget remaining is computed as a ratio (1.0 = full, 0.0 = exhausted) from the 28d SLI and target.
- Multi-window burn-rate alerts use 4 severity levels: 14.4x (2% in 1h), 6x (5% in 6h), 3x (10% in 1d), 1x (10% in 3d).
- Each alert rule requires BOTH short and long window to exceed the threshold (reduces false positives).
- Grafana dashboard includes SLO summary stats, error budget burn-down chart, burn rate overlay, SLI timeseries, and per-endpoint budget bars.
- Error budget policy defines 5 action tiers from normal operations to full freeze with clear thresholds.
- Alert annotations include runbook URLs and human-readable descriptions of budget impact.
