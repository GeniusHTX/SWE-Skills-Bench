"""
Test for 'istio-traffic-management' skill — Istio traffic management resources
Validates that the Agent created Istio VirtualService, DestinationRule, and
Gateway resources for traffic management.
"""

import os
import re

import pytest


class TestIstioTrafficManagement:
    """Verify Istio traffic management configuration."""

    REPO_DIR = "/workspace/istio"

    def test_virtual_service_exists(self):
        """VirtualService YAML resource must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"kind:\s*VirtualService", content):
                        found = True
                        break
            if found:
                break
        assert found, "VirtualService not found"

    def test_destination_rule_exists(self):
        """DestinationRule YAML resource must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"kind:\s*DestinationRule", content):
                        found = True
                        break
            if found:
                break
        assert found, "DestinationRule not found"

    def test_gateway_exists(self):
        """Gateway YAML resource must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"kind:\s*Gateway", content):
                        found = True
                        break
            if found:
                break
        assert found, "Gateway not found"

    def test_virtual_service_has_route(self):
        """VirtualService must define HTTP routes."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "VirtualService" in content and re.search(r"http:|route:", content):
                        found = True
                        break
            if found:
                break
        assert found, "VirtualService does not have HTTP routes"

    def test_traffic_splitting_weights(self):
        """Traffic splitting with weights must be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"weight:\s*\d+", content):
                        if "VirtualService" in content or "route" in content:
                            found = True
                            break
            if found:
                break
        assert found, "No traffic splitting weights found"

    def test_destination_rule_has_subsets(self):
        """DestinationRule must define subsets."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "DestinationRule" in content and re.search(r"subsets:", content):
                        found = True
                        break
            if found:
                break
        assert found, "DestinationRule does not define subsets"

    def test_circuit_breaker_or_outlier_detection(self):
        """DestinationRule should configure circuit breaking or outlier detection."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"outlierDetection:|connectionPool:|circuitBreaker", content):
                        found = True
                        break
            if found:
                break
        assert found, "No circuit breaker or outlier detection configured"

    def test_retry_policy(self):
        """VirtualService should configure retry policy."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"retries:|retry:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No retry policy configured"

    def test_timeout_configured(self):
        """VirtualService should configure request timeouts."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"timeout:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No timeout configured"

    def test_istio_api_version(self):
        """Resources must use Istio networking API version."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"networking\.istio\.io/", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Istio networking API version found"

    def test_host_field_in_routes(self):
        """Routes must specify host fields."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"hosts?:", content) and re.search(r"VirtualService|Gateway", content):
                        found = True
                        break
            if found:
                break
        assert found, "No host field found in routes"
