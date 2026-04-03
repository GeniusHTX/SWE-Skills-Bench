"""
Test for 'fix' skill — React Code Fix & Linter
Validates that the Agent fixed ESLint/Prettier issues in the upgradle React project,
removing eslint-disable comments, fixing formatting, and keeping imports valid.
"""

import os
import re
import subprocess

import pytest


class TestFix:
    """Verify upgradle React code fixes and lint compliance."""

    REPO_DIR = "/workspace/upgradle"

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    # ---- file_path_check ----

    def test_src_directory_exists(self):
        """Verifies that src directory exists."""
        assert os.path.isdir(
            os.path.join(self.REPO_DIR, "src")
        ), "src directory not found"

    def test_app_js_exists(self):
        """Verifies that App.js exists."""
        assert os.path.exists(os.path.join(self.REPO_DIR, "App.js")), "App.js not found"

    def test_board_js_exists(self):
        """Verifies that Board.js exists."""
        assert os.path.exists(
            os.path.join(self.REPO_DIR, "Board.js")
        ), "Board.js not found"

    def test_tile_js_exists(self):
        """Verifies that Tile.js exists."""
        assert os.path.exists(
            os.path.join(self.REPO_DIR, "Tile.js")
        ), "Tile.js not found"

    # ---- semantic_check ----

    def test_all_js_files_accessible(self):
        """All key JS files can be located in src/ or project root."""
        base = os.path.join(self.REPO_DIR, "src")
        candidates = [
            os.path.join(base, "App.js"),
            os.path.join(base, "index.js"),
            os.path.join(base, "components", "Board.js"),
            os.path.join(base, "components", "Tile.js"),
        ]
        existing = [f for f in candidates if os.path.exists(f)]
        assert len(existing) >= 1, "No src JS files found among expected candidates"

    def test_no_eslint_disable_comments(self):
        """No eslint-disable comments should remain in JS source files."""
        base = os.path.join(self.REPO_DIR, "src")
        suppress_pattern = re.compile(r"eslint-disable")
        all_js = []
        for root, _dirs, files in os.walk(base):
            for f in files:
                if f.endswith((".js", ".jsx")):
                    all_js.append(os.path.join(root, f))
        for f in all_js:
            content = self._read(f)
            assert not suppress_pattern.search(
                content
            ), f"eslint-disable comment found in {f}"

    def test_index_js_readable(self):
        """src/index.js should be readable."""
        path = os.path.join(self.REPO_DIR, "src", "index.js")
        if not os.path.exists(path):
            pytest.skip("src/index.js not found")
        content = self._read(path)
        assert len(content) > 0, "src/index.js is empty"

    def test_index_js_has_imports(self):
        """src/index.js should still have necessary imports."""
        path = os.path.join(self.REPO_DIR, "src", "index.js")
        if not os.path.exists(path):
            pytest.skip("src/index.js not found")
        content = self._read(path)
        import_pattern = re.compile(r"^import .* from .*$", re.MULTILINE)
        imports = import_pattern.findall(content)
        assert len(imports) > 0, "src/index.js should still have necessary imports"

    def test_no_eslint_disable_in_root_js(self):
        """Root-level JS files should not contain eslint-disable comments."""
        suppress_pattern = re.compile(r"eslint-disable")
        for name in ["App.js", "Board.js", "Tile.js"]:
            path = os.path.join(self.REPO_DIR, name)
            if os.path.exists(path):
                content = self._read(path)
                assert not suppress_pattern.search(
                    content
                ), f"eslint-disable comment found in {path}"

    def test_import_patterns_valid(self):
        """Import statements in index.js should follow valid ES module pattern."""
        path = os.path.join(self.REPO_DIR, "src", "index.js")
        if not os.path.exists(path):
            pytest.skip("src/index.js not found")
        content = self._read(path)
        import_pattern = re.compile(r"^import .* from .*$", re.MULTILINE)
        imports = import_pattern.findall(content)
        for imp in imports:
            assert "from" in imp, f"Malformed import: {imp}"

    # ---- functional_check ----

    def test_prettier_check_passes(self):
        """Prettier --check should pass on src/ directory."""
        # Ensure npm dependencies are available
        install = subprocess.run(
            ["npm", "ci", "--ignore-scripts"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if install.returncode != 0:
            install = subprocess.run(
                ["npm", "install", "--ignore-scripts"],
                cwd=self.REPO_DIR,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if install.returncode != 0:
                pytest.skip(f"npm install failed: {install.stderr[:200]}")
        result = subprocess.run(
            ["npx", "prettier", "--check", "src/"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert (
            result.returncode == 0
        ), f"Prettier check failed:\n{result.stdout}\n{result.stderr}"

    def test_eslint_passes(self):
        """ESLint should pass on src/ directory."""
        install = subprocess.run(
            ["npm", "ci", "--ignore-scripts"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if install.returncode != 0:
            install = subprocess.run(
                ["npm", "install", "--ignore-scripts"],
                cwd=self.REPO_DIR,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if install.returncode != 0:
                pytest.skip(f"npm install failed: {install.stderr[:200]}")
        result = subprocess.run(
            ["npx", "eslint", "src/"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert (
            result.returncode == 0
        ), f"ESLint failed:\n{result.stdout}\n{result.stderr}"

    def test_prettier_diff_not_present(self):
        """Prettier should produce no diff (formatting is fully fixed)."""
        install = subprocess.run(
            ["npm", "ci", "--ignore-scripts"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if install.returncode != 0:
            install = subprocess.run(
                ["npm", "install", "--ignore-scripts"],
                cwd=self.REPO_DIR,
                capture_output=True,
                text=True,
                timeout=120,
            )
            if install.returncode != 0:
                pytest.skip(f"npm install failed: {install.stderr[:200]}")
        result = subprocess.run(
            ["npx", "prettier", "--list-different", "src/"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        files_with_diff = result.stdout.strip()
        assert (
            files_with_diff == ""
        ), f"Prettier diff still present in:\n{files_with_diff}"
