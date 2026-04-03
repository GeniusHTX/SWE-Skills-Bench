# Task: Implement an Istio Traffic Management Configuration Generator

## Background

Istio (https://github.com/istio/istio) is a service mesh that provides traffic management, security, and observability for microservices. The project needs a Python tool that generates Istio traffic management resources — VirtualServices, DestinationRules, Gateways, and ServiceEntries — for common deployment patterns: canary releases, blue-green deployments, circuit breaking, fault injection, and traffic mirroring. The tool must produce valid Istio CRD YAML and validate configurations against common pitfalls.

## Files to Create/Modify

- `tests/python/istio_generator.py` (create) — `IstioTrafficGenerator` class producing VirtualService, DestinationRule, Gateway, and ServiceEntry resources from a high-level deployment specification
- `tests/python/canary_manager.py` (create) — `CanaryManager` class generating progressive traffic shifting configurations: initial canary split, intermediate steps, full rollout, and rollback configurations
- `tests/python/resilience_config.py` (create) — `ResilienceConfig` class generating circuit breaker settings (outlier detection, connection pool limits), retry policies, timeout configurations, and fault injection rules
- `tests/python/istio_validator.py` (create) — `IstioValidator` class checking generated resources for common errors: subset references matching DestinationRule definitions, weight sums equaling 100, valid timeout formats, and consistent host references
- `tests/test_istio_traffic_management.py` (create) — Tests for resource generation, canary progression, resilience configuration, and validation rules

## Requirements

### IstioTrafficGenerator

- Constructor: `IstioTrafficGenerator(service_name: str, namespace: str, versions: list[str])`
- `generate_destination_rule(lb_policy: str = "ROUND_ROBIN", connection_pool: dict = None) -> dict`:
  - API version: `networking.istio.io/v1beta1`, kind: `DestinationRule`
  - Create one subset per version, each with label `version: {v}`
  - Load balancing: `trafficPolicy.loadBalancer.simple: {lb_policy}`
  - Connection pool defaults: `maxConnections: 100`, `http1MaxPendingRequests: 100`, `http2MaxRequests: 1000`
  - Valid `lb_policy` values: `"ROUND_ROBIN"`, `"LEAST_CONN"`, `"RANDOM"`, `"PASSTHROUGH"`; raise `ValueError` otherwise
- `generate_virtual_service(weights: dict[str, int], match_rules: list[dict] = None) -> dict`:
  - Route traffic to subsets based on `weights` dict (e.g., `{"v1": 90, "v2": 10}`)
  - Weights must sum to 100; raise `ValueError` if not
  - Optional `match_rules`: list of `{"header": str, "value": str, "subset": str}` for header-based routing (matched before weighted routes)
  - Include `retries: {attempts: 3, perTryTimeout: "2s", retryOn: "gateway-error,connect-failure,refused-stream"}`
- `generate_gateway(hosts: list[str], tls_mode: str = "SIMPLE", credential_name: str = None) -> dict`:
  - Gateway with server on port 443 (HTTPS) and port 80 (HTTP redirect)
  - TLS modes: `"SIMPLE"`, `"MUTUAL"`, `"PASSTHROUGH"`; SIMPLE and MUTUAL require `credential_name`
  - Port 80 server with `httpsRedirect: true`
- `generate_service_entry(host: str, ports: list[dict], resolution: str = "DNS") -> dict`:
  - ServiceEntry for external services with `location: MESH_EXTERNAL`
  - Each port: `{"number": int, "name": str, "protocol": str}`

### CanaryManager

- Constructor: `CanaryManager(service_name: str, namespace: str, stable_version: str, canary_version: str)`
- `generate_steps(increments: list[int] = [10, 25, 50, 75, 100]) -> list[dict]`:
  - For each increment, generate a VirtualService with `canary: increment, stable: 100-increment`
  - Return list of VirtualService resources representing the progression
- `generate_rollback() -> dict` — VirtualService routing 100% to stable
- `generate_with_analysis(canary_weight: int, error_rate_threshold: float = 0.01) -> dict`:
  - VirtualService with header-based override: requests with `x-canary: true` always go to canary
  - Include annotation `canary.analysis/error-threshold: "{error_rate_threshold}"`
  - Add timeout of `"10s"` and retry policy for canary subset
- `current_step(canary_weight: int) -> int` — Return the step index (0-based) in the increment list closest to `canary_weight`

### ResilienceConfig

- `circuit_breaker(consecutive_errors: int = 5, interval: str = "10s", base_ejection_time: str = "30s", max_ejection_percent: int = 50) -> dict`:
  - DestinationRule `trafficPolicy.outlierDetection` configuration
  - `consecutiveGatewayErrors: {consecutive_errors}`
  - `splitExternalLocalOriginErrors: true`
- `retry_policy(attempts: int = 3, per_try_timeout: str = "2s", retry_on: str = "gateway-error,connect-failure,refused-stream") -> dict`:
  - Returns a retry configuration dict for inclusion in VirtualService routes
- `timeout(value: str = "10s") -> dict` — Returns timeout configuration
- `fault_injection(delay_percent: float = None, delay_duration: str = None, abort_percent: float = None, abort_code: int = None) -> dict`:
  - Generate fault injection config for VirtualService
  - At least one of delay or abort must be specified; raise `ValueError` if neither
  - `delay_percent` and `abort_percent` must be between 0 and 100
- `rate_limit(max_requests: int, window: str = "60s") -> dict`:
  - Generate EnvoyFilter for local rate limiting with `max_requests` per `window`

### IstioValidator

- `validate_virtual_service(vs: dict, destination_rules: list[dict]) -> list[str]`:
  - Check all referenced subsets exist in destination rules: `"Subset '{subset}' not found in DestinationRule for host '{host}'"`
  - Check route weights sum to 100: `"Route weights sum to {sum}, expected 100"`
  - Check timeout format matches `"[0-9]+[smh]"`: `"Invalid timeout format: '{value}'"`
- `validate_destination_rule(dr: dict) -> list[str]`:
  - Check all subsets have unique names: `"Duplicate subset name: '{name}'"`
  - Check load balancer policy is valid: `"Invalid load balancer policy: '{policy}'"`
- `validate_gateway(gw: dict) -> list[str]`:
  - Check TLS credential present when required: `"TLS mode '{mode}' requires credentialName"`
  - Check no duplicate port numbers: `"Duplicate port: {port}"`
- `validate_all(resources: list[dict]) -> dict` — Validate all resources and return `{valid_count, invalid_count, errors: list}`

## Expected Functionality

- `IstioTrafficGenerator("reviews", "bookinfo", ["v1", "v2", "v3"])` generates resources for the Bookinfo example with 3 version subsets
- `CanaryManager.generate_steps([10, 25, 50, 100])` produces 4 VirtualService configs progressively shifting traffic from v1 to v2
- `ResilienceConfig.circuit_breaker(consecutive_errors=5)` generates outlier detection config ejecting backends after 5 consecutive gateway errors
- `IstioValidator` catches a VirtualService referencing subset "v4" that does not exist in any DestinationRule

## Acceptance Criteria

- Generated VirtualService, DestinationRule, Gateway, and ServiceEntry resources use correct Istio API versions and structure
- Canary progression generates valid weight distributions summing to 100 at each step
- Circuit breaker, retry, timeout, and fault injection configurations follow Istio's specification
- Validator catches missing subsets, invalid weights, bad timeout formats, and missing TLS credentials
- All tests pass with `pytest`
