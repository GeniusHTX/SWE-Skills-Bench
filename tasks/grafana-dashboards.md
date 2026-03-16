# Task: Add Infrastructure Monitoring Dashboard to Grafana

## Background

Add a pre-built infrastructure monitoring dashboard JSON and provisioning configuration to the Grafana repository. The dashboard should be placed in Grafana's devenv provisioning directory for use in development and testing.

## Files to Create/Modify

- `devenv/dev-dashboards/infra/service_metrics.json` - Dashboard JSON definition
- `devenv/provisioning/dashboards/infra.yaml` - Dashboard provider config
- `devenv/provisioning/datasources/prometheus.yaml` - Prometheus datasource config

## Requirements

### Dashboard JSON (service_metrics.json)
- `title` and `uid` fields (uid must be unique)
- Multiple panel types:
  - Graph panel: Request rate over time
  - Stat panel: Error rate percentage
  - Histogram panel: Latency distribution
  - Table panel: Top endpoints by request count
- Variable templating (`$namespace`, `$service`)
- Time range configuration (default: last 1 hour)
- Prometheus queries for all panels

### Dashboard Provisioning (infra.yaml)
- Dashboard provider pointing to `devenv/dev-dashboards/infra/`
- `disableDeletion: false`
- `updateIntervalSeconds: 10`

### Datasource Provisioning (prometheus.yaml)
- Prometheus datasource definition
- URL: `http://localhost:9090`
- Access mode: proxy

## Acceptance Criteria

- `go build ./...` compiles without errors (dashboard files don't affect Go build)
- Dashboard JSON is valid (parseable without errors)
- Dashboard contains `panels` array with at least 4 panel definitions
- Provisioning YAML files are valid and contain provider configuration
