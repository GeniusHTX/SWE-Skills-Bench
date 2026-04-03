"""
Test for 'linkerd-patterns' skill — Linkerd2 service mesh patterns
Validates that the Agent created Linkerd service profiles, traffic policies,
and mesh configuration for the linkerd2 project.
"""

import os
import re

import pytest


class TestLinkerdPatterns:
    """Verify Linkerd2 service mesh patterns."""

    REPO_DIR = "/workspace/linkerd2"

    def test_service_profile_exists(self):
        """ServiceProfile YAML must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"kind:\s*ServiceProfile", content):
                        found = True
                        break
            if found:
                break
        assert found, "ServiceProfile not found"

    def test_service_profile_has_routes(self):
        """ServiceProfile must define routes."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "ServiceProfile" in content and re.search(r"routes:", content):
                        found = True
                        break
            if found:
                break
        assert found, "ServiceProfile does not define routes"

    def test_retry_budget_configured(self):
        """Retry budget should be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"retryBudget:|retry_budget:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No retry budget configured"

    def test_timeout_configured(self):
        """Timeout must be configured on routes."""
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

    def test_traffic_split_exists(self):
        """TrafficSplit resource should exist for canary deployments."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"kind:\s*TrafficSplit|TrafficSplit", content):
                        found = True
                        break
            if found:
                break
        assert found, "TrafficSplit not found"

    def test_linkerd_api_version(self):
        """Resources must use Linkerd API version."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"linkerd\.io/|split\.smi-spec\.io/", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Linkerd API version found"

    def test_mutual_tls_or_mtls(self):
        """mTLS should be referenced or configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml", ".go", ".md")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"mtls|mTLS|mutual.*tls|TLS|identity", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No mTLS configuration found"

    def test_annotations_for_injection(self):
        """Linkerd injection annotations must be present."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"linkerd\.io/inject|linkerd\.io/proxy", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Linkerd injection annotations found"

    def test_route_condition_or_match(self):
        """ServiceProfile routes must define match conditions."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "ServiceProfile" in content:
                        if re.search(r"condition:|pathRegex:|method:", content):
                            found = True
                            break
            if found:
                break
        assert found, "No route match conditions found"

    def test_weight_in_traffic_split(self):
        """TrafficSplit must include weight for backends."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "TrafficSplit" in content and re.search(r"weight:", content):
                        found = True
                        break
            if found:
                break
        assert found, "TrafficSplit does not include weights"
