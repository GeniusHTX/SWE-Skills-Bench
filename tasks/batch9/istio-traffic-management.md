# Task: Generate Istio Traffic Management Manifests for a Bookinfo-Style Application

## Background

Istio (https://github.com/istio/istio) provides traffic management for service mesh deployments. A Python tool is needed that generates Istio traffic management manifests (VirtualService, DestinationRule, Gateway, ServiceEntry) for a microservices application, supporting canary deployments with weighted routing, circuit breaker configuration, fault injection for chaos testing, traffic mirroring, and retry/timeout policies.

## Files to Create/Modify

- `tools/istio_gen/generator.py` (create) — `IstioManifestGenerator` class that generates all Istio traffic management resources from a service topology specification
- `tools/istio_gen/models.py` (create) — Pydantic models for service topology, routing rules, circuit breaker config, fault injection config, and canary config
- `tools/istio_gen/routing.py` (create) — `RoutingEngine` that generates `VirtualService` and `DestinationRule` manifests with header-based routing, weighted splits, and subset definitions
- `tools/istio_gen/resilience.py` (create) — `ResilienceEngine` that generates circuit breaker, retry, timeout, and outlier detection configurations within DestinationRules
- `tools/istio_gen/testing.py` (create) — `ChaosEngine` that generates fault injection rules (delays and aborts) and traffic mirroring configurations
- `tools/istio_gen/gateway.py` (create) — `GatewayEngine` that generates `Gateway` and `ServiceEntry` resources for ingress/egress traffic
- `tests/test_istio_generators.py` (create) — Tests for all generators with expected YAML output validation

## Requirements

### Models (`models.py`)

- `ServiceSpec`: `name` (str), `namespace` (str), `port` (int), `protocol` (str: HTTP|HTTPS|gRPC), `versions` (list[VersionSpec])
- `VersionSpec`: `name` (str, e.g., "v1"), `labels` (dict), `weight` (int, percentage)
- `RoutingRule`: `match_headers` (dict[str, str]), `destination_version` (str), `weight` (Optional[int])
- `CircuitBreakerConfig`: `max_connections` (int), `max_pending_requests` (int), `max_retries` (int), `consecutive_errors` (int), `interval_seconds` (int), `base_ejection_time_seconds` (int), `max_ejection_percent` (int)
- `FaultConfig`: `delay_percent` (float), `delay_seconds` (float), `abort_percent` (float), `abort_status` (int)
- `RetryConfig`: `attempts` (int), `per_try_timeout` (str, e.g., "2s"), `retry_on` (str, e.g., "5xx,reset,connect-failure")
- `GatewaySpec`: `name` (str), `hosts` (list[str]), `port` (int), `tls_mode` (Optional[str]: SIMPLE|MUTUAL|PASSTHROUGH), `credential_name` (Optional[str])

### Routing Engine (`routing.py`)

- Method `generate_virtual_service(service: ServiceSpec, rules: list[RoutingRule]) -> dict` — Produces a VirtualService manifest:
  - `apiVersion: networking.istio.io/v1beta1`, `kind: VirtualService`
  - `spec.hosts: [service.name]`
  - `spec.http[]` — one entry per routing rule:
    - If `match_headers` present: add `match[].headers` with `exact` match
    - `route[].destination.host = service.name`, `route[].destination.subset = destination_version`
    - If `weight` present: include weight field
  - Default route (no match) at the end routing to the version with highest weight
- Method `generate_destination_rule(service: ServiceSpec) -> dict` — Produces a DestinationRule manifest:
  - `spec.host: service.name`
  - `spec.subsets[]` — one per version with `name` and `labels`
  - `spec.trafficPolicy.connectionPool.tcp.maxConnections: 100` (default)
- Weights across all routes for a single match must sum to 100

### Resilience Engine (`resilience.py`)

- Method `apply_circuit_breaker(dest_rule: dict, config: CircuitBreakerConfig) -> dict` — Adds to the DestinationRule:
  - `spec.trafficPolicy.connectionPool.tcp.maxConnections`
  - `spec.trafficPolicy.connectionPool.http.h2UpgradePolicy: DEFAULT`
  - `spec.trafficPolicy.connectionPool.http.maxRequestsPerConnection: 1`
  - `spec.trafficPolicy.outlierDetection.consecutive5xxErrors: config.consecutive_errors`
  - `spec.trafficPolicy.outlierDetection.interval: <config.interval_seconds>s`
  - `spec.trafficPolicy.outlierDetection.baseEjectionTime: <config.base_ejection_time_seconds>s`
  - `spec.trafficPolicy.outlierDetection.maxEjectionPercent: config.max_ejection_percent`
- Method `apply_retry_policy(virtual_service: dict, config: RetryConfig) -> dict` — Adds to each `http[]` route:
  - `retries.attempts`, `retries.perTryTimeout`, `retries.retryOn`
- Method `apply_timeout(virtual_service: dict, timeout: str) -> dict` — Adds `timeout` field to each `http[]` route

### Chaos Engine (`testing.py`)

- Method `inject_fault(virtual_service: dict, config: FaultConfig, target_route_index: int = 0) -> dict` — Adds `fault` block to specified route:
  - `fault.delay.percentage.value: config.delay_percent`, `fault.delay.fixedDelay: <config.delay_seconds>s`
  - `fault.abort.percentage.value: config.abort_percent`, `fault.abort.httpStatus: config.abort_status`
  - Either delay or abort can be omitted if their percent is 0
- Method `add_mirror(virtual_service: dict, mirror_service: str, mirror_percent: float) -> dict` — Adds traffic mirroring:
  - `mirror.host: mirror_service`, `mirrorPercentage.value: mirror_percent`

### Gateway Engine (`gateway.py`)

- Method `generate_gateway(spec: GatewaySpec) -> dict` — Produces a Gateway manifest:
  - `apiVersion: networking.istio.io/v1beta1`, `kind: Gateway`
  - `spec.selector.istio: ingressgateway`
  - `spec.servers[].port.number`, `spec.servers[].port.protocol`
  - `spec.servers[].hosts` from spec
  - If TLS mode specified: `spec.servers[].tls.mode` and `spec.servers[].tls.credentialName`
- Method `generate_service_entry(name, hosts, ports, resolution="DNS") -> dict` — Produces a ServiceEntry for external services

### Expected Functionality

- Generating routing for service "reviews" with versions v1 (80%) and v2 (20%) produces a VirtualService with weighted routes summing to 100
- Circuit breaker config with 5 consecutive errors and 30s ejection produces correct outlier detection in DestinationRule
- Fault injection with 10% delay of 5s adds the correct fault block to the VirtualService
- Traffic mirroring to "reviews-shadow" at 50% adds mirror and mirrorPercentage fields
- Gateway with TLS SIMPLE mode includes tls block with credentialName

## Acceptance Criteria

- All generated manifests use `apiVersion: networking.istio.io/v1beta1`
- VirtualService routes have weights summing to 100 for each match group
- DestinationRule subsets correctly map version labels
- Circuit breaker outlier detection fields use correct Istio duration format (e.g., `"30s"`)
- Fault injection correctly handles delay-only, abort-only, and combined scenarios
- Gateway TLS configuration is present only when tls_mode is specified
- All manifests are valid YAML parseable by `yaml.safe_load`
- `python -m pytest /workspace/tests/test_istio_traffic_management.py -v --tb=short` passes
