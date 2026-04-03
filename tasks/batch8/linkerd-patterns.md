# Task: Implement a Linkerd Service Mesh Configuration Generator

## Background

Linkerd (https://github.com/linkerd/linkerd2) is a lightweight, security-first service mesh for Kubernetes. The project needs a Python tool that generates Linkerd configuration resources — ServiceProfiles, TrafficSplits, Server and ServerAuthorization policies — for common service mesh patterns: per-route metrics and retries, canary traffic splitting, zero-trust authorization, and timeout configuration. The generator must produce valid Linkerd CRD YAML and support multi-service mesh topologies.

## Files to Create/Modify

- `test/python/linkerd_generator.py` (create) — `LinkerdConfigGenerator` class producing ServiceProfile, TrafficSplit, Server, and ServerAuthorization resources
- `test/python/traffic_split.py` (create) — `TrafficSplitManager` class managing progressive traffic splits between service versions with weight validation and rollback support
- `test/python/auth_policy.py` (create) — `AuthorizationPolicyBuilder` class generating Server and ServerAuthorization resources for zero-trust networking with namespace-based and service-account-based identity policies
- `test/python/linkerd_validator.py` (create) — `LinkerdValidator` class checking generated resources for common issues: weight sums, route regex validity, authorization reference consistency, and required annotations
- `tests/test_linkerd_patterns.py` (create) — Tests for resource generation, traffic split management, authorization policies, and validation

## Requirements

### LinkerdConfigGenerator

- Constructor: `LinkerdConfigGenerator(service_name: str, namespace: str, port: int = 80)`
- `generate_service_profile(routes: list[dict]) -> dict`:
  - API version: `linkerd.io/v1alpha2`, kind: `ServiceProfile`
  - `spec.routes`: each route dict has `name` (str), `condition.method` (str, e.g., `"GET"`), `condition.pathRegex` (str), `isRetryable` (bool), `timeout` (str)
  - Example route: `{"name": "GET /api/users", "condition": {"method": "GET", "pathRegex": "/api/users(/.*)?"}, "isRetryable": true, "timeout": "5s"}`
- `generate_server(port: int, proxy_protocol: str = "HTTP/2") -> dict`:
  - API version: `policy.linkerd.io/v1beta1`, kind: `Server`
  - `spec.podSelector` matching `app: {service_name}`
  - `spec.port: {port}`, `spec.proxyProtocol: {proxy_protocol}`
  - Valid protocols: `"HTTP/1"`, `"HTTP/2"`, `"gRPC"`, `"opaque"`; raise `ValueError` otherwise
- `generate_server_authorization(server_name: str, allowed_service_accounts: list[dict] = None, allowed_namespaces: list[str] = None) -> dict`:
  - API version: `policy.linkerd.io/v1beta1`, kind: `ServerAuthorization`
  - `spec.server.name: {server_name}`
  - Client identity: `meshTLS.serviceAccounts` for SA-based auth, or `meshTLS.identities` with namespace matching
  - At least one of `allowed_service_accounts` or `allowed_namespaces` must be provided; raise `ValueError` if neither

### TrafficSplitManager

- Constructor: `TrafficSplitManager(service_name: str, namespace: str, backends: list[dict])`
  - Each backend: `{"service": str, "weight": int}` where weight is 0-1000 (millishares, total must equal 1000)
- `generate_traffic_split() -> dict`:
  - API version: `split.smi-spec.io/v1alpha2`, kind: `TrafficSplit`
  - `spec.service: {service_name}` (apex service)
  - `spec.backends`: list of `{service, weight}` entries
  - Weights must sum to 1000; raise `ValueError("Backend weights must sum to 1000, got {sum}")` otherwise
- `shift_traffic(target_backend: str, target_weight: int) -> dict`:
  - Set `target_backend` to `target_weight`, proportionally redistribute remaining weight among other backends
  - If `target_weight` is 1000, set all others to 0
  - Return the new TrafficSplit resource
- `rollback(stable_backend: str) -> dict` — Route 100% to `stable_backend` (weight 1000, others 0)
- `generate_canary_steps(stable: str, canary: str, step_size: int = 100) -> list[dict]`:
  - Generate a sequence of TrafficSplit resources shifting traffic from stable to canary in `step_size` increments (0, 100, 200, ..., 1000)
  - Return list of TrafficSplit resources representing each step

### AuthorizationPolicyBuilder

- Constructor: `AuthorizationPolicyBuilder(namespace: str)`
- `default_deny(server_name: str) -> list[dict]`:
  - Generate a Server and ServerAuthorization pair that denies all traffic by default (no client identities allowed)
  - The ServerAuthorization has `spec.client.unauthenticated: false` and no identity matches
- `allow_namespace(server_name: str, allowed_namespaces: list[str]) -> dict`:
  - ServerAuthorization allowing traffic from any service account in the specified namespaces
  - Identity pattern: `*.{namespace}.serviceaccount.identity.linkerd.cluster.local`
- `allow_service_accounts(server_name: str, accounts: list[dict]) -> dict`:
  - Each account: `{"name": str, "namespace": str}`
  - ServerAuthorization with explicit `meshTLS.serviceAccounts` entries
- `generate_zero_trust_policy(services: list[dict]) -> list[dict]`:
  - Each service: `{"name": str, "port": int, "allowed_clients": list[dict]}`
  - Generate Server + ServerAuthorization for each service, producing a complete zero-trust mesh policy
  - Return all generated resources as a flat list

### LinkerdValidator

- `validate_service_profile(sp: dict) -> list[str]`:
  - Check route regex compiles: `"Invalid regex in route '{name}': {error}"`
  - Check timeout format: `"Invalid timeout '{value}' in route '{name}'"`
  - Check HTTP method is valid (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS): `"Invalid method '{method}' in route '{name}'"`
- `validate_traffic_split(ts: dict) -> list[str]`:
  - Check weights sum to 1000: `"Backend weights sum to {sum}, expected 1000"`
  - Check no negative weights: `"Negative weight for backend '{service}'"`
  - Check apex service name is set: `"Missing apex service reference"`
- `validate_authorization(sa: dict, servers: list[dict]) -> list[str]`:
  - Check referenced server exists: `"ServerAuthorization references non-existent server '{name}'"`
  - Check at least one identity source: `"No client identity specified"`

## Expected Functionality

- `LinkerdConfigGenerator("api", "default", 8080)` generates ServiceProfiles with per-route metrics for GET/POST endpoints
- `TrafficSplitManager` generates a canary progression from 0% to 100% in 10 steps of 10% each
- `AuthorizationPolicyBuilder.generate_zero_trust_policy()` for 3 services produces 6 resources (3 Servers + 3 ServerAuthorizations)
- `LinkerdValidator` catches a ServiceProfile with invalid route regex and reports the specific regex error

## Acceptance Criteria

- ServiceProfile routes include method conditions, path regex, retry settings, and timeouts
- TrafficSplit resources use SMI spec with millishare weights summing to 1000
- Server and ServerAuthorization resources implement zero-trust patterns with service-account-based identity
- Traffic split progression generates correct weight distributions at each canary step
- Validator catches invalid regex, bad timeout formats, weight sum errors, and missing server references
- All tests pass with `pytest`
