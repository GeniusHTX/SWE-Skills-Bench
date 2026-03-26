"""
Test for 'nx-workspace-patterns' skill — Nx Affected Graph Validation
Validates that the Agent created E2E tests and fixtures for verifying
Nx affected task graph resolution with multi-project workspaces.
"""

import os
import re
import subprocess
import json

import pytest


class TestNxWorkspacePatterns:
    """Verify Nx affected graph E2E test and workspace fixture."""

    REPO_DIR = "/workspace/nx"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _find_test_file(self):
        """Find the affected graph test file."""
        candidates = [
            "e2e/nx/src/affected-graph.test.ts",
            "e2e/nx/src/affected-graph.spec.ts",
            "e2e/nx-misc/src/affected-graph.test.ts",
        ]
        for rel in candidates:
            fpath = os.path.join(self.REPO_DIR, rel)
            if os.path.isfile(fpath):
                return fpath
        # Fallback search
        for root, _dirs, files in os.walk(os.path.join(self.REPO_DIR, "e2e")):
            for f in files:
                if "affected" in f and f.endswith((".test.ts", ".spec.ts")):
                    return os.path.join(root, f)
        pytest.fail("Affected graph test file not found")

    def _find_fixture(self):
        """Find the workspace fixture."""
        candidates = [
            "e2e/nx/src/fixtures/affected-demo/workspace.json",
            "e2e/nx/src/fixtures/affected-demo/nx.json",
            "e2e/nx/src/fixtures/affected-demo/project.json",
        ]
        for rel in candidates:
            fpath = os.path.join(self.REPO_DIR, rel)
            if os.path.isfile(fpath):
                return fpath
        # Check for directory existence at least
        fixture_dir = os.path.join(self.REPO_DIR, "e2e/nx/src/fixtures/affected-demo")
        if os.path.isdir(fixture_dir):
            for f in os.listdir(fixture_dir):
                if f.endswith(".json"):
                    return os.path.join(fixture_dir, f)
        return None

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_test_file_exists(self):
        """E2E affected graph test file must exist."""
        self._find_test_file()

    def test_fixture_exists(self):
        """Workspace fixture must exist."""
        path = self._find_fixture()
        assert path is not None, "Workspace fixture not found"

    # ------------------------------------------------------------------
    # L1: Test structure
    # ------------------------------------------------------------------

    def test_test_file_has_test_cases(self):
        """Test file must define test cases."""
        path = self._find_test_file()
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"it\(", r"test\(", r"describe\("]
        found = sum(1 for p in patterns if re.search(p, content))
        assert found >= 2, "Test file has insufficient test cases"

    def test_test_imports_nx(self):
        """Test file must reference Nx functionality."""
        path = self._find_test_file()
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"nx", r"affected", r"@nx/", r"@nrwl/"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Test file does not reference Nx"

    # ------------------------------------------------------------------
    # L2: Workspace fixture structure
    # ------------------------------------------------------------------

    def test_fixture_has_multiple_projects(self):
        """Fixture must define at least 3 projects."""
        path = self._find_fixture()
        assert path is not None
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
        data = json.loads(content)
        # Check for projects key or multiple project entries
        projects = data.get("projects", {})
        if isinstance(projects, dict):
            count = len(projects)
        else:
            count = len(projects)
        if count < 3:
            # Maybe separate project.json files in subdirectories
            fixture_dir = os.path.dirname(path)
            proj_count = 0
            for root, _dirs, files in os.walk(fixture_dir):
                if "project.json" in files:
                    proj_count += 1
            count = max(count, proj_count)
        assert count >= 3, f"Only {count} project(s) — need at least 3"

    def test_fixture_has_shared_library(self):
        """Fixture must include a shared library project."""
        path = self._find_test_file()
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"shared", r"library", r"lib", r"common"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Test does not reference a shared library project"

    # ------------------------------------------------------------------
    # L2: Affected behavior tests
    # ------------------------------------------------------------------

    def test_verifies_dependency_propagation(self):
        """Test must verify that changes propagate through dependencies."""
        path = self._find_test_file()
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"affected", r"depend", r"propagat", r"downstream", r"impacted"]
        found = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
        assert found >= 2, "Test does not verify dependency propagation"

    def test_verifies_independent_isolation(self):
        """Test must verify independent projects are not affected."""
        path = self._find_test_file()
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"independent",
            r"not.*affected",
            r"unrelated",
            r"isolated",
            r"should not.*build",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Test does not verify independent project isolation"

    def test_verifies_execution_order(self):
        """Test should verify task execution order."""
        path = self._find_test_file()
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"order", r"topolog", r"before", r"graph", r"sequence"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Test does not verify execution order"

    def test_uses_affected_command(self):
        """Test must invoke nx affected or equivalent."""
        path = self._find_test_file()
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"affected",
            r"nx affected",
            r"runNxCommand.*affected",
            r"affected:build",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Test does not invoke affected command"
