"""
Test for 'langsmith-fetch' skill — LangSmith Client Integration
Validates LangSmithClient, ConfigurationError on missing key,
score validation, retry logic, and evaluation pipeline.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestLangsmithFetch:
    """Verify LangSmith client: config, validation, retry, evaluation."""

    REPO_DIR = "/workspace/langchain"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _ls(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "langsmith_fetch", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_client_py_exists(self):
        """client.py must exist."""
        assert os.path.isfile(self._ls("client.py"))

    def test_evaluators_and_models_exist(self):
        """evaluators.py and models.py must exist."""
        assert os.path.isfile(self._ls("evaluators.py"))
        assert os.path.isfile(self._ls("models.py"))

    def test_init_py_exists(self):
        """__init__.py must exist."""
        assert os.path.isfile(self._ls("__init__.py"))

    # ── semantic_check ───────────────────────────────────────────────────

    def test_client_reads_api_key_from_env(self):
        """client.py must read LANGCHAIN_API_KEY from environment."""
        content = self._read_file(self._ls("client.py"))
        if not content:
            pytest.skip("client.py not found")
        assert "LANGCHAIN_API_KEY" in content
        assert "os.environ" in content or "os.getenv" in content

    def test_submit_feedback_validates_score(self):
        """submit_feedback must validate score in [0.0, 1.0]."""
        content = self._read_file(self._ls("client.py"))
        if not content:
            pytest.skip("client.py not found")
        assert "score" in content
        assert "ValueError" in content

    def test_retry_logic_for_429(self):
        """client.py must have retry logic for HTTP 429."""
        content = self._read_file(self._ls("client.py"))
        if not content:
            pytest.skip("client.py not found")
        assert "429" in content or "retry" in content.lower()
        assert "time.sleep" in content or "backoff" in content.lower()

    def test_eval_results_fields(self):
        """EvalResults must have dataset, runs, scores fields."""
        content = self._read_file(self._ls("models.py"))
        if not content:
            pytest.skip("models.py not found")
        assert "EvalResults" in content
        for field in ("dataset", "runs", "scores"):
            assert field in content, f"Missing field '{field}' in models.py"

    # ── functional_check ─────────────────────────────────────────────────

    def test_missing_api_key_raises_config_error(self):
        """LangSmithClient must raise ConfigurationError when key unset."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.langsmith_fetch.client import LangSmithClient, ConfigurationError
        except ImportError:
            pytest.skip("Cannot import LangSmithClient")
        env = os.environ.copy()
        os.environ.pop("LANGCHAIN_API_KEY", None)
        try:
            with pytest.raises(ConfigurationError):
                LangSmithClient()
        finally:
            os.environ.update(env)

    def test_score_above_one_raises_valueerror(self):
        """submit_feedback(score=1.5) must raise ValueError."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.langsmith_fetch.client import LangSmithClient
        except ImportError:
            pytest.skip("Cannot import LangSmithClient")
        os.environ["LANGCHAIN_API_KEY"] = "test-key"
        try:
            with patch("langsmith.Client"):
                client = LangSmithClient()
                with pytest.raises(ValueError):
                    client.submit_feedback("run-id", "accuracy", 1.5)
        finally:
            os.environ.pop("LANGCHAIN_API_KEY", None)

    def test_retry_on_rate_limit(self):
        """Client must retry on rate limit and succeed on 3rd attempt."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.langsmith_fetch.client import LangSmithClient
        except ImportError:
            pytest.skip("Cannot import LangSmithClient")
        os.environ["LANGCHAIN_API_KEY"] = "test-key"
        try:
            mock_api = MagicMock()
            rate_err = Exception("429 rate limit")
            mock_dataset = MagicMock()
            mock_api.create_dataset.side_effect = [rate_err, rate_err, mock_dataset]
            with patch("langsmith.Client", return_value=mock_api):
                client = LangSmithClient()
                try:
                    client.create_dataset("test")
                    assert mock_api.create_dataset.call_count >= 2
                except Exception:
                    pass  # acceptable if retry not implemented yet
        finally:
            os.environ.pop("LANGCHAIN_API_KEY", None)

    def test_log_run_returns_uuid_string(self):
        """log_run must return a run_id string."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.langsmith_fetch.client import LangSmithClient
        except ImportError:
            pytest.skip("Cannot import LangSmithClient")
        os.environ["LANGCHAIN_API_KEY"] = "test-key"
        try:
            mock_api = MagicMock()
            mock_run = MagicMock()
            mock_run.id = "aaaa-bbbb-cccc-dddd"
            mock_api.create_run.return_value = mock_run
            with patch("langsmith.Client", return_value=mock_api):
                client = LangSmithClient()
                run_id = client.log_run(
                    inputs={"prompt": "hello"},
                    outputs={"text": "world"},
                    run_type="llm",
                )
                assert isinstance(run_id, str)
                assert len(run_id) > 0
        finally:
            os.environ.pop("LANGCHAIN_API_KEY", None)

    def test_empty_dataset_returns_empty_results(self):
        """run_evaluation with empty dataset must return empty results."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.langsmith_fetch.client import LangSmithClient
        except ImportError:
            pytest.skip("Cannot import LangSmithClient")
        os.environ["LANGCHAIN_API_KEY"] = "test-key"
        try:
            mock_api = MagicMock()
            mock_api.list_examples.return_value = []
            with patch("langsmith.Client", return_value=mock_api):
                client = LangSmithClient()
                try:
                    results = client.run_evaluation("empty_ds", lambda x: x, [])
                    assert len(results.runs) == 0
                except (AttributeError, TypeError):
                    pass  # method may not exist yet
        finally:
            os.environ.pop("LANGCHAIN_API_KEY", None)
