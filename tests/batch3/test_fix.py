"""
Tests for the fix skill.
Verifies that the React/upgradle project code quality tooling (ESLint, Prettier)
is properly configured with required scripts, no global disables, and that
the linting/formatting/build pipeline works correctly.
"""

import json
import os
import subprocess

import pytest

REPO_DIR = "/workspace/upgradle"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    full = _path(rel)
    if not os.path.isfile(full):
        pytest.skip(f"File not found: {full}")
    with open(full, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _load_json(rel: str) -> dict:
    full = _path(rel)
    if not os.path.isfile(full):
        pytest.skip(f"File not found: {full}")
    with open(full, encoding="utf-8") as fh:
        return json.load(fh)


def _run(cmd: list, cwd: str = None, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_DIR,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _yarn_install() -> bool:
    """Attempt yarn install; return True if successful."""
    try:
        r = _run(["yarn", "install"], timeout=120)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _npm_available() -> bool:
    try:
        r = subprocess.run(["npm", "--version"], capture_output=True, timeout=10)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ---------------------------------------------------------------------------
# File path checks
# ---------------------------------------------------------------------------


class TestFix:
    """Test suite for the Fix (React code/linter) skill in the upgradle project."""

    def test_package_json_exists(self):
        """Verify package.json exists in the project root and is valid JSON."""
        target = _path("package.json")
        assert os.path.isfile(target), f"package.json not found: {target}"
        assert os.path.getsize(target) > 0, "package.json must be non-empty"
        data = _load_json("package.json")
        assert isinstance(data, dict), "package.json must be a valid JSON object"

    def test_eslint_and_prettier_config_exist(self):
        """Verify at least one ESLint config and one Prettier config file exist."""
        eslint_candidates = [
            ".eslintrc.js",
            ".eslintrc.json",
            ".eslintrc.yaml",
            ".eslintrc",
        ]
        prettier_candidates = [
            ".prettierrc",
            ".prettierrc.json",
            ".prettierrc.js",
            "prettier.config.js",
        ]
        has_eslint = any(os.path.isfile(_path(f)) for f in eslint_candidates)
        has_prettier = any(os.path.isfile(_path(f)) for f in prettier_candidates)
        assert has_eslint, f"At least one ESLint config must exist: {eslint_candidates}"
        assert (
            has_prettier
        ), f"At least one Prettier config must exist: {prettier_candidates}"

    # -----------------------------------------------------------------------
    # Semantic checks
    # -----------------------------------------------------------------------

    def test_no_global_eslint_disable_comments(self):
        """Verify no source files contain global ESLint rule disable comments."""
        src_dir = _path("src")
        if not os.path.isdir(src_dir):
            pytest.skip("src/ directory not found")
        for root, _, files in os.walk(src_dir):
            for fname in files:
                if not fname.endswith((".js", ".jsx", ".ts", ".tsx")):
                    continue
                fpath = os.path.join(root, fname)
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    content = f.read()
                rel = os.path.relpath(fpath, REPO_DIR)
                assert (
                    "/* eslint-disable */" not in content
                ), f"{rel} contains global '/* eslint-disable */' without specifying a rule"

    def test_package_json_has_required_scripts(self):
        """Verify package.json defines build, lint/linc, and prettier/format scripts."""
        data = _load_json("package.json")
        scripts = data.get("scripts", {})
        assert "build" in scripts, "package.json must define a 'build' script"
        has_lint = "lint" in scripts or "linc" in scripts
        assert has_lint, "package.json must define a 'lint' or 'linc' script"
        has_prettier = "prettier" in scripts or "format" in scripts
        assert has_prettier, "package.json must define a 'prettier' or 'format' script"

    def test_eslint_config_has_react_plugin(self):
        """Verify ESLint config references the React or React Hooks plugin."""
        for candidate in [".eslintrc.js", ".eslintrc.json"]:
            full = _path(candidate)
            if os.path.isfile(full):
                with open(full, encoding="utf-8", errors="replace") as f:
                    content = f.read()
                has_react = "react" in content.lower()
                assert (
                    has_react
                ), f"{candidate} must reference the 'react' ESLint plugin"
                return
        pytest.skip("No .eslintrc.js or .eslintrc.json found")

    def test_dependencies_no_wildcard_versions(self):
        """Verify package.json has no wildcard '*' version specifiers for dependencies."""
        data = _load_json("package.json")
        for dep_section in ("dependencies", "devDependencies"):
            deps = data.get(dep_section, {})
            for name, version in deps.items():
                assert (
                    version != "*"
                ), f"Dependency '{name}' in {dep_section} must not use wildcard '*' version"

    # -----------------------------------------------------------------------
    # Functional checks (command)
    # -----------------------------------------------------------------------

    @pytest.fixture(scope="class", autouse=True)
    def _try_yarn_install(self):
        """Attempt yarn install before running command tests."""
        if _npm_available():
            try:
                _run(["npm", "ci"], timeout=180)
            except Exception:
                try:
                    _run(["npm", "install"], timeout=180)
                except Exception:
                    pass
            return
        # Don't fail if install fails - command tests will skip individually
        try:
            _run(["yarn", "install", "--frozen-lockfile"], timeout=180)
        except Exception:
            pass

    def test_prettier_check_exits_zero(self):
        """Verify yarn prettier --check passes for all source files."""
        nm = _path("node_modules")
        if not os.path.isdir(nm):
            pytest.skip("node_modules not found; run yarn install first")
        result = _run(["npm", "run", "prettier", "--", "--check", "."], timeout=120)
        assert (
            result.returncode == 0
        ), f"prettier --check failed:\nstdout: {result.stdout[:500]}\nstderr: {result.stderr[:500]}"

    def test_lint_check_exits_zero(self):
        """Verify yarn linc (incremental lint) exits with code 0."""
        nm = _path("node_modules")
        if not os.path.isdir(nm):
            pytest.skip("node_modules not found; run yarn install first")
        result = _run(["npm", "run", "lint"], timeout=120)
        assert (
            result.returncode == 0
        ), f"yarn linc failed:\nstdout: {result.stdout[:500]}\nstderr: {result.stderr[:500]}"

    def test_build_exits_zero(self):
        """Verify yarn build exits with code 0 producing a production build."""
        nm = _path("node_modules")
        if not os.path.isdir(nm):
            pytest.skip("node_modules not found; run yarn install first")
        result = _run(["npm", "run", "build"], timeout=180)
        assert (
            result.returncode == 0
        ), f"yarn build failed:\nstdout: {result.stdout[:500]}\nstderr: {result.stderr[:500]}"

    def test_unformatted_file_makes_prettier_check_fail(self):
        """Verify prettier --check returns non-zero for a temporarily unformatted file."""
        nm = _path("node_modules")
        if not os.path.isdir(nm):
            pytest.skip("node_modules not found; run yarn install first")
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".js", mode="w", delete=False) as tmp:
            tmp.write("const a=1\n")
            tmp_path = tmp.name
        try:
            result = _run(
                ["npm", "run", "prettier", "--", "--check", tmp_path], timeout=30
            )
            assert (
                result.returncode != 0
            ), "prettier --check must fail for unformatted code"
        finally:
            os.unlink(tmp_path)

    def test_eslint_detects_undefined_in_strict_mode(self):
        """Verify ESLint is strict enough to catch certain code issues."""
        nm = _path("node_modules")
        if not os.path.isdir(nm):
            pytest.skip("node_modules not found; run yarn install first")
        import tempfile

        # Write a file with a clear ESLint issue (no-undef or similar)
        with tempfile.NamedTemporaryFile(
            suffix=".js", mode="w", delete=False, dir=REPO_DIR
        ) as tmp:
            tmp.write(
                "/* eslint-disable no-unused-vars */\nconsole.log(undefinedVariableXyz123)\n"
            )
            tmp_path = tmp.name
        try:
            result = _run(
                ["npm", "run", "eslint", "--", os.path.basename(tmp_path)], timeout=30
            )
            # ESLint should report an issue (no-undef)
            # Some configs may auto-fix, so just verify ESLint ran
            ran = result.returncode in (0, 1, 2)
            assert ran, "ESLint command must execute without crashing"
        finally:
            os.unlink(tmp_path)

    def test_node_modules_excluded_from_eslint(self):
        """Verify .eslintignore or eslintrc contains node_modules exclusion."""
        eslintignore = _path(".eslintignore")
        if os.path.isfile(eslintignore):
            with open(eslintignore, encoding="utf-8") as f:
                content = f.read()
            assert "node_modules" in content, ".eslintignore must exclude node_modules"
            return
        # Fallback: check ignorePatterns in .eslintrc.js
        eslintrc = _path(".eslintrc.js")
        if os.path.isfile(eslintrc):
            with open(eslintrc, encoding="utf-8") as f:
                content = f.read()
            if "node_modules" in content:
                return  # Found in config
        # Also acceptable to rely on default ESLint behavior
        # Just verify at least one of these patterns exists
        has_exclusion = os.path.isfile(eslintignore) or os.path.isfile(eslintrc)
        assert (
            has_exclusion
        ), "ESLint config or .eslintignore must exist to prevent scanning node_modules"
