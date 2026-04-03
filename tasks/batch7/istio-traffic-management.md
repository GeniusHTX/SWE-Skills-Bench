# Task: Implement a Canary Deployment Traffic Controller in Istio

## Background

Istio (https://github.com/istio/istio) is a service mesh platform. The task is to implement a Go controller within the Istio pilot component that manages progressive canary deployments: it creates and updates `VirtualService` and `DestinationRule` resources to gradually shift traffic from a stable version to a canary version based on configurable weight steps, with automatic rollback triggered by error rate thresholds.

## Files to Create/Modify

- `pilot/pkg/canary/controller.go` (create) — `CanaryController` that manages `VirtualService` and `DestinationRule` resources for progressive traffic shifting
- `pilot/pkg/canary/types.go` (create) — Type definitions for `CanaryDeployment` configuration and state
- `pilot/pkg/canary/rollback.go` (create) — `RollbackManager` that monitors error rates and triggers automatic rollback
- `pilot/pkg/canary/controller_test.go` (create) — Unit tests for the canary controller
- `pilot/pkg/canary/rollback_test.go` (create) — Unit tests for the rollback manager

## Requirements

### Type Definitions (`types.go`)

```go
type CanaryDeployment struct {
    Name           string
    Namespace      string
    ServiceName    string
    StableVersion  string        // e.g., "v1"
    CanaryVersion  string        // e.g., "v2"
    StableSubset   string        // DestinationRule subset name for stable
    CanarySubset   string        // DestinationRule subset name for canary
    Steps          []TrafficStep
    CurrentStep    int
    Status         CanaryStatus
    ErrorThreshold float64       // Max error rate (0.0-1.0) before rollback
    MetricWindow   time.Duration // Time window for error rate calculation
}

type TrafficStep struct {
    CanaryWeight int           // 0-100 percentage
    StableWeight int           // 0-100 percentage (= 100 - CanaryWeight)
    Duration     time.Duration // How long to hold at this step before advancing
}

type CanaryStatus string

const (
    CanaryStatusProgressing CanaryStatus = "Progressing"
    CanaryStatusPaused      CanaryStatus = "Paused"
    CanaryStatusCompleted   CanaryStatus = "Completed"
    CanaryStatusRolledBack  CanaryStatus = "RolledBack"
    CanaryStatusFailed      CanaryStatus = "Failed"
)

type CanaryState struct {
    CurrentStep       int
    CurrentCanaryWeight int
    Status            CanaryStatus
    LastTransitionTime time.Time
    ErrorRate         float64
    Message           string
}
```

### `CanaryController` (`controller.go`)

```go
type CanaryController struct {
    // dependencies
}

func NewCanaryController(istioClient istioclient.Interface, metricsProvider MetricsProvider) *CanaryController
```

#### Methods

- `Start(deployment CanaryDeployment) (*CanaryState, error)`:
  1. Validate the deployment configuration (steps must sum to 100 for each weight pair, versions must differ)
  2. Create or update a `DestinationRule` with two subsets: `StableSubset` selecting pods with label `version: <StableVersion>`, `CanarySubset` selecting pods with label `version: <CanaryVersion>`
  3. Create or update a `VirtualService` routing traffic with the first step's weights
  4. Set status to `Progressing` at step 0
  5. Return the initial `CanaryState`

- `Advance(deployment *CanaryDeployment) (*CanaryState, error)`:
  1. Move to the next step in the `Steps` array
  2. Update the `VirtualService` with the new weights
  3. If this was the last step (100% canary), set status to `Completed` and update the `VirtualService` to route all traffic to the canary subset
  4. Return the updated state

- `Rollback(deployment *CanaryDeployment, reason string) (*CanaryState, error)`:
  1. Update the `VirtualService` to route 100% traffic to the stable subset
  2. Set status to `RolledBack`
  3. Record the reason in the state message
  4. Return the updated state

- `GetState(deployment *CanaryDeployment) *CanaryState`:
  - Return the current state including step, weight, status, error rate

- `GenerateVirtualService(deployment *CanaryDeployment) *networkingv1alpha3.VirtualService`:
  - Generate the VirtualService spec with:
    - Host: `deployment.ServiceName`
    - HTTP route with two destinations: stable subset at `StableWeight`, canary subset at `CanaryWeight`
    - Both destinations reference the same host with different subset labels

- `GenerateDestinationRule(deployment *CanaryDeployment) *networkingv1alpha3.DestinationRule`:
  - Generate the DestinationRule spec with:
    - Host: `deployment.ServiceName`
    - Two subsets with version label selectors
    - Default traffic policy with outlier detection: `consecutiveErrors: 5`, `interval: 10s`, `baseEjectionTime: 30s`

### `RollbackManager` (`rollback.go`)

```go
type MetricsProvider interface {
    GetErrorRate(service, subset, namespace string, window time.Duration) (float64, error)
    GetLatencyP99(service, subset, namespace string, window time.Duration) (time.Duration, error)
    GetRequestRate(service, subset, namespace string, window time.Duration) (float64, error)
}

type RollbackManager struct {
    metricsProvider MetricsProvider
    controller      *CanaryController
}
```

#### `CheckAndRollback(deployment *CanaryDeployment) (*CanaryState, bool, error)`

1. Query the `metricsProvider` for the canary subset's error rate over the `MetricWindow`
2. If `errorRate > deployment.ErrorThreshold`:
   a. Call `controller.Rollback` with reason `"error rate <X>% exceeded threshold <Y>%"`
   b. Return `(state, true, nil)` indicating rollback was triggered
3. If error rate is within threshold, return `(state, false, nil)`
4. If metrics are unavailable (provider returns error), do NOT rollback — return the error for the caller to handle

### Configuration Defaults

- Default steps if none provided: `[{10%, 90%, 5m}, {25%, 75%, 5m}, {50%, 50%, 10m}, {75%, 25%, 10m}, {100%, 0%, 0}]`
- Default error threshold: `0.05` (5%)
- Default metric window: `1m`

## Expected Functionality

- Starting a canary with steps `[10/90, 50/50, 100/0]`:
  1. `Start` creates a VirtualService with 10% canary / 90% stable
  2. First `Advance` updates to 50% / 50%
  3. Second `Advance` updates to 100% / 0% and sets status to `Completed`

- If error rate is 8% with threshold 5%: `CheckAndRollback` triggers rollback to 100% stable

- `GenerateVirtualService` produces a valid Istio VirtualService with correct weight routing

## Acceptance Criteria

- `Start` creates valid DestinationRule and VirtualService with correct subset labels and weights
- `Advance` correctly increments through traffic steps and updates VirtualService weights
- `Rollback` immediately routes 100% traffic to stable and records the reason
- `GenerateVirtualService` and `GenerateDestinationRule` produce valid Istio API objects
- `RollbackManager` triggers rollback when error rate exceeds threshold
- `RollbackManager` does NOT rollback when metrics are unavailable (returns error)
- Weights in each step sum to 100
- All edge cases handled: single-step deployment, already completed, already rolled back
- All unit tests pass with mock Istio clients and mock metrics providers
