"""
Test for 'slo-implementation' skill — SLO implementation with slo-generator
Validates that the Agent implemented SLO (Service Level Objectives) using
the slo-generator project.
"""

import os
import re

import pytest


class TestSloImplementation:
    """Verify SLO implementation with slo-generator."""

    REPO_DIR = "/workspace/slo-generator"

    def test_slo_config_exists(self):
        """SLO configuration file must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yaml", ".yml", ".json")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"slo|SLO|service_level|target|objective", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No SLO configuration found"

    def test_sli_definition(self):
        """SLI (Service Level Indicator) must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"SLI|sli|indicator|good_events|total_events|good_count|valid_count", content):
                        found = True
                        break
            if found:
                break
        assert found, "No SLI definition found"

    def test_error_budget_calculation(self):
        """Error budget must be calculated."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"error.budget|error_budget|budget|remaining|burn.rate", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No error budget calculation found"

    def test_target_percentage(self):
        """SLO target percentage must be defined (e.g. 99.9%)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".yaml", ".yml", ".json")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"target|goal|objective", content, re.IGNORECASE):
                        if re.search(r"99\.|0\.999|95\.|0\.95|99\.9", content):
                            found = True
                            break
            if found:
                break
        assert found, "No SLO target percentage found"

    def test_backend_integration(self):
        """Backend data source (Prometheus, Stackdriver, etc) must be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Pp]rometheus|[Ss]tackdriver|[Dd]atadog|[Ee]lasticsearch|[Cc]loud[Mm]onitoring|backend", content):
                        found = True
                        break
            if found:
                break
        assert found, "No backend integration found"

    def test_exporter_defined(self):
        """SLO exporter must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ee]xporter|export|[Rr]eporter|report|output|publish", content):
                        found = True
                        break
            if found:
                break
        assert found, "No SLO exporter found"

    def test_window_definition(self):
        """SLO window (rolling or calendar) must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"window|period|rolling|calendar|duration|28d|30d|7d", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No SLO window defined"

    def test_burn_rate_alerting(self):
        """Burn rate alerting should be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".yaml", ".yml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"burn.rate|alert|threshold|notification", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No burn rate alerting found"

    def test_python_compute_module(self):
        """Python compute module for SLO must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"compute|calculate|slo|SLO", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Python compute module found"

    def test_test_file_exists(self):
        """Test files for SLO implementation must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.startswith("test_") and f.endswith(".py"):
                    found = True
                    break
            if found:
                break
        assert found, "No test files found"
