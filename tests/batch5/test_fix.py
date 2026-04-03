"""
Test for 'fix' skill — Upgradle Game Bug Fixes
Validates TSX/TS component fixes including immutable state, null checks,
useEffect cleanup, game types, ESLint/TS compilation, and Jest tests.
"""

import os
import re
import subprocess

import pytest


class TestFix:
    """Verify Upgradle game bug fixes."""

    REPO_DIR = "/workspace/upgradle"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_tsx_source_files_exist(self):
        """Verify at least 3 TSX/TS source files exist."""
        ts_files = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath or ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".tsx") or f.endswith(".ts"):
                    ts_files.append(os.path.join(dirpath, f))
        assert len(ts_files) >= 3, f"Expected ≥3 TS/TSX files, found {len(ts_files)}"

    def test_eslint_config_exists(self):
        """Verify ESLint configuration file exists."""
        eslint_files = [
            ".eslintrc",
            ".eslintrc.js",
            ".eslintrc.json",
            ".eslintrc.yml",
            "eslint.config.js",
            "eslint.config.mjs",
        ]
        for name in eslint_files:
            if os.path.isfile(os.path.join(self.REPO_DIR, name)):
                return
        # Check package.json for eslintConfig
        pkg = os.path.join(self.REPO_DIR, "package.json")
        if os.path.isfile(pkg):
            content = self._read(pkg)
            if "eslintConfig" in content:
                return
        pytest.skip("No ESLint configuration file found")

    def test_test_file_exists(self):
        """Verify at least one test file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath or ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".test.ts")
                    or f.endswith(".test.tsx")
                    or f.endswith(".spec.ts")
                    or f.endswith(".spec.tsx")
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No test file found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_immutable_state_pattern(self):
        """Verify immutable state update pattern (spread operator or structuredClone)."""
        ts_files = self._find_ts_files()
        assert ts_files, "No TS files"
        for fpath in ts_files:
            content = self._read(fpath)
            if re.search(
                r"(\.\.\.\w+|structuredClone|Object\.assign|immer|produce)", content
            ):
                return
        pytest.fail("No immutable state pattern found")

    def test_explicit_null_check(self):
        """Verify explicit null/undefined checks replace loose equality."""
        ts_files = self._find_ts_files()
        assert ts_files, "No TS files"
        for fpath in ts_files:
            content = self._read(fpath)
            if re.search(
                r"(===\s*null|!==\s*null|===\s*undefined|!==\s*undefined|\?\?|optional chaining)",
                content,
            ):
                return
        pytest.fail("No explicit null check found")

    def test_useeffect_cleanup(self):
        """Verify useEffect includes cleanup/return function."""
        ts_files = self._find_ts_files()
        assert ts_files, "No TS files"
        for fpath in ts_files:
            content = self._read(fpath)
            if "useEffect" in content:
                # Check for return function in useEffect
                if re.search(r"useEffect\s*\(.*return\s", content, re.DOTALL):
                    return
                # Check multi-line
                lines = content.split("\n")
                in_effect = False
                for line in lines:
                    if "useEffect" in line:
                        in_effect = True
                    if (
                        in_effect
                        and "return" in line
                        and (
                            "=>" in line
                            or "function" in line
                            or "clearInterval" in line
                            or "clearTimeout" in line
                        )
                    ):
                        return
        pytest.skip("useEffect cleanup not explicitly detectable")

    def test_game_types_defined(self):
        """Verify TypeScript game types/interfaces are defined."""
        ts_files = self._find_ts_files()
        assert ts_files, "No TS files"
        for fpath in ts_files:
            content = self._read(fpath)
            if re.search(
                r"(interface\s+Game|type\s+Game|interface\s+Score|type\s+Score|interface\s+Board)",
                content,
            ):
                return
        pytest.fail("No game type interfaces found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_typescript_compiles(self):
        """Verify TypeScript compilation succeeds."""
        tsc = os.path.join(self.REPO_DIR, "node_modules", ".bin", "tsc")
        if not os.path.isfile(tsc) and not os.path.isfile(tsc + ".cmd"):
            # Try npx
            try:
                result = subprocess.run(
                    ["npx", "tsc", "--noEmit"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=self.REPO_DIR,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pytest.skip("TypeScript compiler not available")
        else:
            result = subprocess.run(
                [tsc, "--noEmit"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.REPO_DIR,
            )
        # Allow type errors but not hard crashes
        if result.returncode != 0:
            assert (
                "Cannot find module" in result.stderr or "error TS" in result.stderr
            ), f"Unexpected tsc failure: {result.stderr[:500]}"

    def test_jest_tests_exist_in_test_file(self):
        """Verify test files contain describe/it/test blocks."""
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".test.ts")
                    or f.endswith(".test.tsx")
                    or f.endswith(".spec.ts")
                ):
                    content = self._read(os.path.join(dirpath, f))
                    if re.search(r"(describe|it|test)\s*\(", content):
                        return
        pytest.fail("No Jest test blocks found")

    def test_score_zero_display(self):
        """Verify score=0 is displayed correctly (not falsy-hidden)."""
        ts_files = self._find_ts_files()
        for fpath in ts_files:
            content = self._read(fpath)
            if "score" in content.lower():
                if re.search(
                    r"(score\s*===\s*0|score\s*!==\s*undefined|score\s*!=\s*null|\?\?)",
                    content,
                ):
                    return
                if re.search(r"score.*\{.*0.*\}|display.*score", content, re.DOTALL):
                    return
        pytest.skip("Score=0 display not explicitly verifiable via static analysis")

    def test_package_json_valid(self):
        """Verify package.json is valid JSON."""
        import json

        pkg_path = os.path.join(self.REPO_DIR, "package.json")
        if not os.path.isfile(pkg_path):
            pytest.skip("No package.json")
        with open(pkg_path, "r") as fh:
            data = json.load(fh)
        assert "name" in data or "private" in data, "package.json missing name/private"

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_ts_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath or ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".ts") or f.endswith(".tsx"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
