"""
Test for 'python-background-jobs' skill — Video Transcoding Task System
Validates that the Agent implemented Celery tasks (extract_audio, transcode_video,
generate_thumbnail) and a chain workflow in the celery repository.
"""

import os
import ast
import subprocess
import pytest


class TestPythonBackgroundJobs:
    """Verify Celery transcoding task implementation."""

    REPO_DIR = "/workspace/celery"

    # ------------------------------------------------------------------
    # L1: file & syntax
    # ------------------------------------------------------------------

    def test_tasks_file_exists(self):
        """examples/transcoding/tasks.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "transcoding", "tasks.py")
        assert os.path.isfile(fpath), "tasks.py not found"

    def test_workflow_file_exists(self):
        """examples/transcoding/workflow.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "transcoding", "workflow.py")
        assert os.path.isfile(fpath), "workflow.py not found"

    def test_tasks_compiles(self):
        """tasks.py must compile without syntax errors."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/transcoding/tasks.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_workflow_compiles(self):
        """workflow.py must compile without syntax errors."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/transcoding/workflow.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: structural verification
    # ------------------------------------------------------------------

    def _parse_tasks(self):
        fpath = os.path.join(self.REPO_DIR, "examples", "transcoding", "tasks.py")
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read(), ast.parse(f.read())

    def _read_tasks_source(self):
        fpath = os.path.join(self.REPO_DIR, "examples", "transcoding", "tasks.py")
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def _read_workflow_source(self):
        fpath = os.path.join(self.REPO_DIR, "examples", "transcoding", "workflow.py")
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def test_extract_audio_task_defined(self):
        """extract_audio task must be defined in tasks.py."""
        source = self._read_tasks_source()
        assert "extract_audio" in source, "extract_audio task not found"

    def test_transcode_video_task_defined(self):
        """transcode_video task must be defined in tasks.py."""
        source = self._read_tasks_source()
        assert "transcode_video" in source, "transcode_video task not found"

    def test_generate_thumbnail_task_defined(self):
        """generate_thumbnail task must be defined in tasks.py."""
        source = self._read_tasks_source()
        assert "generate_thumbnail" in source, "generate_thumbnail task not found"

    def test_bind_true_on_tasks(self):
        """Tasks should use bind=True for self access."""
        source = self._read_tasks_source()
        assert (
            "bind" in source and "True" in source
        ), "bind=True not found — tasks should have self access"

    def test_update_state_used(self):
        """Tasks should call self.update_state for progress reporting."""
        source = self._read_tasks_source()
        assert "update_state" in source, "update_state not found in tasks.py"

    def test_retry_configured(self):
        """transcode_video should implement retry logic."""
        source = self._read_tasks_source()
        assert "retry" in source.lower(), "No retry logic found in tasks.py"

    def test_max_retries_set(self):
        """Max retries should be configured (3)."""
        source = self._read_tasks_source()
        assert (
            "max_retries" in source or "3" in source
        ), "max_retries configuration not found"

    def test_chain_in_workflow(self):
        """workflow.py should use chain() to compose tasks."""
        source = self._read_workflow_source()
        assert "chain" in source, "chain() not found in workflow.py"

    def test_signatures_in_workflow(self):
        """workflow.py should use .s() or .si() signatures."""
        source = self._read_workflow_source()
        assert (
            ".s(" in source or ".si(" in source
        ), "Celery signatures (.s() or .si()) not found in workflow.py"
