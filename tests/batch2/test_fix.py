"""
Test for 'fix' skill — React Code Fix & Linter
Validates that the Agent successfully fixed all ESLint and formatting violations
in the Upgradle React TypeScript project without introducing functional changes.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_npm_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_npm_dependencies(TestFix.REPO_DIR)


class TestFix:
    """Verify that lint and formatting violations are resolved in the Upgradle project."""

    REPO_DIR = "/workspace/upgradle"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _collect_src_files(self, extensions=(".ts", ".tsx")):
        """Collect all TypeScript source files under src/."""
        src_dir = os.path.join(self.REPO_DIR, "src")
        result = []
        if not os.path.isdir(src_dir):
            return result
        for root, _, files in os.walk(src_dir):
            for fname in files:
                if fname.endswith(extensions):
                    result.append(os.path.join(root, fname))
        return result

    # ------------------------------------------------------------------
    # L1: Project structure sanity
    # ------------------------------------------------------------------

    def test_package_json_exists(self):
        """package.json must exist at the repository root."""
        content = self._read("package.json")
        assert '"name"' in content, "package.json is missing the 'name' field"

    def test_src_directory_contains_tsx_files(self):
        """The src/ directory must contain at least one .tsx file."""
        files = self._collect_src_files((".tsx",))
        assert len(files) >= 1, "No .tsx files found under src/"

    def test_lint_script_defined_in_package_json(self):
        """package.json must define a 'lint' script in the scripts section."""
        import json

        content = self._read("package.json")
        pkg = json.loads(content)
        scripts = pkg.get("scripts", {})
        assert "lint" in scripts, (
            "package.json does not define a 'lint' script — "
            f"available scripts: {list(scripts.keys())}"
        )

    # ------------------------------------------------------------------
    # L2: Lint execution — the primary acceptance gate
    # ------------------------------------------------------------------

    def test_npm_run_lint_exits_cleanly(self):
        """Running 'npm run lint' must exit with code 0 (zero violations)."""
        result = subprocess.run(
            ["npm", "run", "lint"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"npm run lint failed (rc={result.returncode}):\n"
            f"stdout:\n{result.stdout[-3000:]}\n"
            f"stderr:\n{result.stderr[-3000:]}"
        )

    def test_npm_run_lint_no_error_lines(self):
        """Lint output must not contain ESLint error-level markers."""
        result = subprocess.run(
            ["npm", "run", "lint", "--", "--format", "compact"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        # Even if the exit code is 0, double-check there are no error lines
        error_lines = [
            line
            for line in result.stdout.splitlines()
            if re.search(r"\bError\b", line) and ".tsx" in line or ".ts" in line
        ]
        assert (
            len(error_lines) == 0
        ), f"ESLint still reports {len(error_lines)} error(s):\n" + "\n".join(
            error_lines[:20]
        )

    # ------------------------------------------------------------------
    # L2: No blanket disable comments
    # ------------------------------------------------------------------

    def test_no_eslint_disable_next_line_abuse(self):
        """Source files must not contain excessive eslint-disable-next-line comments."""
        files = self._collect_src_files()
        total_disables = 0
        for fpath in files:
            with open(fpath, "r", errors="ignore") as fh:
                content = fh.read()
            total_disables += len(re.findall(r"eslint-disable-next-line", content))
        # A small number may be legitimate; blanket use is not
        assert total_disables <= 5, (
            f"Found {total_disables} eslint-disable-next-line comments across src/ — "
            "fixes should address the root cause, not suppress warnings"
        )

    def test_no_file_level_eslint_disable(self):
        """No source file should contain a file-level /* eslint-disable */ comment."""
        files = self._collect_src_files()
        offending = []
        for fpath in files:
            with open(fpath, "r", errors="ignore") as fh:
                content = fh.read()
            # File-level disable: "/* eslint-disable */" without a specific rule
            if re.search(r"/\*\s*eslint-disable\s*\*/", content):
                offending.append(os.path.relpath(fpath, self.REPO_DIR))
        assert not offending, (
            f"File-level eslint-disable found in: {offending} — "
            "this bypasses all lint rules and is not an acceptable fix"
        )

    def test_no_ts_nocheck_or_ts_ignore_abuse(self):
        """Source files must not contain excessive @ts-nocheck or @ts-ignore directives."""
        files = self._collect_src_files()
        total = 0
        for fpath in files:
            with open(fpath, "r", errors="ignore") as fh:
                content = fh.read()
            total += len(re.findall(r"@ts-(?:nocheck|ignore)", content))
        assert total <= 2, (
            f"Found {total} @ts-nocheck/@ts-ignore directives — "
            "TypeScript errors should be fixed, not suppressed"
        )

    # ------------------------------------------------------------------
    # L2: TypeScript compilation / syntax
    # ------------------------------------------------------------------

    def test_typescript_compilation_succeeds(self):
        """TypeScript compilation (tsc --noEmit) must succeed without type errors."""
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        # Some projects may not have strict tsc; we check that it doesn't outright fail
        if result.returncode != 0:
            # Count actual errors vs. warnings
            error_count = len(re.findall(r"error TS\d+", result.stdout + result.stderr))
            assert error_count == 0, (
                f"TypeScript reports {error_count} error(s):\n"
                f"{(result.stdout + result.stderr)[-3000:]}"
            )

    # ------------------------------------------------------------------
    # L2: Build integrity — no functional regression
    # ------------------------------------------------------------------

    def test_project_builds_successfully(self):
        """npm run build must succeed, proving the fixes introduced no regressions."""
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert result.returncode == 0, (
            f"npm run build failed (rc={result.returncode}):\n"
            f"stderr:\n{result.stderr[-3000:]}"
        )

    # ------------------------------------------------------------------
    # L2: Formatting consistency
    # ------------------------------------------------------------------

    def test_prettier_formatting_consistent(self):
        """If Prettier is configured, running a check must report no violations."""
        # Check whether Prettier is available
        pkg_content = self._read("package.json")
        has_prettier = "prettier" in pkg_content.lower()
        if not has_prettier:
            pytest.skip("Prettier not configured in this project")

        result = subprocess.run(
            ["npx", "prettier", "--check", "src/"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, (
            f"Prettier check failed — files are not formatted:\n"
            f"{result.stdout[-2000:]}"
        )

    def test_no_console_log_left_in_source(self):
        """Source files should not contain stray console.log statements added during fixing."""
        files = self._collect_src_files()
        stray_logs = []
        for fpath in files:
            with open(fpath, "r", errors="ignore") as fh:
                for i, line in enumerate(fh, 1):
                    stripped = line.strip()
                    # Skip commented-out lines
                    if stripped.startswith("//") or stripped.startswith("/*"):
                        continue
                    if "console.log(" in stripped:
                        stray_logs.append(
                            f"{os.path.relpath(fpath, self.REPO_DIR)}:{i}"
                        )
        # Some projects legitimately use console.log; allow a small number
        assert len(stray_logs) <= 3, (
            f"Found {len(stray_logs)} console.log statements — "
            "ensure no debug logging was left during fixing:\n"
            + "\n".join(stray_logs[:10])
        )
