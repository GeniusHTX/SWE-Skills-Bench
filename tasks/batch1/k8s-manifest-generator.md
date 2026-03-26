# Task: Create Multi-Environment Kustomize Overlay Example

## Background
   Add a comprehensive
   multi-environment overlay example to the Kustomize repository demonstrating
   production-ready configuration management patterns.

## Files to Create/Modify
   - examples/multi-env/base/deployment.yaml (base deployment)
   - examples/multi-env/base/service.yaml (base service)
   - examples/multi-env/base/kustomization.yaml (base kustomization)
   - examples/multi-env/overlays/dev/kustomization.yaml (dev overlay)
   - examples/multi-env/overlays/staging/kustomization.yaml (staging overlay)
   - examples/multi-env/overlays/production/kustomization.yaml (prod overlay)

## Requirements
   
   Base Configuration:
   - Deployment with configurable replicas
   - Service exposing the deployment
   - ConfigMap for application settings
   - Resource limits and requests
   
   Overlay Features:
   - Dev: single replica, debug logging, no resource limits
   - Staging: 2 replicas, info logging, moderate resources
   - Production: 3 replicas, warning logging, high resources, HPA
   
   Kustomize Patterns to Demonstrate:
   - patches (strategic merge and JSON)
   - configMapGenerator
   - commonLabels and commonAnnotations
   - namespace transformation
   - images transformer

4. Validation Commands:
   - `kustomize build examples/multi-env/overlays/dev`
   - `kustomize build examples/multi-env/overlays/production`

## Acceptance Criteria
   - `kustomize build examples/multi-env/overlays/production` exits with code 0
   - Generated manifests include all required resources
   - Each environment has appropriate configuration differences
