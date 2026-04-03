# Task: Build a Kubernetes Manifest Generator Library for Kustomize

## Background

The Kustomize repository (https://github.com/kubernetes-sigs/kustomize) provides template-free customization of Kubernetes manifests. A new Python utility library is needed that generates production-ready Kubernetes manifests (Deployment, Service, ConfigMap, Secret, PVC, Ingress) from a declarative application specification, applies security best practices by default, and produces output compatible with Kustomize base/overlay patterns.

## Files to Create/Modify

- `examples/manifest-gen/generator.py` (create) — `ManifestGenerator` class that produces Kubernetes YAML from an application spec
- `examples/manifest-gen/models.py` (create) — Data classes defining the application specification schema
- `examples/manifest-gen/security.py` (create) — Security context defaults and validation
- `examples/manifest-gen/kustomize_writer.py` (create) — Writes generated manifests into a Kustomize-compatible directory structure
- `tests/test_k8s_manifest_generator.py` (create) — Tests for manifest generation, security defaults, and Kustomize output

## Requirements

### Application Specification (models.py)

- `AppSpec` dataclass with fields: `name` (str), `image` (str, must include tag), `port` (int), `replicas` (int, default 3), `env_vars` (dict, optional), `secrets` (dict, optional), `storage` (StorageSpec, optional), `ingress` (IngressSpec, optional), `resources` (ResourceSpec, optional)
- `ResourceSpec`: `cpu_request` (str, default "100m"), `cpu_limit` (str, default "500m"), `memory_request` (str, default "128Mi"), `memory_limit` (str, default "512Mi")
- `StorageSpec`: `size` (str, e.g., "10Gi"), `access_mode` (str, default "ReadWriteOnce"), `storage_class` (str, optional), `mount_path` (str)
- `IngressSpec`: `host` (str), `path` (str, default "/"), `tls` (bool, default True), `tls_secret_name` (str, optional)
- Image must include a tag (not `:latest`); if `:latest` or no tag is provided, raise `ValueError`

### Manifest Generator (generator.py)

- `ManifestGenerator` class accepting an `AppSpec`
- `generate_deployment() -> dict` — produces a Kubernetes Deployment dict:
  - Labels: `app: <name>`, `app.kubernetes.io/name: <name>`, `app.kubernetes.io/managed-by: manifest-gen`
  - Container with resource requests/limits, liveness probe (HTTP GET `/healthz`, initial delay 30s, period 10s), readiness probe (HTTP GET `/readyz`, initial delay 5s, period 5s)
  - Security context: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `capabilities: {drop: ["ALL"]}`
  - If storage is specified, include a volume mount and PVC volume reference
  - Environment variables from ConfigMap ref and Secret ref when configured
- `generate_service() -> dict` — ClusterIP Service targeting the deployment's pods
- `generate_configmap() -> dict` — ConfigMap from `env_vars` (skip if empty)
- `generate_secret() -> dict` — Secret from `secrets` with base64-encoded values (skip if empty)
- `generate_pvc() -> dict` — PVC from `storage` spec (skip if no storage)
- `generate_ingress() -> dict` — Ingress with TLS configuration if `ingress.tls` is True
- `generate_all() -> list[dict]` — generates all applicable manifests; uses `---` separator

### Security Defaults (security.py)

- `apply_security_context(container: dict) -> dict` — ensures the security context fields are set; does not overwrite existing values
- `validate_image(image: str) -> bool` — returns True if the image includes a non-latest tag; raises `ValueError` otherwise
- `validate_resources(resources: dict) -> bool` — returns True if both requests and limits are set; raises `ValueError` if limits are missing

### Kustomize Writer (kustomize_writer.py)

- `KustomizeWriter` class accepting an output directory path
- `write(manifests: list[dict], app_name: str)` — writes each manifest to a separate YAML file in `<output_dir>/<app_name>/` and generates a `kustomization.yaml` that references all files
- `kustomization.yaml` must include `apiVersion: kustomize.config.k8s.io/v1beta1`, `kind: Kustomization`, and a `resources` list
- Files are named: `deployment.yaml`, `service.yaml`, `configmap.yaml`, `secret.yaml`, `pvc.yaml`, `ingress.yaml`

### Expected Functionality

- An `AppSpec(name="myapp", image="nginx:1.25", port=80)` generates a Deployment with 3 replicas, ClusterIP Service, and security context defaults
- An `AppSpec` with `secrets={"DB_PASSWORD": "s3cret"}` generates both a Secret and a Deployment with `secretRef`
- An `AppSpec` with `storage=StorageSpec(size="10Gi", mount_path="/data")` generates a PVC and a Deployment with a volume mount
- An `AppSpec` with `image="nginx:latest"` raises `ValueError`
- `KustomizeWriter.write()` creates a directory with individual YAML files and a valid `kustomization.yaml`

## Acceptance Criteria

- Generated Deployment manifests include resource limits, health probes, security context, and correct labels
- Security context defaults enforce non-root, read-only filesystem, dropped capabilities, and no privilege escalation
- ConfigMap, Secret, PVC, and Ingress are conditionally generated based on the AppSpec
- Image validation rejects `:latest` and untagged images
- KustomizeWriter produces a valid Kustomize base directory with proper file structure
- All generated YAML is valid and parseable
- Tests verify manifest correctness, security defaults, conditional generation, and Kustomize output structure
