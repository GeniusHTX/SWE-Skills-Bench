"""
Test for 'langsmith-fetch' skill — LangSmith Data Fetch Utility
Validates that the Agent created a LangSmith fetch utility with CLI interface,
JSON/CSV export, and proper field handling.
"""

import os
import ast
import subprocess
import pytest


class TestLangsmithFetch:
    """Verify LangSmith fetch utility in LangChain."""

    REPO_DIR = "/workspace/langchain"

    # ------------------------------------------------------------------
    # L1: file existence & syntax
    # ------------------------------------------------------------------

    def test_fetch_script_exists(self):
        """examples/langsmith_fetch.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "langsmith_fetch.py")
        assert os.path.isfile(fpath), "langsmith_fetch.py not found"

    def test_fetch_script_compiles(self):
        """langsmith_fetch.py must compile."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/langsmith_fetch.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: CLI & content verification
    # ------------------------------------------------------------------

    def _read_source(self):
        fpath = os.path.join(self.REPO_DIR, "examples", "langsmith_fetch.py")
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def test_help_flag_works(self):
        """--help must display usage information."""
        result = subprocess.run(
            ["python", "examples/langsmith_fetch.py", "--help"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"--help failed:\n{result.stderr}"
        assert len(result.stdout) > 20, "--help output is too short"

    def test_project_argument(self):
        """CLI must support --project argument."""
        result = subprocess.run(
            ["python", "examples/langsmith_fetch.py", "--help"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "--project" in result.stdout, "--project not in help output"

    def test_output_argument(self):
        """CLI must support --output argument."""
        result = subprocess.run(
            ["python", "examples/langsmith_fetch.py", "--help"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "--output" in result.stdout, "--output not in help output"

    def test_format_argument(self):
        """CLI must support --format argument (json or csv)."""
        result = subprocess.run(
            ["python", "examples/langsmith_fetch.py", "--help"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "--format" in result.stdout, "--format not in help output"

    def test_source_uses_argparse(self):
        """Script should use argparse or click for CLI parsing."""
        source = self._read_source()
        assert (
            "argparse" in source or "click" in source or "typer" in source
        ), "No CLI framework (argparse/click/typer) found"

    def test_required_export_fields(self):
        """Script must reference required export fields."""
        source = self._read_source()
        fields = [
            "run_id",
            "inputs",
            "outputs",
            "feedback_scores",
            "start_time",
            "end_time",
        ]
        found = sum(1 for f in fields if f in source)
        assert found >= 4, f"Only {found}/6 required fields found in source"

    def test_json_export_support(self):
        """Script must support JSON export."""
        source = self._read_source()
        assert "json" in source.lower(), "No JSON export support found"

    def test_csv_export_support(self):
        """Script must support CSV export."""
        source = self._read_source()
        assert "csv" in source.lower(), "No CSV export support found"

    def test_api_key_handling(self):
        """Script must handle API authentication via environment variable."""
        source = self._read_source()
        auth_patterns = [
            "API_KEY",
            "api_key",
            "LANGSMITH",
            "LANGCHAIN",
            "environ",
            "getenv",
        ]
        found = sum(1 for p in auth_patterns if p in source)
        assert found >= 2, "Insufficient API key handling"

    def test_pagination_support(self):
        """Script should handle pagination for large result sets."""
        source = self._read_source()
        page_patterns = ["page", "offset", "cursor", "limit", "next", "pagina", "batch"]
        found = any(p in source.lower() for p in page_patterns)
        assert found, "No pagination handling found"
