# Task: Add Linkerd TCP Metrics Collection Example

## Background
   Add TCP connection metrics collection
   example demonstrating service mesh observability features for TCP
   workloads in the Linkerd2 repository.

## Files to Create/Modify
   - viz/metrics-api/examples/tcp_metrics_demo.go (demo code)
   - viz/metrics-api/examples/README.md (documentation)
   - viz/metrics-api/tcp_metrics_test.go (tests)

## Requirements
   
   TCP Metrics Demo (tcp_metrics_demo.go):
   - Connection establishment metrics
   - Bytes sent/received counters
   - Connection duration tracking
   - Error rate monitoring
   
   Metrics to Collect:
   - tcp_open_total: Total TCP connections opened
   - tcp_close_total: Total TCP connections closed
   - tcp_connection_duration_ms: Connection duration histogram
   - tcp_read_bytes_total: Total bytes read
   - tcp_write_bytes_total: Total bytes written
   
   Integration Points:
   - Prometheus metric exposition
   - Grafana dashboard configuration
   - Linkerd proxy integration

4. Test Coverage:
   - Metric counter increments correctly
   - Duration histogram bucketing
   - Label cardinality validation
   - Thread-safe metric updates

## Acceptance Criteria
   - `go build ./viz/...` exits with code 0
   - `go test ./viz/metrics-api/...` passes
   - Metrics follow Linkerd naming conventions
