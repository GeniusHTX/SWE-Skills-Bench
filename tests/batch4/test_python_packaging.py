"""
Test for 'python-packaging' skill — Python Packaging
Validates pyproject.toml configuration, sample_lib package with TextProcessor,
CLI entry point, and proper packaging structure.
"""

import os
import re
import sys
import subprocess
import pytest


class TestPythonPackaging:
    """Tests for Python packaging in the packaging repo."""

    REPO_DIR = "/workspace/packaging"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    # --- File Path Checks ---

    def test_pyproject_toml_exists(self):
        """Verifies that pyproject.toml exists."""
        path = os.path.join(self.REPO_DIR, "pyproject.toml")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_sample_lib_init_py_exists(self):
        """Verifies that sample_lib/__init__.py exists."""
        path = os.path.join(self.REPO_DIR, "sample_lib", "__init__.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_sample_lib_core_py_exists(self):
        """Verifies that sample_lib/core.py exists."""
        path = os.path.join(self.REPO_DIR, "sample_lib", "core.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_sample_lib_cli_py_exists(self):
        """Verifies that sample_lib/cli.py exists."""
        path = os.path.join(self.REPO_DIR, "sample_lib", "cli.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_pyproject_has_project_section(self):
        """pyproject.toml has [project] section."""
        content = self._read("pyproject.toml")
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        config = tomllib.loads(content)
        assert "project" in config, "'project' section not found in pyproject.toml"

    def test_sem_pyproject_has_scripts_with_textproc(self):
        """pyproject.toml has scripts section with textproc entry."""
        content = self._read("pyproject.toml")
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        config = tomllib.loads(content)
        assert "scripts" in config.get("project", {}), "'scripts' not in [project]"
        scripts = config["project"]["scripts"]
        assert any(
            "textproc" in str(v) for v in scripts.values()
        ), f"No script entry references 'textproc': {scripts}"

    def test_sem_pyproject_has_requires_python(self):
        """pyproject.toml has requires-python field."""
        content = self._read("pyproject.toml")
        assert (
            "requires-python" in content
        ), "'requires-python' not found in pyproject.toml"

    def test_sem_pyproject_has_optional_dependencies(self):
        """pyproject.toml has [project.optional-dependencies] or [dependency-groups] with dev/test extras."""
        content = self._read("pyproject.toml")
        has_optional = "optional-dependencies" in content
        has_dep_groups = "dependency-groups" in content
        assert (
            has_optional or has_dep_groups
        ), "Neither [project.optional-dependencies] nor [dependency-groups] found"

    def test_sem_import_text_processor(self):
        """from sample_lib.core import TextProcessor — importable."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from sample_lib.core import TextProcessor

            assert TextProcessor is not None
        finally:
            sys.path[:] = old_path

    def test_sem_text_processor_methods(self):
        """TextProcessor has methods: analyze, compare, summarize."""
        content = self._read("sample_lib/core.py")
        for method in ["analyze", "compare", "summarize"]:
            assert re.search(
                rf"def\s+{method}\s*\(", content
            ), f"Method {method} not found"

    # --- Functional Checks (import) ---

    def test_func_analyze_word_count(self):
        """TextProcessor().analyze('Hello world. Hello.') returns dict with word_count == 3."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from sample_lib.core import TextProcessor

            result = TextProcessor().analyze("Hello world. Hello.")
            assert isinstance(result, dict)
            assert (
                result["word_count"] == 3
            ), f"Expected word_count=3, got {result.get('word_count')}"
        finally:
            sys.path[:] = old_path

    def test_func_analyze_sentence_count(self):
        """TextProcessor().analyze('Hello world. Hello.')['sentence_count'] == 2."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from sample_lib.core import TextProcessor

            result = TextProcessor().analyze("Hello world. Hello.")
            assert (
                result["sentence_count"] == 2
            ), f"Expected 2, got {result.get('sentence_count')}"
        finally:
            sys.path[:] = old_path

    def test_func_analyze_top_words(self):
        """TextProcessor().analyze('Hello world. Hello.')['top_words'][0][0].lower() == 'hello'."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from sample_lib.core import TextProcessor

            result = TextProcessor().analyze("Hello world. Hello.")
            assert (
                result["top_words"][0][0].lower() == "hello"
            ), f"Expected 'hello' as top word, got {result['top_words'][0][0]}"
        finally:
            sys.path[:] = old_path

    def test_func_analyze_empty_string(self):
        """TextProcessor().analyze('') returns dict with word_count==0 and empty top_words."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from sample_lib.core import TextProcessor

            result = TextProcessor().analyze("")
            assert result["word_count"] == 0
            assert len(result["top_words"]) == 0
        finally:
            sys.path[:] = old_path

    def test_func_compare_partial_overlap(self):
        """TextProcessor().compare('cat dog', 'cat fish')['similarity'] ≈ 1/3."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from sample_lib.core import TextProcessor

            result = TextProcessor().compare("cat dog", "cat fish")
            assert result["similarity"] == pytest.approx(
                1 / 3, rel=1e-3
            ), f"Expected ~0.333, got {result['similarity']}"
        finally:
            sys.path[:] = old_path

    def test_func_compare_identical(self):
        """TextProcessor().compare('cat dog', 'cat dog')['similarity'] == 1.0."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from sample_lib.core import TextProcessor

            result = TextProcessor().compare("cat dog", "cat dog")
            assert result["similarity"] == 1.0
        finally:
            sys.path[:] = old_path

    def test_func_compare_no_overlap(self):
        """TextProcessor().compare('cat', 'dog')['similarity'] == 0.0."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from sample_lib.core import TextProcessor

            result = TextProcessor().compare("cat", "dog")
            assert result["similarity"] == 0.0
        finally:
            sys.path[:] = old_path

    def test_func_compare_common_words(self):
        """TextProcessor().compare('cat dog', 'cat fish')['common_words'] == {'cat'}."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from sample_lib.core import TextProcessor

            result = TextProcessor().compare("cat dog", "cat fish")
            assert result["common_words"] == {
                "cat"
            }, f"Expected {{'cat'}}, got {result['common_words']}"
        finally:
            sys.path[:] = old_path

    def test_func_cli_missing_file_exit_code(self):
        """CLI analyze with missing file -> exit code 1, error on stderr."""
        result = subprocess.run(
            [sys.executable, "-m", "sample_lib.cli", "analyze", "nonexistent_file.txt"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            result.returncode != 0
        ), f"Expected non-zero exit code, got {result.returncode}"
