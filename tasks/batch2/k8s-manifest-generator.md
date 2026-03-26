# Task: Create Multi-Environment Kustomize Overlays for Kubernetes

## Background

Kustomize (https://github.com/kubernetes-sigs/kustomize) is a Kubernetes configuration management tool. A complete example is needed showing how to use base manifests with environment-specific overlays to generate deployment configurations for staging and production environments.

## Files to Create

- `examples/multi-env/base/deployment.yaml` — Base Deployment manifest
- `examples/multi-env/base/service.yaml` — Base Service manifest
- `examples/multi-env/base/configmap.yaml` — Base ConfigMap
- `examples/multi-env/base/kustomization.yaml` — Base kustomization file listing all resources
- `examples/multi-env/overlays/staging/kustomization.yaml` — Staging overlay with patches for replicas, resource limits, and namespace
- `examples/multi-env/overlays/production/kustomization.yaml` — Production overlay with patches for replicas, resource limits, and namespace

## Requirements

### Base Manifests

- Define a base set of Kubernetes resources: a Deployment with a container spec, a Service, and a ConfigMap
- The base `kustomization.yaml` must list all base resources

### Overlays

- Each environment overlay must customize:
  - Replica count (lower for staging, higher for production)
  - Resource limits (CPU and memory)
  - Environment-specific configuration values in the ConfigMap
  - Namespace assignment
- Use Kustomize patches (strategic merge or JSON patches) for modifications
- Each overlay must have its own `kustomization.yaml` referencing the base

### Labels and Annotations

- Apply common labels (app name, version) via Kustomize's `commonLabels` feature
- Apply environment-specific labels or annotations per overlay

## Expected Functionality

- Running `kustomize build` on each overlay produces valid, environment-specific Kubernetes manifests
- Staging and production outputs differ in replica counts, resource limits, namespaces, and config values
- All generated manifests are valid Kubernetes YAML

## Acceptance Criteria

- The base configuration defines a reusable deployment, service, and config map shared by multiple environments.
- The staging and production overlays each produce environment-specific manifests with different replica counts, configuration values, and namespaces.
- Common labels are applied consistently while overlay-specific labels or annotations remain distinct.
- Patches are used to express environment differences rather than duplicating the entire manifest set.
- A user can build each overlay and understand exactly which settings differ between environments.
