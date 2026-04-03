# Task: Implement a Per-Service Golden Signals Dashboard in Linkerd2

## Background

Linkerd2 (https://github.com/linkerd/linkerd2) provides a service mesh with built-in observability through Prometheus metrics. The task is to implement a Go package within the Linkerd2 `viz` extension that generates Grafana dashboard JSON for the four golden signals (latency, traffic, errors, saturation) for a given Kubernetes service, using Linkerd's standard metric label schema.

## Files to Create/Modify

- `viz/pkg/dashboard/generator.go` (create) — `DashboardGenerator` that builds Grafana dashboard JSON for a named service
- `viz/pkg/dashboard/panels.go` (create) — Individual panel builders for the four golden signals
- `viz/pkg/dashboard/types.go` (create) — Go structs representing the Grafana Dashboard JSON schema subset needed
- `viz/pkg/dashboard/generator_test.go` (create) — Unit tests for the generator and panel builders

## Requirements

### Grafana Dashboard Types (`types.go`)

Define Go structs that marshal to valid Grafana dashboard JSON:

```go
type Dashboard struct {
    Title       string        `json:"title"`
    UID         string        `json:"uid"`          // Deterministic: sha256(service+namespace)[:8]
    Tags        []string      `json:"tags"`
    Refresh     string        `json:"refresh"`      // e.g. "30s"
    SchemaVersion int         `json:"schemaVersion"` // 36
    Panels      []Panel       `json:"panels"`
    Templating  Templating    `json:"templating"`
    Time        TimeRange     `json:"time"`
}

type Panel struct {
    ID          int           `json:"id"`
    Title       string        `json:"title"`
    Type        string        `json:"type"`         // "timeseries", "stat", "gauge"
    GridPos     GridPos       `json:"gridPos"`
    Targets     []Target      `json:"targets"`
    FieldConfig FieldConfig   `json:"fieldConfig,omitempty"`
    Alert       *Alert        `json:"alert,omitempty"`
}

type Target struct {
    Expr          string `json:"expr"`
    LegendFormat  string `json:"legendFormat"`
    RefID         string `json:"refId"`
}

type GridPos struct {
    X, Y, W, H int `json:"x" json:"y" json:"w" json:"h"`
}

type Alert struct {
    Name              string          `json:"name"`
    Conditions        []AlertCondition `json:"conditions"`
    ExecutionErrorState string        `json:"executionErrorState"` // "keep_state"
    Frequency         string          `json:"frequency"`          // "1m"
    Handler           int             `json:"handler"`            // 1
}

type AlertCondition struct {
    Evaluator  Evaluator  `json:"evaluator"`
    Operator   Operator   `json:"operator"`
    Query      QueryRef   `json:"query"`
    Reducer    Reducer    `json:"reducer"`
    Type       string     `json:"type"` // "query"
}
```

### Panel Builders (`panels.go`)

All panels use Linkerd's standard Prometheus metric labels: `namespace`, `deployment`, `direction`.

#### `SuccessRatePanel(service, namespace string, gridPos GridPos) Panel`

- Type: `"stat"`
- Title: `"Success Rate"`
- PromQL target:
  ```
  sum(rate(response_total{namespace="<namespace>",deployment="<service>",classification="success"}[2m]))
  /
  sum(rate(response_total{namespace="<namespace>",deployment="<service>"}[2m]))
  ```
- Unit: `"percentunit"` (0.0–1.0 displayed as percentage)
- Alert: trigger when success rate < 0.99 for 5 minutes

#### `RequestRatePanel(service, namespace string, gridPos GridPos) Panel`

- Type: `"timeseries"`
- Title: `"Request Rate"`
- PromQL target (by direction):
  ```
  sum(rate(response_total{namespace="<namespace>",deployment="<service>"}[2m])) by (direction)
  ```
- LegendFormat: `"{{direction}}"`
- Unit: `"reqps"`

#### `LatencyPanel(service, namespace string, gridPos GridPos) Panel`

- Type: `"timeseries"`
- Title: `"Latency (P50/P95/P99)"`
- Three targets using `response_latency_ms_bucket` histogram:
  - P50: `histogram_quantile(0.50, sum(rate(response_latency_ms_bucket{namespace="<ns>",deployment="<svc>"}[2m])) by (le))`
  - P95: `histogram_quantile(0.95, ...)`
  - P99: `histogram_quantile(0.99, ...)`
- LegendFormats: `"P50"`, `"P95"`, `"P99"`
- Unit: `"ms"`
- Alert: trigger when P99 > 1000ms for 5 minutes

#### `TCPConnectionsPanel(service, namespace string, gridPos GridPos) Panel`

- Type: `"timeseries"`
- Title: `"TCP Connections (Saturation)"`
- PromQL target:
  ```
  sum(tcp_open_connections{namespace="<namespace>",deployment="<service>"}) by (direction)
  ```
- LegendFormat: `"{{direction}}"`
- Unit: `"conn"`

### `DashboardGenerator` (`generator.go`)

```go
type DashboardGeneratorConfig struct {
    ServiceName string
    Namespace   string
    Tags        []string      // Additional tags beyond default ["linkerd", "service-mesh"]
    RefreshRate string        // Default: "30s"
}

type DashboardGenerator struct {
    config DashboardGeneratorConfig
}

func NewDashboardGenerator(cfg DashboardGeneratorConfig) *DashboardGenerator

func (g *DashboardGenerator) Generate() (*Dashboard, error)
func (g *DashboardGenerator) ToJSON() ([]byte, error)
```

#### `Generate()` Layout

Arrange panels in a 24-column grid:

| Panel             | Type       | GridPos (x, y, w, h)  |
|-------------------|------------|-----------------------|
| Success Rate      | stat       | 0, 0, 6, 4            |
| Request Rate      | timeseries | 6, 0, 18, 8           |
| Latency P50/95/99 | timeseries | 0, 8, 12, 8           |
| TCP Connections   | timeseries | 12, 8, 12, 8          |

#### Dashboard UID Generation

```go
func generateUID(service, namespace string) string {
    hash := sha256.Sum256([]byte(service + "/" + namespace))
    return hex.EncodeToString(hash[:])[:8]
}
```

#### Tags

Always include `["linkerd", "service-mesh"]` plus any tags from `DashboardGeneratorConfig.Tags`. Also add `"ns:" + namespace` and `"svc:" + serviceName`.

## Expected Functionality

- `NewDashboardGenerator(DashboardGeneratorConfig{ServiceName: "web", Namespace: "default"}).ToJSON()` produces valid Grafana dashboard JSON with 4 panels
- The success rate panel PromQL expression contains both `classification="success"` (numerator) and the total (denominator) with the correct service and namespace substituted
- The latency panel has three separate `Target` entries with P50, P95, P99 quantile expressions
- Dashboard UID is deterministic: same service+namespace always produces the same 8-char hex UID
- Tags always include `["linkerd", "service-mesh", "ns:default", "svc:web"]`

## Acceptance Criteria

- `Generate()` produces a `Dashboard` with exactly 4 panels positioned at the correct grid coordinates
- All four panel builders use the correct Linkerd metric names (`response_total`, `response_latency_ms_bucket`, `tcp_open_connections`)
- PromQL expressions correctly substitute `service` and `namespace` values
- `ToJSON()` produces valid JSON that marshals cleanly with no nil pointer panics
- Alert conditions are present on the success rate panel and latency panel
- Dashboard UID is 8 hex characters and deterministic
- `go build ./viz/...` succeeds after changes
- All unit tests pass verifying panel counts, PromQL expressions, grid positions, and UID generation
