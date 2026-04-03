"""
Test for 'python-background-jobs' skill — Celery background jobs
Validates that the Agent implemented Celery background job patterns
in the celery project.
"""

import os
import re

import pytest


class TestPythonBackgroundJobs:
    """Verify Celery background job implementation."""

    REPO_DIR = "/workspace/celery"

    def test_celery_app_defined(self):
        """Celery app instance must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"Celery\(|app\s*=\s*Celery", content):
                        found = True
                        break
            if found:
                break
        assert found, "Celery app not defined"

    def test_task_decorator_used(self):
        """At least one @task or @shared_task decorator must be used."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"@.*task|@shared_task|@app\.task", content):
                        found = True
                        break
            if found:
                break
        assert found, "No @task decorator found"

    def test_broker_configured(self):
        """A message broker must be configured (Redis, RabbitMQ, etc)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"broker|BROKER_URL|broker_url|redis://|amqp://", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No broker configured"

    def test_result_backend_configured(self):
        """Result backend should be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"result_backend|CELERY_RESULT_BACKEND|backend", content):
                        found = True
                        break
            if found:
                break
        assert found, "No result backend configured"

    def test_task_retry_configuration(self):
        """Tasks should have retry configuration."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"max_retries|retry|autoretry|retry_backoff", content):
                        found = True
                        break
            if found:
                break
        assert found, "No task retry configuration found"

    def test_task_serializer_or_accept(self):
        """Task serializer or accepted content types should be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"task_serializer|accept_content|CELERY_TASK_SERIALIZER|serializer", content):
                        found = True
                        break
            if found:
                break
        assert found, "No task serializer configured"

    def test_periodic_task_or_beat(self):
        """Periodic tasks or Celery beat configuration should exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"beat_schedule|periodic_task|crontab|schedule", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No periodic task or beat configuration found"

    def test_task_chaining_or_group(self):
        """Task chaining, grouping, or chord patterns should be used."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"chain\(|group\(|chord\(|canvas|signature|\.s\(|\.si\(", content):
                        found = True
                        break
            if found:
                break
        assert found, "No task chaining or grouping found"

    def test_error_handling_in_tasks(self):
        """Tasks must have error handling."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"@.*task|@shared_task", content):
                        if re.search(r"try:|except|raise|on_failure|on_retry", content):
                            found = True
                            break
            if found:
                break
        assert found, "No error handling in tasks"

    def test_celery_import(self):
        """Code must import from celery."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"from\s+celery|import\s+celery", content):
                        found = True
                        break
            if found:
                break
        assert found, "No celery import found"
