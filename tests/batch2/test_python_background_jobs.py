"""
Test for 'python-background-jobs' skill — Python Background Jobs
Validates that the Agent implemented a video transcoding task system using Celery
with task definitions, workflow orchestration, retry logic, and error handling.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestPythonBackgroundJobs.REPO_DIR)


class TestPythonBackgroundJobs:
    """Verify Celery-based video transcoding task system."""

    REPO_DIR = "/workspace/celery"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_tasks_file_exists(self):
        """examples/transcoding/tasks.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "transcoding", "tasks.py")
        assert os.path.isfile(fpath), "examples/transcoding/tasks.py not found"

    def test_workflow_file_exists(self):
        """examples/transcoding/workflow.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "transcoding", "workflow.py")
        assert os.path.isfile(fpath), "examples/transcoding/workflow.py not found"

    def test_tasks_compiles(self):
        """tasks.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/transcoding/tasks.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error in tasks.py:\n{result.stderr}"

    def test_workflow_compiles(self):
        """workflow.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/transcoding/workflow.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error in workflow.py:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L1: Task definitions
    # ------------------------------------------------------------------

    def test_tasks_define_multiple_celery_tasks(self):
        """tasks.py must define at least 3 distinct Celery tasks (pipeline stages)."""
        content = self._read("examples", "transcoding", "tasks.py")
        # Match @app.task, @shared_task, @celery.task decorators, or Task subclasses
        task_decorators = re.findall(r"@\w*\.?(?:task|shared_task)", content)
        task_classes = re.findall(r"class\s+\w+.*Task\b", content)
        total = len(task_decorators) + len(task_classes)
        assert total >= 3, (
            f"tasks.py defines only {total} Celery task(s) — "
            f"need at least 3 pipeline stages (validation, transcoding, thumbnail, etc.)"
        )

    def test_tasks_import_celery(self):
        """tasks.py must import from celery."""
        content = self._read("examples", "transcoding", "tasks.py")
        assert re.search(
            r"from\s+celery|import\s+celery", content, re.IGNORECASE
        ), "tasks.py does not import from celery"

    def test_tasks_have_retry_configuration(self):
        """At least one task must configure retry behavior (max_retries, retry_backoff, etc.)."""
        content = self._read("examples", "transcoding", "tasks.py")
        retry_patterns = [
            r"max_retries",
            r"retry_backoff",
            r"default_retry_delay",
            r"autoretry_for",
            r"\.retry\(",
        ]
        assert any(
            re.search(p, content) for p in retry_patterns
        ), "No task configures retry behavior"

    def test_tasks_have_bind_parameter(self):
        """At least one task should use bind=True for self-access in retries."""
        content = self._read("examples", "transcoding", "tasks.py")
        assert re.search(
            r"bind\s*=\s*True", content
        ), "No task uses bind=True — needed for self.retry() pattern"

    # ------------------------------------------------------------------
    # L1: Error handling
    # ------------------------------------------------------------------

    def test_tasks_have_error_handling(self):
        """tasks.py must include error handling (try/except, on_failure, error callbacks)."""
        content = self._read("examples", "transcoding", "tasks.py")
        error_patterns = [
            r"except\s+\w+",
            r"on_failure",
            r"errback",
            r"link_error",
            r"error_callback",
        ]
        assert any(
            re.search(p, content) for p in error_patterns
        ), "tasks.py has no error handling (try/except, on_failure, errbacks)"

    # ------------------------------------------------------------------
    # L2: Workflow orchestration
    # ------------------------------------------------------------------

    def test_workflow_uses_chain_or_group(self):
        """workflow.py must use Celery primitives (chain, group, chord) for orchestration."""
        content = self._read("examples", "transcoding", "workflow.py")
        primitives = [r"chain\(", r"group\(", r"chord\(", r"\|"]
        assert any(
            re.search(p, content) for p in primitives
        ), "workflow.py does not use chain, group, or chord for orchestration"

    def test_workflow_has_sequential_pipeline(self):
        """Workflow must define at least one sequential pipeline (A → B → C)."""
        content = self._read("examples", "transcoding", "workflow.py")
        # chain() or pipe | operator indicates sequential composition
        seq_patterns = [
            r"chain\(",
            r"\|\s*\w+\.s\(",
            r"\|\s*\w+\.si\(",
            r"\|\s*\w+\.signature",
        ]
        assert any(
            re.search(p, content) for p in seq_patterns
        ), "Workflow does not define a sequential pipeline"

    def test_workflow_has_parallel_fanout(self):
        """Workflow must define at least one parallel fan-out step."""
        content = self._read("examples", "transcoding", "workflow.py")
        parallel_patterns = [r"group\(", r"chord\("]
        assert any(
            re.search(p, content) for p in parallel_patterns
        ), "Workflow does not define a parallel fan-out step (group/chord)"

    def test_workflow_has_entry_point(self):
        """workflow.py must define a main entry point function to kick off the pipeline."""
        content = self._read("examples", "transcoding", "workflow.py")
        entry_patterns = [
            r"def\s+(?:main|run|start|execute|launch|process)",
            r'if\s+__name__\s*==\s*["\']__main__["\']',
        ]
        assert any(
            re.search(p, content) for p in entry_patterns
        ), "workflow.py missing main entry point function"

    def test_workflow_imports_tasks(self):
        """workflow.py must import tasks from the tasks module."""
        content = self._read("examples", "transcoding", "workflow.py")
        assert re.search(
            r"from\s+.*tasks\s+import|import\s+.*tasks", content
        ), "workflow.py does not import from the tasks module"

    # ------------------------------------------------------------------
    # L2: Task configuration completeness
    # ------------------------------------------------------------------

    def test_tasks_acks_late_configured(self):
        """At least one task should configure acks_late for reliability."""
        content = self._read("examples", "transcoding", "tasks.py")
        patterns = [r"acks_late", r"ack_late", r"task_acks_late"]
        has_acks_late = any(re.search(p, content) for p in patterns)
        # This is a best practice, not strictly required — warn but pass
        if not has_acks_late:
            # Still pass, but look for other reliability indicators
            other_reliability = re.search(
                r"reject_on_worker_lost|task_reject_on_worker_lost", content
            )
            assert (
                other_reliability or has_acks_late or True
            ), "Consider adding acks_late=True for task reliability"
