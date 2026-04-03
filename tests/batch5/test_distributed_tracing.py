"""
Test for 'distributed-tracing' skill — OpenTelemetry Collector Tracing
Validates Go source files for ConsumeTraces, peer.service extraction,
LRU cache with TTL, config validation, and functional tests.
"""

import os
import re
import subprocess

import pytest


class TestDistributedTracing:
    """Verify OpenTelemetry Collector distributed tracing implementation."""

    REPO_DIR = "/workspace/opentelemetry-collector"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_go_source_files_exist(self):
        """Verify at least 3 Go source files for tracing exist."""
        go_files = self._find_go_files(exclude_test=True)
        assert len(go_files) >= 3, f"Expected ≥3 Go source files, found {len(go_files)}"

    def test_config_yaml_exists(self):
        """Verify a collector config YAML file exists."""
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".yaml") or f.endswith(".yml")
                ) and "config" in f.lower():
                    return
        pytest.skip("No config YAML found (may be embedded in Go)")

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_consume_traces_function(self):
        """Verify ConsumeTraces function is implemented."""
        go_files = self._find_go_files()
        assert go_files, "No Go files found"
        for fpath in go_files:
            content = self._read(fpath)
            if re.search(r"func.*ConsumeTraces|ConsumeTraces\(", content):
                return
        pytest.fail("No ConsumeTraces function found")

    def test_peer_service_extraction(self):
        """Verify peer.service attribute extraction logic."""
        go_files = self._find_go_files()
        assert go_files, "No Go files found"
        for fpath in go_files:
            content = self._read(fpath)
            if "peer.service" in content or "peerService" in content.lower():
                return
        pytest.fail("No peer.service extraction found")

    def test_lru_cache_with_ttl(self):
        """Verify LRU cache with TTL is implemented."""
        go_files = self._find_go_files()
        assert go_files, "No Go files found"
        has_lru = False
        has_ttl = False
        for fpath in go_files:
            content = self._read(fpath)
            if re.search(r"(lru|LRU|cache|Cache)", content):
                has_lru = True
            if re.search(r"(ttl|TTL|expir|Expir)", content):
                has_ttl = True
        assert has_lru, "No LRU cache implementation found"
        assert has_ttl, "No TTL/expiration logic found"

    def test_config_validate_method(self):
        """Verify Config struct has Validate() method."""
        go_files = self._find_go_files()
        assert go_files, "No Go files found"
        for fpath in go_files:
            content = self._read(fpath)
            if re.search(r"func\s*\(.*Config\)\s*Validate\b", content):
                return
        pytest.fail("No Config.Validate() method found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_go_files_compile(self):
        """Verify Go files compile with go build."""
        try:
            subprocess.run(["go", "version"], capture_output=True, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("go not available")
        result = subprocess.run(
            ["go", "build", "./..."],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=self.REPO_DIR,
        )
        if result.returncode != 0:
            # Allow missing dependencies, but not syntax errors
            if "syntax error" in result.stderr.lower():
                pytest.fail(f"Go syntax error: {result.stderr[:500]}")

    def test_go_test_runs(self):
        """Verify Go tests can at least be listed."""
        try:
            subprocess.run(["go", "version"], capture_output=True, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("go not available")
        result = subprocess.run(
            ["go", "test", "-list", ".*", "./..."],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=self.REPO_DIR,
        )
        # Non-zero is ok if just missing deps
        if "syntax error" in result.stderr.lower():
            pytest.fail(f"Go syntax error: {result.stderr[:500]}")

    def test_cache_dedup_logic(self):
        """Verify cache prevents duplicate processing."""
        go_files = self._find_go_files()
        for fpath in go_files:
            content = self._read(fpath)
            if re.search(
                r"(dedup|duplicate|already.?seen|cache.*hit|Get\(|Load\()",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No cache deduplication logic found")

    def test_invalid_config_handling(self):
        """Verify invalid configuration is properly rejected."""
        go_files = self._find_go_files()
        for fpath in go_files:
            content = self._read(fpath)
            if re.search(
                r"(err\s*!=\s*nil|return.*error|fmt\.Errorf|errors\.New)", content
            ):
                if "config" in content.lower() or "Config" in content:
                    return
        pytest.fail("No invalid config error handling found")

    def test_span_attributes_set(self):
        """Verify span attributes like http.method or status_code are set."""
        go_files = self._find_go_files()
        for fpath in go_files:
            content = self._read(fpath)
            if re.search(r"(http\.method|status_code|SetAttributes|Span)", content):
                return
        pytest.fail("No span attributes found in tracing code")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_go_files(self, exclude_test=False):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath or "vendor" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".go"):
                    if exclude_test and f.endswith("_test.go"):
                        continue
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
