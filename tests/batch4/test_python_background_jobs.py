"""
Test for 'python-background-jobs' skill — Celery Background Jobs
Validates that the Agent created Celery tasks with retry logic, rate limiting,
proper configuration, and scheduling on the celery project.
"""

import ast
import glob
import os
import re

import pytest


class TestPythonBackgroundJobs:
    """Verify Celery background job implementation."""

    REPO_DIR = "/workspace/celery"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _task_files(self):
        return glob.glob(os.path.join(self.REPO_DIR, "**/tasks*.py"), recursive=True)

    def _task_text(self):
        return "\n".join(self._read(f) for f in self._task_files())

    def _celery_config(self):
        files = glob.glob(os.path.join(self.REPO_DIR, "**/celery*.py"), recursive=True)
        return "".join(self._read(f) for f in files)

    # ---- file_path_check ----

    def test_tasks_dir_exists(self):
        """Verifies **/tasks/*.py exists."""
        files = glob.glob(os.path.join(self.REPO_DIR, "**/tasks/*.py"), recursive=True)
        assert len(files) >= 1, "No tasks/*.py files found"

    def test_tasks_py_exists(self):
        """Verifies **/tasks.py exists."""
        files = glob.glob(os.path.join(self.REPO_DIR, "**/tasks.py"), recursive=True)
        assert len(files) >= 1, "No tasks.py files found"

    def test_celeryconfig_exists(self):
        """Verifies celeryconfig.py exists."""
        path = os.path.join(self.REPO_DIR, "celeryconfig.py")
        assert os.path.exists(path), f"File not found: {path}"

    def test_proj_celery_exists(self):
        """Verifies proj/celery.py exists."""
        path = os.path.join(self.REPO_DIR, "proj/celery.py")
        assert os.path.exists(path), f"File not found: {path}"

    # ---- semantic_check ----

    def test_sem_task_decorator(self):
        """Verifies @shared_task or @app.task or @celery.task."""
        text = self._task_text()
        assert (
            "@shared_task" in text or "@app.task" in text or "@celery.task" in text
        ), "No task decorator found"

    def test_sem_retry_keyword(self):
        """Verifies 'retry' in task files."""
        text = self._task_text()
        assert "retry" in text, "'retry' not found in tasks"

    def test_sem_max_retries(self):
        """Verifies 'max_retries' in task files (edge case)."""
        text = self._task_text()
        assert "max_retries" in text, "'max_retries' not found in tasks"

    def test_sem_broker_url(self):
        """Verifies broker_url or BROKER_URL in celery config."""
        config = self._celery_config()
        assert (
            "broker_url" in config or "BROKER_URL" in config
        ), "No broker_url in celery config"

    def test_sem_celery_config_readable(self):
        """Verifies celery config files are readable."""
        config = self._celery_config()
        assert len(config) > 0, "Celery config is empty"

    # ---- functional_check ----

    def test_func_ast_parseable(self):
        """Verifies all task files are valid Python."""
        for f in self._task_files():
            tree = ast.parse(self._read(f))
            assert tree is not None, f"Failed to parse {f}"

    def test_func_retry_calls(self):
        """Verifies at least 1 retry call in task ASTs."""
        all_task_trees = [ast.parse(self._read(f)) for f in self._task_files()]
        retry_calls = [
            n
            for tree in all_task_trees
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and "retry" in ast.dump(n)
        ]
        assert len(retry_calls) >= 1, "No retry calls found in task ASTs"

    def test_func_countdown_backoff(self):
        """Verifies 'countdown' (exponential backoff indicator)."""
        text = self._task_text()
        assert "countdown" in text, "'countdown' not found (no backoff)"

    def test_func_rate_limit(self):
        """Verifies 'rate_limit' in task files."""
        text = self._task_text()
        assert "rate_limit" in text, "'rate_limit' not found in tasks"

    def test_func_beat_schedule(self):
        """Verifies beat_schedule or CELERYBEAT_SCHEDULE in config."""
        config = self._celery_config()
        assert (
            "beat_schedule" in config or "CELERYBEAT_SCHEDULE" in config
        ), "No beat schedule configured"

    def test_func_json_serializer(self):
        """Verifies json serializer and task_serializer in config."""
        config = self._celery_config()
        assert (
            "json" in config and "task_serializer" in config
        ), "JSON task_serializer not configured"

    def test_func_no_pickle_serializer(self):
        """Failure case: task_serializer should not be 'pickle'."""
        config = self._celery_config()
        if "task_serializer" in config:
            assert not re.search(
                r"task_serializer\s*=\s*['\"]pickle['\"]", config
            ), "task_serializer='pickle' is a security risk"

    def test_func_task_routes(self):
        """Verifies task_routes or CELERY_TASK_ROUTES in config."""
        config = self._celery_config()
        assert (
            "task_routes" in config or "CELERY_TASK_ROUTES" in config
        ), "No task routing configured"

    def test_func_error_handling_in_tasks(self):
        """Verifies error handling (try/except) in task files."""
        text = self._task_text()
        assert "except" in text, "No error handling found in tasks"
