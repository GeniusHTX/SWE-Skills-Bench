"""
Test for 'analyze-ci' skill — Analyze CI
Validates analyze_ci function and CIAnalysisReport with anti-pattern detection,
security issue scanning, optimization suggestions, and metrics extraction.
"""

import os
import re
import sys
import glob
import json
import tempfile
import pytest

import yaml


class TestAnalyzeCi:
    """Tests for CI analysis tool in the sentry repo."""

    REPO_DIR = "/workspace/sentry"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    def _find_analyze_ci(self):
        """Find analyze_ci.py in common locations."""
        candidates = [
            "src/sentry/utils/analyze_ci.py",
            "tools/analyze_ci.py",
            "scripts/analyze_ci.py",
            "analyze_ci.py",
        ]
        for c in candidates:
            path = os.path.join(self.REPO_DIR, c)
            if os.path.exists(path):
                return c
        return None

    def _get_module_dir(self):
        """Get directory containing analyze_ci.py for sys.path insertion."""
        found = self._find_analyze_ci()
        assert found is not None, "analyze_ci.py not found in any expected location"
        return os.path.join(self.REPO_DIR, os.path.dirname(found))

    def _write_temp_yaml(self, config):
        """Write a YAML config to a temp file and return the path."""
        fd, path = tempfile.mkstemp(suffix=".yml")
        with os.fdopen(fd, "w") as f:
            yaml.dump(config, f)
        return path

    # --- File Path Checks ---

    def test_src_sentry_utils_analyze_ci_py_exists(self):
        """Verifies that src/sentry/utils/analyze_ci.py exists."""
        path = os.path.join(self.REPO_DIR, "src", "sentry", "utils", "analyze_ci.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_tools_analyze_ci_py_exists(self):
        """Verifies that tools/analyze_ci.py exists."""
        path = os.path.join(self.REPO_DIR, "tools", "analyze_ci.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_scripts_analyze_ci_py_exists(self):
        """Verifies that scripts/analyze_ci.py exists."""
        path = os.path.join(self.REPO_DIR, "scripts", "analyze_ci.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_analyze_ci_py_exists(self):
        """Verifies that analyze_ci.py exists at repo root."""
        path = os.path.join(self.REPO_DIR, "analyze_ci.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_import_analyze_ci_and_report(self):
        """from analyze_ci import analyze_ci, CIAnalysisReport — importable."""
        module_dir = self._get_module_dir()
        old_path = sys.path[:]
        sys.path.insert(0, module_dir)
        try:
            from analyze_ci import analyze_ci, CIAnalysisReport

            assert analyze_ci is not None
            assert CIAnalysisReport is not None
        finally:
            sys.path[:] = old_path

    def test_sem_analyze_ci_accepts_config_path(self):
        """analyze_ci function accepts config_path string parameter."""
        found = self._find_analyze_ci()
        assert found is not None
        content = self._read(found)
        assert re.search(
            r"def\s+analyze_ci\s*\(", content
        ), "analyze_ci function not defined"
        assert (
            "config_path" in content or "path" in content
        ), "config_path parameter not found"

    def test_sem_report_has_required_attributes(self):
        """CIAnalysisReport has attributes: anti_patterns, security_issues, optimization_suggestions, metrics."""
        found = self._find_analyze_ci()
        assert found is not None
        content = self._read(found)
        for attr in [
            "anti_patterns",
            "security_issues",
            "optimization_suggestions",
            "metrics",
        ]:
            assert attr in content, f"Attribute '{attr}' not found in analyze_ci.py"

    def test_sem_report_has_to_json_and_to_markdown(self):
        """CIAnalysisReport has to_json() and to_markdown() methods."""
        found = self._find_analyze_ci()
        assert found is not None
        content = self._read(found)
        assert re.search(r"def\s+to_json\s*\(", content), "to_json method not found"
        assert re.search(
            r"def\s+to_markdown\s*\(", content
        ), "to_markdown method not found"

    # --- Functional Checks (import) ---

    def test_func_analyze_basic_config_returns_report(self):
        """analyze_ci with basic GH config returns CIAnalysisReport instance."""
        module_dir = self._get_module_dir()
        old_path = sys.path[:]
        sys.path.insert(0, module_dir)
        try:
            from analyze_ci import analyze_ci, CIAnalysisReport

            gh_config = {
                "on": {"push": {"branches": ["main"]}},
                "jobs": {
                    "test": {
                        "runs-on": "ubuntu-latest",
                        "steps": [{"run": "pip install -r requirements.txt"}],
                    }
                },
            }
            fp = self._write_temp_yaml(gh_config)
            try:
                report = analyze_ci(fp)
                assert isinstance(report, CIAnalysisReport)
            finally:
                os.unlink(fp)
        finally:
            sys.path[:] = old_path

    def test_func_report_metrics_num_jobs(self):
        """report.metrics.get('num_jobs', 0) >= 1 for config with one job."""
        module_dir = self._get_module_dir()
        old_path = sys.path[:]
        sys.path.insert(0, module_dir)
        try:
            from analyze_ci import analyze_ci, CIAnalysisReport

            gh_config = {
                "on": {"push": {"branches": ["main"]}},
                "jobs": {
                    "test": {
                        "runs-on": "ubuntu-latest",
                        "steps": [{"run": "pip install -r requirements.txt"}],
                    }
                },
            }
            fp = self._write_temp_yaml(gh_config)
            try:
                report = analyze_ci(fp)
                assert report.metrics.get("num_jobs", 0) >= 1
            finally:
                os.unlink(fp)
        finally:
            sys.path[:] = old_path

    def test_func_malicious_config_detects_security_issues(self):
        """Config with inline password produces security_issues >= 1."""
        module_dir = self._get_module_dir()
        old_path = sys.path[:]
        sys.path.insert(0, module_dir)
        try:
            from analyze_ci import analyze_ci, CIAnalysisReport

            malicious_config = {
                "jobs": {"build": {"steps": [{"run": "docker login -p mypassword123"}]}}
            }
            fp = self._write_temp_yaml(malicious_config)
            try:
                report2 = analyze_ci(fp)
                assert (
                    len(report2.security_issues) >= 1
                ), "Expected at least 1 security issue"
            finally:
                os.unlink(fp)
        finally:
            sys.path[:] = old_path

    def test_func_security_issue_mentions_password(self):
        """Security issues mention password/credential/secret for inline password config."""
        module_dir = self._get_module_dir()
        old_path = sys.path[:]
        sys.path.insert(0, module_dir)
        try:
            from analyze_ci import analyze_ci, CIAnalysisReport

            malicious_config = {
                "jobs": {"build": {"steps": [{"run": "docker login -p mypassword123"}]}}
            }
            fp = self._write_temp_yaml(malicious_config)
            try:
                report2 = analyze_ci(fp)
                assert any(
                    "password" in str(i).lower()
                    or "credential" in str(i).lower()
                    or "secret" in str(i).lower()
                    for i in report2.security_issues
                ), "No security issue mentions password/credential/secret"
            finally:
                os.unlink(fp)
        finally:
            sys.path[:] = old_path

    def test_func_no_cache_config_detects_anti_patterns(self):
        """Config with heavy pip install without cache produces anti_patterns >= 1."""
        module_dir = self._get_module_dir()
        old_path = sys.path[:]
        sys.path.insert(0, module_dir)
        try:
            from analyze_ci import analyze_ci, CIAnalysisReport

            no_cache_config = {
                "jobs": {"test": {"steps": [{"run": "pip install pandas numpy torch"}]}}
            }
            fp = self._write_temp_yaml(no_cache_config)
            try:
                report3 = analyze_ci(fp)
                assert (
                    len(report3.anti_patterns) >= 1
                ), "Expected at least 1 anti-pattern"
            finally:
                os.unlink(fp)
        finally:
            sys.path[:] = old_path

    def test_func_anti_pattern_mentions_cache(self):
        """Anti-patterns mention 'cache' for pip install without caching config."""
        module_dir = self._get_module_dir()
        old_path = sys.path[:]
        sys.path.insert(0, module_dir)
        try:
            from analyze_ci import analyze_ci, CIAnalysisReport

            no_cache_config = {
                "jobs": {"test": {"steps": [{"run": "pip install pandas numpy torch"}]}}
            }
            fp = self._write_temp_yaml(no_cache_config)
            try:
                report3 = analyze_ci(fp)
                assert any(
                    "cache" in str(p).lower() for p in report3.anti_patterns
                ), "No anti-pattern mentions cache"
            finally:
                os.unlink(fp)
        finally:
            sys.path[:] = old_path

    def test_func_nonexistent_file_raises_error(self):
        """analyze_ci('definitely_nonexistent_file.yml') raises FileNotFoundError."""
        module_dir = self._get_module_dir()
        old_path = sys.path[:]
        sys.path.insert(0, module_dir)
        try:
            from analyze_ci import analyze_ci

            with pytest.raises(FileNotFoundError):
                analyze_ci("definitely_nonexistent_file.yml")
        finally:
            sys.path[:] = old_path

    def test_func_report_to_json(self):
        """report.to_json() returns valid JSON with 'metrics' key."""
        module_dir = self._get_module_dir()
        old_path = sys.path[:]
        sys.path.insert(0, module_dir)
        try:
            from analyze_ci import analyze_ci, CIAnalysisReport

            gh_config = {
                "on": {"push": {"branches": ["main"]}},
                "jobs": {
                    "test": {
                        "runs-on": "ubuntu-latest",
                        "steps": [{"run": "pip install -r requirements.txt"}],
                    }
                },
            }
            fp = self._write_temp_yaml(gh_config)
            try:
                report = analyze_ci(fp)
                json_out = report.to_json()
                parsed = json.loads(json_out)
                assert (
                    "metrics" in parsed
                ), f"'metrics' not in JSON output: {list(parsed.keys())}"
            finally:
                os.unlink(fp)
        finally:
            sys.path[:] = old_path
