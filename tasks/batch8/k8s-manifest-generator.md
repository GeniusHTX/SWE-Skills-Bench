# Task: Build a Kubernetes Manifest Generator with Kustomize Overlay Support

## Background

Kustomize (https://github.com/kubernetes-sigs/kustomize) is a tool for customizing Kubernetes configurations. The project needs a Python library that programmatically generates production-ready Kubernetes manifests (Deployments, Services, ConfigMaps, Ingress, HPA) following best practices: resource limits, health checks, security contexts, and anti-affinity rules. The generator must support Kustomize-style base + overlay composition for multi-environment deployments.

## Files to Create/Modify

- `tests/python/manifest_generator.py` (create) — `ManifestGenerator` class producing Deployment, Service, ConfigMap, Ingress, and HPA manifests from a declarative application specification
- `tests/python/kustomize_builder.py` (create) — `KustomizeBuilder` class creating Kustomize directory structures with base manifests and per-environment overlays that patch replicas, images, resource limits, and ConfigMap values
- `tests/python/security_policies.py` (create) — `SecurityPolicyGenerator` class adding security contexts (non-root, read-only filesystem, dropped capabilities), NetworkPolicy resources, and PodDisruptionBudget resources
- `tests/python/manifest_validator.py` (create) — `ManifestValidator` class checking generated manifests against best practices: required labels, resource limits present, health checks defined, image tags not `latest`, and no privileged containers
- `tests/test_k8s_manifest_generator.py` (create) — Tests for manifest generation, Kustomize overlay merging, security policy application, and validation rules

## Requirements

### ManifestGenerator

- Constructor: `ManifestGenerator(app_name: str, namespace: str, image: str, port: int)`
- `generate_deployment(replicas: int = 3, env_vars: dict = None, resources: dict = None) -> dict`:
  - Standard Deployment structure with `apiVersion: apps/v1`
  - Labels: `app: {app_name}`, `version: {image_tag}`, `managed-by: manifest-generator`
  - Container resources default: `requests: {cpu: "100m", memory: "128Mi"}`, `limits: {cpu: "500m", memory: "512Mi"}`
  - Liveness probe: HTTP GET on `port` at `/healthz`, `initialDelaySeconds: 15`, `periodSeconds: 20`
  - Readiness probe: HTTP GET on `port` at `/ready`, `initialDelaySeconds: 5`, `periodSeconds: 10`
  - Strategy: `RollingUpdate` with `maxSurge: 1`, `maxUnavailable: 0`
  - Pod anti-affinity: prefer spreading across nodes using `app` label
- `generate_service(service_type: str = "ClusterIP") -> dict`:
  - Standard Service targeting pods with `app: {app_name}` label selector
  - Port mapping: `port: 80`, `targetPort: {port}`, `protocol: TCP`
  - If `service_type` is `"LoadBalancer"`, add annotation `service.beta.kubernetes.io/aws-load-balancer-type: nlb`
- `generate_configmap(data: dict) -> dict`:
  - ConfigMap with `{app_name}-config` name in the correct namespace
  - All values must be strings; non-string values are converted using `str()`
- `generate_ingress(host: str, tls: bool = True, annotations: dict = None) -> dict`:
  - Ingress with `networking.k8s.io/v1` API version
  - Single rule mapping `host` to the service on port 80
  - If `tls=True`, add TLS section with `secretName: {app_name}-tls`
  - Default annotations: `kubernetes.io/ingress.class: nginx`
- `generate_hpa(min_replicas: int = 2, max_replicas: int = 10, cpu_target: int = 70) -> dict`:
  - HPA targeting the Deployment with CPU utilization metric
  - `apiVersion: autoscaling/v2`

### KustomizeBuilder

- Constructor: `KustomizeBuilder(base_dir: str)`
- `create_base(generator: ManifestGenerator, replicas: int = 3) -> dict`:
  - Generate all manifests (Deployment, Service, ConfigMap) and a `kustomization.yaml` listing them as resources
  - Return the kustomization dict with `resources` list
- `create_overlay(env_name: str, patches: dict) -> dict`:
  - `patches` can include: `replicas` (int), `image` (str), `resources` (dict), `env_vars` (dict), `configmap_data` (dict)
  - Generate a `kustomization.yaml` for the overlay with `bases: ["../../base"]` and appropriate strategic merge patches or JSON patches
  - `replicas` patch: `[{"op": "replace", "path": "/spec/replicas", "value": N}]`
  - `image` patch: `images: [{name: old_image, newName: new_image, newTag: tag}]`
  - `configmap_data` patch: `configMapGenerator` with merge behavior
- `render_overlay(env_name: str) -> list[dict]` — Simulate Kustomize rendering by merging base manifests with overlay patches; return the final list of manifests
- Supported environments: `"dev"`, `"staging"`, `"production"`

### SecurityPolicyGenerator

- `add_security_context(deployment: dict) -> dict` — Modify deployment in-place:
  - Pod-level: `runAsNonRoot: true`, `fsGroup: 65534`, `seccompProfile: {type: RuntimeDefault}`
  - Container-level: `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `capabilities: {drop: ["ALL"]}`
  - Add `emptyDir` volume mount at `/tmp` for writable temp directory
- `generate_network_policy(app_name: str, namespace: str, allowed_namespaces: list[str]) -> dict`:
  - Default deny all ingress, allow ingress only from pods in `allowed_namespaces`
  - Allow all egress
- `generate_pdb(app_name: str, namespace: str, min_available: str = "50%") -> dict`:
  - PodDisruptionBudget targeting the app's pods

### ManifestValidator

- `validate(manifest: dict) -> list[str]` — Return list of violations:
  - `"Missing label: {label}"` if required labels (`app`, `version`) are absent
  - `"Missing resource limits for container '{name}'"` if `limits` not set
  - `"Missing liveness probe for container '{name}'"` if no health check
  - `"Image uses 'latest' tag: {image}"` if image ends with `:latest` or has no tag
  - `"Privileged container: '{name}'"` if `securityContext.privileged: true`
  - `"No readiness probe for container '{name}'"` if readiness probe missing
- `validate_all(manifests: list[dict]) -> dict` — Return `{valid_count, invalid_count, violations_by_resource: dict}`

### Edge Cases

- Empty `env_vars`: no env section in container spec (not an empty list)
- Image without tag (e.g., `nginx`): treated as implicit `latest` and flagged by validator
- `min_replicas > max_replicas` in HPA: raise `ValueError`
- Overlay patch for non-existent base field: raise `KeyError` with descriptive message
- Namespace with special characters: validate against DNS label format (`^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`)

## Expected Functionality

- `ManifestGenerator("webapp", "production", "myapp:v1.2.3", 8080).generate_deployment()` produces a valid Deployment with health checks, resource limits, and anti-affinity
- `KustomizeBuilder.create_overlay("production", {"replicas": 5, "resources": {"limits": {"cpu": "2", "memory": "2Gi"}}})` patches the base to production scale
- `SecurityPolicyGenerator.add_security_context(deployment)` adds non-root, read-only filesystem, and dropped capabilities
- `ManifestValidator.validate(deployment)` returns empty list for a well-configured deployment, or specific violations for misconfigured ones

## Acceptance Criteria

- Generated Deployments include resource limits, health probes, rolling update strategy, and anti-affinity
- Services, ConfigMaps, Ingress, and HPA are generated with correct API versions and label selectors
- Kustomize overlays correctly patch base manifests for replicas, images, and resources
- Security contexts enforce non-root, read-only filesystem, and dropped capabilities
- NetworkPolicy and PDB are generated with correct selectors
- Validator catches all specified best-practice violations
- All tests pass with `pytest`
