# Task: Implement a Tail Sampling Processor for the OpenTelemetry Collector

## Background

The OpenTelemetry Collector (https://github.com/open-telemetry/opentelemetry-collector) is a Go-based telemetry pipeline that processes traces, metrics, and logs. The task is to implement a new `tailsamplingprocessor` component that buffers complete traces in memory and makes sampling decisions based on configurable per-trace policies (error presence, latency threshold, and service name matching), forwarding only selected traces to the next pipeline stage.

## Files to Create/Modify

- `processor/tailsamplingprocessor/processor.go` (create) — `tailSamplingProcessor` implementing `component.Component` and `consumer.Traces`
- `processor/tailsamplingprocessor/config.go` (create) — Configuration struct with policy definitions
- `processor/tailsamplingprocessor/policy.go` (create) — `SamplingPolicy` interface and built-in policy implementations
- `processor/tailsamplingprocessor/trace_buffer.go` (create) — In-memory trace buffer indexed by trace ID
- `processor/tailsamplingprocessor/processor_test.go` (create) — Unit tests for the processor and policies
- `processor/tailsamplingprocessor/factory.go` (create) — `NewFactory()` to register the component with the Collector

## Requirements

### Configuration (`config.go`)

```go
type PolicyType string

const (
    PolicyAlwaysSample    PolicyType = "always_sample"
    PolicyNeverSample     PolicyType = "never_sample"  
    PolicyStatusCodeError PolicyType = "status_code"
    PolicyLatency         PolicyType = "latency"
    PolicyServiceName     PolicyType = "service_name"
)

type PolicyConfig struct {
    Name string     `mapstructure:"name"`
    Type PolicyType `mapstructure:"type"`
    
    // Populated based on Type:
    StatusCode  *StatusCodePolicyConfig  `mapstructure:"status_code,omitempty"`
    Latency     *LatencyPolicyConfig     `mapstructure:"latency,omitempty"`
    ServiceName *ServiceNamePolicyConfig `mapstructure:"service_name,omitempty"`
}

type StatusCodePolicyConfig struct {
    StatusCodes []string `mapstructure:"status_codes"` // "ERROR", "UNSET", "OK"
}

type LatencyPolicyConfig struct {
    ThresholdMs int64 `mapstructure:"threshold_ms"` // Sample if trace duration > threshold
}

type ServiceNamePolicyConfig struct {
    ServiceNames []string `mapstructure:"service_names"` // Sample only these services
}

type Config struct {
    DecisionWait     time.Duration  `mapstructure:"decision_wait"`      // Buffer window before deciding (default: 30s)
    MaxBatchSize     int            `mapstructure:"max_batch_size"`     // Max spans per buffered trace
    NumTraces        int            `mapstructure:"num_traces"`         // Max traces in buffer (default: 50000)
    Policies         []PolicyConfig `mapstructure:"policies"`
    PolicyEvaluation string         `mapstructure:"policy_evaluation"`  // "any" or "all" (default: "any")
}
```

### Sampling Policies (`policy.go`)

```go
type SamplingDecision int

const (
    Pending       SamplingDecision = iota
    Sampled
    NotSampled
)

type TraceData struct {
    TraceID    pcommon.TraceID
    Spans      []ptrace.Span
    ReceivedAt time.Time
    RootSpan   ptrace.Span   // Span with no parent
}

type SamplingPolicy interface {
    Evaluate(trace *TraceData) SamplingDecision
    Name() string
}
```

Implement these four policies:

**`StatusCodePolicy`**: Samples traces where at least one span has a status code matching any of the configured `StatusCodes` list. StatusCode values are `"ERROR"`, `"OK"`, `"UNSET"`. Returns `Sampled` if match found, `Pending` otherwise.

**`LatencyPolicy`**: Computes trace duration as `max(span.EndTime) - min(span.StartTime)` across all spans in the trace. Returns `Sampled` if duration > `ThresholdMs` milliseconds, `Pending` otherwise.

**`ServiceNamePolicy`**: Samples traces where any span's `service.name` resource attribute matches any name in `ServiceNames`. Returns `Sampled` if match found, `NotSampled` (exclude) otherwise — this is an allowlist policy.

**`AlwaysSamplePolicy`**: Always returns `Sampled`.

### `TraceBuffer` (`trace_buffer.go`)

```go
type TraceBuffer struct {
    mu       sync.RWMutex
    traces   map[pcommon.TraceID]*TraceData
    maxSize  int
}

func NewTraceBuffer(maxSize int) *TraceBuffer
func (b *TraceBuffer) Add(traceID pcommon.TraceID, spans []ptrace.Span) bool
func (b *TraceBuffer) Get(traceID pcommon.TraceID) (*TraceData, bool)
func (b *TraceBuffer) Delete(traceID pcommon.TraceID)
func (b *TraceBuffer) Evict() int  // Evict oldest traces if over maxSize, return count evicted
func (b *TraceBuffer) Size() int
```

- Thread-safe: all methods use `sync.RWMutex`
- `Add` returns `false` if the buffer is at `maxSize` after the add (used to trigger eviction)
- `Evict` removes the oldest 10% of traces (by `ReceivedAt`) when called

### `tailSamplingProcessor` (`processor.go`)

```go
type tailSamplingProcessor struct {
    config       Config
    policies     []SamplingPolicy
    buffer       *TraceBuffer
    nextConsumer consumer.Traces
    ticker       *time.Ticker
    logger       *zap.Logger
    stopCh       chan struct{}
}

func newTailSamplingProcessor(cfg Config, next consumer.Traces, logger *zap.Logger) (*tailSamplingProcessor, error)
```

#### `ConsumeTraces(ctx context.Context, td ptrace.Traces) error`

1. For each `ResourceSpans` in `td`:
   - Group spans by trace ID
   - Add each group to the `TraceBuffer`
2. Return nil (decisions are made asynchronously)

#### `makeDecisions()`

Runs on a `time.Ticker` every second. For each trace in the buffer where `time.Since(trace.ReceivedAt) >= config.DecisionWait`:

1. Evaluate each policy in `config.Policies`:
   - If `PolicyEvaluation == "any"` and any policy returns `Sampled` → forward trace, remove from buffer
   - If `PolicyEvaluation == "all"` and all policies return `Sampled` → forward trace, remove from buffer
   - If any policy returns `NotSampled` (for allowlist policies) → drop trace, remove from buffer
   - If all policies return `Pending` after the wait window → drop trace (default: not sampled)

2. Rebuild a `ptrace.Traces` from the buffered spans and call `nextConsumer.ConsumeTraces`

#### `Start` / `Shutdown`

- `Start` launches the `makeDecisions` goroutine
- `Shutdown` closes `stopCh` to stop the goroutine and flushes remaining buffered traces

### Factory (`factory.go`)

```go
func NewFactory() processor.Factory {
    return processor.NewFactory(
        "tail_sampling",
        createDefaultConfig,
        processor.WithTraces(createTracesProcessor, component.StabilityLevelAlpha),
    )
}
```

Default config: `DecisionWait: 30s`, `NumTraces: 50000`, `PolicyEvaluation: "any"`.

## Expected Functionality

- A trace with one span having StatusCode `ERROR` is sampled by `StatusCodePolicy(["ERROR"])`
- A trace spanning 250ms is sampled by `LatencyPolicy(ThresholdMs: 200)`
- A trace from service `"payment-service"` is sampled by `ServiceNamePolicy(["payment-service", "auth-service"])`
- A trace from service `"unknown-service"` is dropped by `ServiceNamePolicy(["payment-service"])`
- With `PolicyEvaluation: "all"`, a trace must satisfy ALL policies to be forwarded
- Traces not decided within `DecisionWait` are dropped by default

## Acceptance Criteria

- `ConsumeTraces` correctly groups spans by trace ID and buffers them
- `StatusCodePolicy`, `LatencyPolicy`, `ServiceNamePolicy`, and `AlwaysSamplePolicy` return correct decisions
- `makeDecisions` applies `PolicyEvaluation: "any"` and `"all"` logic correctly
- `TraceBuffer` is thread-safe and evicts correctly when over `maxSize`
- Traces are forwarded to `nextConsumer` as valid `ptrace.Traces` objects
- `Start` and `Shutdown` correctly manage the decision goroutine
- `NewFactory()` registers the component under the `"tail_sampling"` type name
- All unit tests pass with mock consumers and synthetic trace data
