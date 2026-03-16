# Task: Add Istio Canary Deployment Example

## Background

Add an Istio canary deployment example to the `samples/` directory demonstrating weighted traffic routing between stable and canary versions of a service.

## Files to Create/Modify

- `samples/canary-demo/virtual-service.yaml` - VirtualService with weighted routing
- `samples/canary-demo/destination-rule.yaml` - DestinationRule for subsets
- `samples/canary-demo/gateway.yaml` - Ingress gateway configuration
- `samples/canary-demo/deployments.yaml` - Stable and canary Deployment manifests
- `samples/canary-demo/verify.sh` - Verification script

## Requirements

### VirtualService Configuration
- `apiVersion: networking.istio.io/v1beta1`
- HTTP route rules with weighted traffic split (e.g., 90% stable / 10% canary)
- Match conditions on headers or URI prefix
- Retry policy and timeout settings

### DestinationRule
- Define subsets: `stable` and `canary` with label selectors
- Load balancing policy
- Connection pool settings and outlier detection

### Deployments
- Stable deployment with label `version: stable`
- Canary deployment with label `version: canary`
- Kubernetes Service selecting both versions

### Verification Script (verify.sh)
- Validate all YAML files with `istioctl analyze`
- Check that VirtualService references valid destinations
- Verify weight percentages sum to 100

## Acceptance Criteria

- `istioctl analyze samples/canary-demo/` exits with code 0
- VirtualService contains `spec.http[].route` entries with weight
- DestinationRule defines `stable` and `canary` subsets
- Verification script passes all checks
