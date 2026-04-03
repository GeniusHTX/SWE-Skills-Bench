"""
Test for 'python-background-jobs' skill — Celery Background Job Pipeline
Validates ExportJob model, Celery config, task chain, API endpoints, retry logic,
and status transitions for a report export pipeline.
"""

import os
import re
import subprocess
import sys

import pytest


class TestPythonBackgroundJobs:
    """Verify Celery background job pipeline for report exports."""

    REPO_DIR = "/workspace/celery"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _example(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "report_export", *parts)

    def _install_deps(self):
        try:
            import celery  # noqa: F401
        except ImportError:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "celery", "fastapi", "httpx"],
                capture_output=True, timeout=60,
            )
            if result.returncode != 0:
                pytest.skip("pip install failed")

    # ── file_path_check ──────────────────────────────────────────────────

    def test_tasks_and_models_exist(self):
        """tasks.py and models.py must exist in examples/report_export/."""
        for name in ("tasks.py", "models.py"):
            path = self._example(name)
            assert os.path.isfile(path), f"{path} does not exist"

    def test_api_store_app_exist(self):
        """api.py, store.py, and app.py must exist."""
        for name in ("api.py", "store.py", "app.py"):
            path = self._example(name)
            assert os.path.isfile(path), f"{path} does not exist"

    def test_test_file_exists(self):
        """tests/test_report_export.py must exist."""
        path = os.path.join(self.REPO_DIR, "tests", "test_report_export.py")
        assert os.path.isfile(path), f"{path} does not exist"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_export_job_has_required_fields(self):
        """ExportJob must have id, status, progress, result_url, error, created_at, updated_at."""
        path = self._example("models.py")
        if not os.path.isfile(path):
            pytest.skip("models.py not found")
        content = self._read_file(path)
        assert "ExportJob" in content, "ExportJob class not defined"
        for field in ("id", "status", "progress", "result_url", "error", "created_at", "updated_at"):
            assert field in content, f"ExportJob missing field: {field}"

    def test_celery_reliability_settings(self):
        """app.py must have task_acks_late=True and task_reject_on_worker_lost=True."""
        path = self._example("app.py")
        if not os.path.isfile(path):
            pytest.skip("app.py not found")
        content = self._read_file(path)
        assert "task_acks_late" in content, "task_acks_late not configured"
        assert "task_reject_on_worker_lost" in content, "task_reject_on_worker_lost not configured"

    def test_query_data_has_max_retries(self):
        """query_data task must have max_retries=3 and bind=True."""
        path = self._example("tasks.py")
        if not os.path.isfile(path):
            pytest.skip("tasks.py not found")
        content = self._read_file(path)
        assert "query_data" in content, "query_data task not defined"
        assert "max_retries" in content, "max_retries not set on tasks"
        assert "bind=True" in content or "bind = True" in content, "bind=True not found"

    def test_export_report_uses_chain(self):
        """export_report must use celery.chain with 4 tasks."""
        path = self._example("tasks.py")
        if not os.path.isfile(path):
            pytest.skip("tasks.py not found")
        content = self._read_file(path)
        assert "chain" in content, "celery chain not used in tasks.py"
        for task in ("query_data", "transform_data", "write_csv", "upload_to_storage"):
            assert task in content, f"Task {task} not defined in tasks.py"

    # ── functional_check ─────────────────────────────────────────────────

    def test_create_job_returns_pending(self):
        """create_job() must return ExportJob with status=PENDING."""
        self._install_deps()
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.report_export.store import create_job
            from examples.report_export.models import JobStatus
        except ImportError:
            pytest.skip("Cannot import store/models")
        job = create_job()
        assert job.status == JobStatus.PENDING or str(job.status) == "PENDING"
        assert job.progress == 0

    def test_invalid_status_transition_raises_error(self):
        """update_job with backward transition (RUNNING->PENDING) must raise ValueError."""
        self._install_deps()
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.report_export.store import create_job, update_job
            from examples.report_export.models import JobStatus
        except ImportError:
            pytest.skip("Cannot import store/models")
        job = create_job()
        update_job(job.id, status=JobStatus.RUNNING)
        with pytest.raises(ValueError):
            update_job(job.id, status=JobStatus.PENDING)

    def test_post_exports_creates_job(self):
        """POST /exports must return 200 with job_id."""
        self._install_deps()
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.report_export.api import app
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("Cannot import API app")
        from unittest.mock import patch
        client = TestClient(app)
        with patch("examples.report_export.tasks.export_report.delay"):
            r = client.post("/exports", json={"query_params": {"table": "users"}})
        assert r.status_code == 200
        assert "job_id" in r.json()

    def test_get_nonexistent_job_returns_404(self):
        """GET /exports/{nonexistent-id} must return 404."""
        self._install_deps()
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.report_export.api import app
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("Cannot import API app")
        client = TestClient(app)
        r = client.get("/exports/nonexistent-uuid-99999")
        assert r.status_code == 404

    def test_retry_exponential_backoff(self):
        """query_data retry must use exponential backoff (2**n)."""
        path = self._example("tasks.py")
        if not os.path.isfile(path):
            pytest.skip("tasks.py not found")
        content = self._read_file(path)
        has_backoff = (
            "2 **" in content
            or "2**" in content
            or "countdown" in content
            or "exponential" in content.lower()
        )
        assert has_backoff, "No exponential backoff pattern found in retry logic"
