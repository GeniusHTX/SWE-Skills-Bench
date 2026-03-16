"""
Test for 'fix' skill — React Code Fix & Linter
Validates that the Agent scanned and fixed all ESLint violations in the upgradle
TypeScript codebase so that `npm run lint` passes cleanly.
"""

import os
import subprocess
import glob
import re
import pytest

from _dependency_utils import ensure_npm_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_npm_dependencies(TestFix.REPO_DIR)


class TestFix:
    """Verify ESLint violations in upgradle src/ have been fixed."""

    REPO_DIR = "/workspace/upgradle"

    # ------------------------------------------------------------------
    # L1: basic file / project integrity
    # ------------------------------------------------------------------

    def test_src_directory_exists(self):
        """src/ directory must exist in the repository."""
        assert os.path.isdir(
            os.path.join(self.REPO_DIR, "src")
        ), "src/ directory is missing"

    def test_package_json_exists(self):
        """package.json must exist at repo root."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "package.json")
        ), "package.json is missing"

    def test_ts_files_exist_in_src(self):
        """At least one .ts file must exist under src/."""
        ts_files = glob.glob(
            os.path.join(self.REPO_DIR, "src", "**", "*.ts"), recursive=True
        )
        assert len(ts_files) >= 1, "No .ts files found under src/"

    # ------------------------------------------------------------------
    # L2: functional lint verification
    # ------------------------------------------------------------------

    def test_npm_run_lint_exit_code(self):
        """npm run lint must exit with code 0 (no error-level reports)."""
        result = subprocess.run(
            ["npm", "run", "lint"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert result.returncode == 0, (
            f"npm run lint failed (rc={result.returncode}):\n"
            f"stdout={result.stdout[-2000:]}\nstderr={result.stderr[-2000:]}"
        )

    def test_no_eslint_errors_in_stdout(self):
        """Lint output must not contain error-level reports."""
        result = subprocess.run(
            ["npm", "run", "lint"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
        combined = result.stdout + result.stderr
        # ESLint outputs "X errors" when there are error-level problems
        match = re.search(r"(\d+)\s+error", combined)
        if match:
            error_count = int(match.group(1))
            assert (
                error_count == 0
            ), f"ESLint reported {error_count} error(s):\n{combined[-2000:]}"

    def test_no_unused_vars_in_src(self):
        """No @typescript-eslint/no-unused-vars violations should remain."""
        result = subprocess.run(
            ["npx", "eslint", "src/", "--format", "json"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
        import json

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.skip("ESLint JSON output could not be parsed")
        for file_report in data:
            for msg in file_report.get("messages", []):
                if msg.get("severity", 0) >= 2:
                    assert "no-unused-vars" not in msg.get(
                        "ruleId", ""
                    ), f"no-unused-vars error in {file_report['filePath']}:{msg['line']}"

    def test_no_explicit_any_in_src(self):
        """No @typescript-eslint/no-explicit-any errors should remain."""
        result = subprocess.run(
            ["npx", "eslint", "src/", "--format", "json"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
        import json

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.skip("ESLint JSON output could not be parsed")
        for file_report in data:
            for msg in file_report.get("messages", []):
                if msg.get("severity", 0) >= 2:
                    assert "no-explicit-any" not in msg.get(
                        "ruleId", ""
                    ), f"no-explicit-any error in {file_report['filePath']}:{msg['line']}"

    def test_no_eqeqeq_violations_in_src(self):
        """No eqeqeq (loose equality) errors should remain."""
        result = subprocess.run(
            ["npx", "eslint", "src/", "--format", "json"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
        import json

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.skip("ESLint JSON output could not be parsed")
        for file_report in data:
            for msg in file_report.get("messages", []):
                if msg.get("severity", 0) >= 2:
                    assert "eqeqeq" not in msg.get(
                        "ruleId", ""
                    ), f"eqeqeq error in {file_report['filePath']}:{msg['line']}"

    def test_no_loose_equality_operators(self):
        """Source files should not contain == or != (use === / !==)."""
        ts_files = glob.glob(
            os.path.join(self.REPO_DIR, "src", "**", "*.ts"), recursive=True
        )
        for fpath in ts_files:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                for lineno, line in enumerate(f, 1):
                    stripped = line.strip()
                    if stripped.startswith("//") or stripped.startswith("*"):
                        continue
                    # Match == or != but not === or !==
                    if re.search(r"(?<!=)==(?!=)", stripped) or re.search(
                        r"(?<!!)!=(?!=)", stripped
                    ):
                        pytest.fail(
                            f"Loose equality in {os.path.relpath(fpath, self.REPO_DIR)}:{lineno}: {stripped[:120]}"
                        )

    def test_no_new_lint_warnings_introduced(self):
        """npm run lint should produce no new warning-level reports beyond baseline."""
        result = subprocess.run(
            ["npm", "run", "lint"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
        combined = result.stdout + result.stderr
        match = re.search(r"(\d+)\s+warning", combined)
        if match:
            warning_count = int(match.group(1))
            # Acceptance criteria: no *new* warnings. Allow 0.
            assert (
                warning_count == 0
            ), f"ESLint reported {warning_count} warning(s); task requires 0 new warnings."

    def test_test_files_not_modified(self):
        """Test files must not have been modified by the Agent."""
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        changed_files = result.stdout.strip().splitlines()
        test_changes = [
            f for f in changed_files if f.startswith("test") or "/test" in f
        ]
        assert (
            len(test_changes) == 0
        ), f"Test files were modified but should be preserved: {test_changes}"

    def test_existing_tests_still_pass(self):
        """All existing tests in the project must continue to pass."""
        pkg_json = os.path.join(self.REPO_DIR, "package.json")
        import json

        with open(pkg_json) as f:
            pkg = json.load(f)
        if "test" not in pkg.get("scripts", {}):
            pytest.skip("No test script defined in package.json")
        result = subprocess.run(
            ["npm", "test"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert (
            result.returncode == 0
        ), f"Existing tests failed (rc={result.returncode}):\n{result.stderr[-2000:]}"
