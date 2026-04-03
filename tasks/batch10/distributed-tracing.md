# Task: Implement Tail Sampling Processor in OpenTelemetry Collector

## Background
The OpenTelemetry Collector (`open-telemetry/opentelemetry-collector`) routes telemetry through a pipeline defined in `service/`. The `processor/` directory houses processors such as `batchprocessor`. A tail-based sampling processor is needed that buffers complete traces by trace ID for a configurable wait period, applies a probabilistic sampling decision after all spans for a trace have arrived, and forwards sampled traces to the next consumer while preserving W3C `traceparent` context intact.

## Files to Create/Modify
- `processor/tailsamplingprocessor/config.go` - `Config` struct with validation (new)
- `processor/tailsamplingprocessor/processor.go` - `tailSamplingProcessor` implementing `processor.Traces` (new)
- `processor/tailsamplingprocessor/factory.go` - `NewFactory()` registering component type `"tailsampling"` (new)
- `processor/tailsamplingprocessor/processor_test.go` - Unit tests (new)

## Requirements

### Config (`config.go`)
- `Config` struct with three exported fields:
  - `DecisionWait time.Duration` — buffer duration before sampling decision; default `30 * time.Second`
  - `NumTraces uint64` — maximum traces buffered in memory; default `50000`
  - `SamplingRate float64` — fraction of traces to forward; range `[0.0, 1.0]`; default `1.0`
- `Validate() error` must return a non-nil error if `SamplingRate < 0.0` or `SamplingRate > 1.0`
- `Validate()` must return a non-nil error if `DecisionWait <= 0`

### Factory (`factory.go`)
- `NewFactory() processor.Factory` registers component type string `"tailsampling"`
- `createDefaultConfig()` returns `&Config{DecisionWait: 30 * time.Second, NumTraces: 50000, SamplingRate: 1.0}`
- Factory must register `CreateTracesProcessor` using `processor.WithTraces`
- `createTracesProcessor` must call `cfg.Validate()` and return the error if validation fails

### Processor (`processor.go`)
- Struct `tailSamplingProcessor` holds a `nextConsumer consumer.Traces`, a `Config`, a mutex-protected map from `pcommon.TraceID` to `ptrace.Traces`, and a `*rand.Rand` seeded at construction time
- `ConsumeTraces(ctx context.Context, td ptrace.Traces) error`:
  - Group incoming resource spans by trace ID using `ptrace.Span.TraceID()`
  - After `DecisionWait` elapses since a trace's first span was buffered, call `r.Float64() < cfg.SamplingRate` to decide; forward if true, discard if false
  - Preserve `span.TraceState()` string on forwarded spans unchanged
  - Evict the trace buffered longest when `len(buffer) >= NumTraces` before inserting a new trace
- `Capabilities()` must return `consumer.Capabilities{MutatesData: false}`

### Unit Tests (`processor_test.go`)
- `TestConfigValidation_InvalidSamplingRate`: `Config{SamplingRate: 1.5, DecisionWait: time.Second}` → `Validate()` returns non-nil
- `TestConfigValidation_NegativeSamplingRate`: `Config{SamplingRate: -0.1, DecisionWait: time.Second}` → `Validate()` returns non-nil
- `TestConfigValidation_ZeroDecisionWait`: `Config{SamplingRate: 1.0, DecisionWait: 0}` → `Validate()` returns non-nil
- `TestConsumeTraces_ForwardAll`: `SamplingRate=1.0`, send a `ptrace.Traces` with 5 spans sharing one trace ID → all 5 spans present in next consumer
- `TestConsumeTraces_DropAll`: `SamplingRate=0.0`, send 5 spans → next consumer receives 0 spans
- `TestTraceStatePassthrough`: construct a span with `TraceState` set to `"vendor=abc"`; `SamplingRate=1.0`; assert forwarded span `TraceState() == "vendor=abc"`

### Expected Functionality
- `SamplingRate=1.0` → every trace forwarded after `DecisionWait`
- `SamplingRate=0.0` → no traces forwarded
- `SamplingRate=1.5` → factory `createTracesProcessor` returns error, processor not created
- `tracestate` header on input spans is unchanged on forwarded spans
- Buffer at capacity → oldest trace evicted before new trace inserted

## Acceptance Criteria
- `go test ./processor/tailsamplingprocessor/... -v` passes all 6 tests
- `NewFactory().Type()` returns `component.MustNewType("tailsampling")`
- `tailSamplingProcessor` uses its own `rand.New(rand.NewSource(time.Now().UnixNano()))` instance; no calls to `math/rand` package-level functions
- `processor.go` imports `go.opentelemetry.io/collector/pdata/ptrace` and `go.opentelemetry.io/collector/pdata/pcommon`
- `Validate()` is invoked inside `createTracesProcessor` before the processor struct is allocated
- `go build ./processor/tailsamplingprocessor/...` succeeds with no errors
