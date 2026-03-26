# Task: Create a Canary Deployment Example for Istio Traffic Management

## Background

Istio (https://github.com/istio/istio) is a service mesh platform with advanced traffic management capabilities. A new example under `samples/canary-demo/` is needed to demonstrate weighted traffic routing for canary deployments, where a percentage of traffic is gradually shifted from a stable version to a new version.

## Files to Create

- Files under `samples/canary-demo/` including:
  - Kubernetes Deployment manifests for stable and canary versions of a service
  - Istio VirtualService and DestinationRule resources for traffic splitting
  - A Service resource fronting both versions
  - Documentation or README explaining the canary workflow

## Requirements

### Traffic Routing

- Define a VirtualService with weighted routing rules splitting traffic between stable (e.g., 90%) and canary (e.g., 10%) subsets
- Define a DestinationRule with subset definitions corresponding to deployment labels

### Deployment Manifests

- Create two Deployment resources with distinct version labels (e.g., `v1` and `v2`)
- Both deployments should be fronted by a single Kubernetes Service
- Include appropriate labels and annotations for Istio sidecar injection

### Configuration Validation

- All YAML resources must be syntactically valid
- Resources must follow Istio's API schema conventions

## Expected Functionality

- Applying the manifests creates a service with traffic split between two versions
- Adjusting the weight percentages in the VirtualService shifts traffic proportionally
- Both versions are reachable through the same service hostname

## Acceptance Criteria

- The example defines a stable and a canary workload that are reachable through a single Kubernetes service.
- Traffic routing is controlled by an Istio `VirtualService` with weighted distribution between the two subsets.
- The `DestinationRule` subsets match the deployment labels used by the stable and canary workloads.
- Adjusting route weights changes the expected traffic split without requiring changes to the service hostname.
- The example is clear enough for a reader to understand how to perform a canary rollout with Istio.
