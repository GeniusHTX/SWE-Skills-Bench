# Task: Create a GitOps Configuration Example for Flux

## Background

Flux (https://github.com/fluxcd/flux2) is a GitOps toolkit for Kubernetes that enables declarative, automated deployments from Git repositories. A complete GitOps configuration example is needed that demonstrates how to define sources, kustomizations, and reconciliation policies for a multi-environment Kubernetes deployment.

## Files to Create

- `examples/gitops-demo/source.yaml` — Flux GitRepository source definition
- `examples/gitops-demo/staging-kustomization.yaml` — Flux Kustomization for staging environment
- `examples/gitops-demo/production-kustomization.yaml` — Flux Kustomization for production environment
- `examples/gitops-demo/base/deployment.yaml` — Base Kubernetes Deployment manifest
- `examples/gitops-demo/base/service.yaml` — Base Kubernetes Service manifest
- `examples/gitops-demo/base/configmap.yaml` — Base ConfigMap
- `examples/gitops-demo/base/kustomization.yaml` — Base kustomization file
- `examples/gitops-demo/overlays/staging/kustomization.yaml` — Staging overlay patches
- `examples/gitops-demo/overlays/production/kustomization.yaml` — Production overlay patches

## Requirements

### Source Configuration

- Define a GitRepository source pointing to an application repository with branch and interval settings
- Include authentication configuration placeholders for private repositories

### Kustomization Definitions

- Create Kustomization resources for at least two environments (e.g., staging and production)
- Configure appropriate path references, pruning policies, and health checks
- Set different reconciliation intervals per environment

### Deployment Manifests

- Include sample Kubernetes manifests (Deployment, Service, ConfigMap) that the Kustomizations reference
- Demonstrate environment-specific overlays or patches

### Validation

- All YAML files must be syntactically valid
- Go source files must compile as part of the project

## Expected Functionality

- The configuration describes a complete GitOps workflow: Flux watches the Git source, reconciles resources per environment, and prunes deleted resources
- Environment-specific differences (replica counts, resource limits, image tags) are handled through overlays
- Health checks prevent unhealthy deployments from progressing

## Acceptance Criteria

- The example contains a complete GitOps flow with a source definition, environment-specific kustomizations, and Kubernetes manifests.
- Staging and production environments reconcile different overlays while sharing a common base definition.
- Environment-specific differences such as image tags, replica counts, or resource limits are expressed declaratively in overlays.
- The configuration demonstrates pruning, reconciliation intervals, and health checks rather than only static manifests.
- A reader can follow the example to understand how Flux applies changes from Git into multiple environments.
