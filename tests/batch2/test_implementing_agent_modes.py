"""
Test for 'implementing-agent-modes' skill — PostHog Agent Mode Detection
Validates that the Agent modified posthog/api/capture.py to detect agent mode
traffic (payload field or X-Agent-Mode header) and attach agent metadata
(agent_id, agent_session_id, agent_action) while preserving backward compatibility.
"""

import os
import re
import subprocess

import pytest


class TestImplementingAgentModes:
    """Verify PostHog capture endpoint agent-mode implementation."""

    REPO_DIR = "/workspace/posthog"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence & syntax
    # ------------------------------------------------------------------

    def test_capture_py_exists(self):
        """posthog/api/capture.py must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "posthog", "api", "capture.py")
        )

    def test_capture_py_valid_python(self):
        """capture.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python3", "-m", "py_compile", "posthog/api/capture.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: Agent-mode detection
    # ------------------------------------------------------------------

    def test_agent_mode_payload_field(self):
        """capture.py must detect agent_mode from the event payload."""
        content = self._read("posthog", "api", "capture.py")
        assert re.search(
            r"agent.?mode", content, re.IGNORECASE
        ), "No agent_mode payload field detection found"

    def test_agent_mode_header_detection(self):
        """capture.py must detect agent mode via X-Agent-Mode header."""
        content = self._read("posthog", "api", "capture.py")
        patterns = [
            r"X-Agent-Mode",
            r"HTTP_X_AGENT_MODE",
            r"x.agent.mode",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "No X-Agent-Mode header detection found"

    # ------------------------------------------------------------------
    # L2: Agent metadata fields
    # ------------------------------------------------------------------

    def test_agent_id_metadata(self):
        """capture.py must handle agent_id metadata."""
        content = self._read("posthog", "api", "capture.py")
        assert re.search(
            r"agent_id", content
        ), "agent_id metadata not found in capture.py"

    def test_agent_session_id_metadata(self):
        """capture.py must handle agent_session_id metadata."""
        content = self._read("posthog", "api", "capture.py")
        assert re.search(
            r"agent_session_id", content
        ), "agent_session_id metadata not found in capture.py"

    def test_agent_action_metadata(self):
        """capture.py must handle agent_action metadata."""
        content = self._read("posthog", "api", "capture.py")
        assert re.search(
            r"agent_action", content
        ), "agent_action metadata not found in capture.py"

    # ------------------------------------------------------------------
    # L2: Backward compatibility
    # ------------------------------------------------------------------

    def test_get_distinct_id_preserved(self):
        """Existing get_distinct_id logic or similar helper must remain."""
        content = self._read("posthog", "api", "capture.py")
        patterns = [
            r"get_distinct_id",
            r"distinct_id",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Core distinct_id handling appears to have been removed"

    def test_capture_endpoint_preserved(self):
        """The core capture/batch endpoint logic must still exist."""
        content = self._read("posthog", "api", "capture.py")
        patterns = [
            r"def\s+get_event",
            r"def\s+capture",
            r"def\s+post",
            r"def\s+get_data",
            r"def\s+_handle",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Core capture endpoint handler not found"

    def test_original_imports_intact(self):
        """capture.py should keep its original imports."""
        content = self._read("posthog", "api", "capture.py")
        # At least one Django-related import should remain
        assert re.search(
            r"(from django|import django|from rest_framework)", content
        ), "Original Django/DRF imports appear removed"

    # ------------------------------------------------------------------
    # L2: Integration quality
    # ------------------------------------------------------------------

    def test_agent_metadata_attached_to_event(self):
        """Agent metadata should be attached to event properties or set-properties."""
        content = self._read("posthog", "api", "capture.py")
        # Look for property assignment patterns
        patterns = [
            r"\$set",
            r"properties\[.*agent",
            r"agent.*properties",
            r"metadata.*agent",
            r"event.*agent",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Agent metadata not attached to event data"

    def test_no_hardcoded_agent_ids(self):
        """capture.py should not contain hardcoded agent IDs."""
        content = self._read("posthog", "api", "capture.py")
        # Should not have UUIDs or obviously hardcoded IDs
        hardcoded = re.findall(r'agent_id\s*=\s*["\'][0-9a-f]{8,}["\']', content)
        assert len(hardcoded) == 0, f"Hardcoded agent IDs found: {hardcoded}"

    def test_conditional_agent_mode(self):
        """Agent mode should be conditional, not always applied."""
        content = self._read("posthog", "api", "capture.py")
        # Should have conditionals around agent mode
        assert re.search(
            r"if.*agent.?mode|agent.?mode.*if|is_agent", content, re.IGNORECASE
        ), "Agent mode detection should be conditional"
