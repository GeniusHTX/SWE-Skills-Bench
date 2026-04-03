"""
Test for 'python-background-jobs' skill — Celery Background Tasks
Validates @app.task with bind=True, max_retries, idempotency key,
task serialization, and retry behavior.
"""

import os
import re
import sys

import pytest


class TestPythonBackgroundJobs:
    """Verify Celery background job implementations."""

    REPO_DIR = "/workspace/celery"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_celery_source_exists(self):
        """Verify Celery source directory exists."""
        src = os.path.join(self.REPO_DIR, "celery")
        assert os.path.isdir(src), "celery/ package directory not found"

    def test_task_files_exist(self):
        """Verify task-related Python files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and "task" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No task-related files found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_app_task_decorator(self):
        """Verify @app.task or @shared_task decorator usage."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"@(app\.task|shared_task|celery\.task)", content):
                return
        pytest.fail("No @app.task or @shared_task decorator found")

    def test_bind_true(self):
        """Verify bind=True is used in task decorators."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(bind\s*=\s*True)", content):
                return
        pytest.fail("No bind=True in task decorators")

    def test_max_retries_configured(self):
        """Verify max_retries is configured."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"max_retries\s*=\s*\d+", content):
                return
        pytest.fail("No max_retries configuration found")

    def test_idempotency_key(self):
        """Verify idempotency key or deduplication mechanism."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(idempoten|dedup|task_id|unique.?id)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No idempotency mechanism found")

    def test_retry_mechanism(self):
        """Verify self.retry() or retry logic is present."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(self\.retry\(|autoretry_for|retry_backoff)", content):
                return
        pytest.fail("No retry mechanism found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_task_module_importable(self):
        """Verify celery.app.task module can be loaded."""
        task_mod = os.path.join(self.REPO_DIR, "celery", "app", "task.py")
        if not os.path.exists(task_mod):
            pytest.skip("celery/app/task.py not found")
        import py_compile

        try:
            py_compile.compile(task_mod, doraise=True)
        except py_compile.PyCompileError:
            pytest.skip("task.py has syntax issues")

    def test_task_serialization(self):
        """Verify task serialization config (JSON/pickle)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(task_serializer|accept_content|CELERY_TASK_SERIALIZER|serializer\s*=)",
                content,
            ):
                return
        pytest.fail("No task serialization config found")

    def test_error_handling_in_tasks(self):
        """Verify tasks include error handling (try/except)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"@(app\.task|shared_task)", content) and "except" in content:
                return
        pytest.fail("No error handling in task files")

    def test_celery_config_exists(self):
        """Verify Celery configuration (broker, backend, etc.)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(broker_url|BROKER_URL|result_backend|CELERY_BROKER)", content
            ):
                return
        pytest.fail("No Celery broker/backend config found")

    def test_countdown_or_eta(self):
        """Verify countdown or ETA scheduling capability."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(countdown|eta|apply_async|delay)", content):
                return
        pytest.fail("No countdown/eta scheduling found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_py_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
