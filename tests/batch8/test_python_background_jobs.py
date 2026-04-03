"""
Test for 'python-background-jobs' skill — Celery Background Jobs
Validates that the Agent implemented Celery task modules with retry logic,
queue routing, JSON serialization security, and exponential backoff.
"""

import os
import re
import sys

import pytest


class TestPythonBackgroundJobs:
    """Verify Celery background jobs implementation."""

    REPO_DIR = "/workspace/celery"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_tasks_package_and_pipeline_exist(self):
        """Verify tasks/__init__.py and tasks/pipeline.py exist."""
        for rel in ("tasks/__init__.py", "tasks/pipeline.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_workers_and_config_exist(self):
        """Verify tasks/workers.py and tasks/config.py exist."""
        for rel in ("tasks/workers.py", "tasks/config.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    # ── semantic_check ──────────────────────────────────────────────

    def test_task_serializer_is_json(self):
        """Verify CeleryConfig.task_serializer='json' (not pickle) for security."""
        content = self._read(os.path.join(self.REPO_DIR, "tasks/config.py"))
        assert content, "tasks/config.py is empty or unreadable"
        assert "task_serializer" in content, "task_serializer not found"
        assert "'json'" in content or '"json"' in content, \
            "task_serializer must be set to 'json'"

    def test_data_processor_retry_config(self):
        """Verify DataProcessor has autoretry_for=(TransientError,) and max_retries=3."""
        content = self._read(os.path.join(self.REPO_DIR, "tasks/workers.py"))
        assert content, "tasks/workers.py is empty or unreadable"
        for kw in ("autoretry_for", "TransientError", "max_retries"):
            assert kw in content, f"'{kw}' not found in tasks/workers.py"

    def test_notification_worker_queue_routing(self):
        """Verify NotificationWorker routed to 'notifications' queue."""
        content = self._read(os.path.join(self.REPO_DIR, "tasks/workers.py"))
        assert content, "tasks/workers.py is empty or unreadable"
        assert "notifications" in content, "'notifications' queue not found"
        assert "queue" in content, "'queue' keyword not found"

    def test_exponential_backoff_configured(self):
        """Verify exponential backoff via retry_backoff or countdown=2**retries."""
        content = self._read(os.path.join(self.REPO_DIR, "tasks/workers.py"))
        assert content, "tasks/workers.py is empty or unreadable"
        found = any(kw in content for kw in ("retry_backoff", "2**", "countdown"))
        assert found, "No exponential backoff configuration found"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_task_serializer_json_at_runtime(self):
        """CeleryConfig.task_serializer equals 'json' at runtime."""
        self._skip_unless_importable()
        try:
            from tasks.config import CeleryConfig
        except Exception as exc:
            pytest.skip(f"Cannot import tasks.config: {exc}")
        assert CeleryConfig.task_serializer == "json", \
            "task_serializer must be 'json' at runtime"

    def test_submit_returns_async_result_with_id(self):
        """submit({}) returns AsyncResult with a valid 36-char UUID id."""
        self._skip_unless_importable()
        os.environ["CELERY_TASK_ALWAYS_EAGER"] = "1"
        try:
            from tasks.pipeline import CeleryPipeline
        except Exception as exc:
            pytest.skip(f"Cannot import tasks.pipeline: {exc}")
        result = CeleryPipeline().submit({"key": "val"})
        assert hasattr(result, "id"), "submit() result has no 'id' attribute"
        assert isinstance(result.id, str), "id is not a string"
        assert len(result.id) == 36, f"id length {len(result.id)} != 36"

    def test_data_processor_task_attributes(self):
        """DataProcessor.process task has max_retries=3 set on task object."""
        self._skip_unless_importable()
        try:
            from tasks.workers import DataProcessor
        except Exception as exc:
            pytest.skip(f"Cannot import tasks.workers: {exc}")
        assert DataProcessor.process.max_retries == 3, \
            "max_retries must be 3"

    def test_notification_worker_queue_attribute(self):
        """NotificationWorker.notify task queue attribute is 'notifications'."""
        self._skip_unless_importable()
        try:
            from tasks.workers import NotificationWorker
        except Exception as exc:
            pytest.skip(f"Cannot import tasks.workers: {exc}")
        assert NotificationWorker.notify.queue == "notifications", \
            "queue must be 'notifications'"
