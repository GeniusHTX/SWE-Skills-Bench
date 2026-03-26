"""
Test for 'langsmith-fetch' skill — LangSmith Fetch
Validates that the Agent created a LangSmith trace fetching example for LangChain
with API connection, filtering, pagination, and formatted output.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestLangsmithFetch.REPO_DIR)


class TestLangsmithFetch:
    """Verify LangSmith trace fetching script."""

    REPO_DIR = "/workspace/langchain"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_script_exists(self):
        """examples/langsmith_fetch.py must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "examples", "langsmith_fetch.py")
        )

    def test_script_compiles(self):
        """langsmith_fetch.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/langsmith_fetch.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_has_main_entry_point(self):
        """Script must have a __main__ entry point."""
        content = self._read("examples", "langsmith_fetch.py")
        assert re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', content)

    # ------------------------------------------------------------------
    # L1: API connection
    # ------------------------------------------------------------------

    def test_uses_langsmith_api_key(self):
        """Script must read LANGSMITH_API_KEY from environment."""
        content = self._read("examples", "langsmith_fetch.py")
        patterns = [r"LANGSMITH_API_KEY", r"api_key", r"langsmith.*key"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not reference LangSmith API key"

    def test_uses_langsmith_endpoint(self):
        """Script must support configurable LANGSMITH_ENDPOINT."""
        content = self._read("examples", "langsmith_fetch.py")
        patterns = [
            r"LANGSMITH_ENDPOINT",
            r"endpoint",
            r"api_url",
            r"base_url",
            r"langsmith.*url",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not reference LangSmith endpoint"

    def test_references_langsmith_client(self):
        """Script must use LangSmith Client or similar SDK."""
        content = self._read("examples", "langsmith_fetch.py")
        patterns = [
            r"Client\(",
            r"langsmith",
            r"LangSmithClient",
            r"from\s+langsmith",
            r"import\s+langsmith",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not use LangSmith Client"

    # ------------------------------------------------------------------
    # L1: Filtering
    # ------------------------------------------------------------------

    def test_supports_time_range_filter(self):
        """Script must support filtering traces by time range."""
        content = self._read("examples", "langsmith_fetch.py")
        patterns = [
            r"start_time",
            r"end_time",
            r"time_range",
            r"date",
            r"since",
            r"until",
            r"datetime",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not support time range filtering"

    def test_supports_run_type_filter(self):
        """Script must support filtering by run type (chain, llm, tool)."""
        content = self._read("examples", "langsmith_fetch.py")
        patterns = [r"run_type", r"chain|llm|tool", r"type.*filter"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not support run type filtering"

    def test_supports_status_filter(self):
        """Script must support filtering by status (success, error)."""
        content = self._read("examples", "langsmith_fetch.py")
        patterns = [r"status", r"success", r"error", r"is_error"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not support status filtering"

    # ------------------------------------------------------------------
    # L1: Trace display
    # ------------------------------------------------------------------

    def test_displays_trace_summary(self):
        """Script must format and display trace summaries."""
        content = self._read("examples", "langsmith_fetch.py")
        fields = [
            r"run_id",
            r"name",
            r"run_type",
            r"status",
            r"latency",
            r"token",
            r"duration",
        ]
        matches = sum(1 for p in fields if re.search(p, content, re.IGNORECASE))
        assert matches >= 3, (
            f"Trace summary includes only {matches} of expected fields "
            "(need run_id, name, run_type, status, latency, tokens)"
        )

    def test_shows_error_info_for_failed_traces(self):
        """Script must display error details for failed traces."""
        content = self._read("examples", "langsmith_fetch.py")
        patterns = [
            r"error.*message",
            r"error_info",
            r"traceback",
            r"exception",
            r"error.*detail",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not display error information for failed traces"

    # ------------------------------------------------------------------
    # L2: Pagination
    # ------------------------------------------------------------------

    def test_handles_pagination(self):
        """Script must handle paginated API responses."""
        content = self._read("examples", "langsmith_fetch.py")
        patterns = [
            r"page",
            r"offset",
            r"cursor",
            r"limit",
            r"next_page",
            r"has_more",
            r"paginate",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not handle pagination"

    def test_configurable_result_limit(self):
        """Script must support a configurable limit on total traces."""
        content = self._read("examples", "langsmith_fetch.py")
        patterns = [r"limit", r"max_results", r"max_traces", r"count"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not support configurable result limit"

    # ------------------------------------------------------------------
    # L2: Output format
    # ------------------------------------------------------------------

    def test_supports_json_output(self):
        """Script must support JSON output mode."""
        content = self._read("examples", "langsmith_fetch.py")
        patterns = [r"json", r"JSON", r"--format", r"output.*format"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not support JSON output"
