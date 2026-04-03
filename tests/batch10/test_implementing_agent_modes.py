"""
Test for 'implementing-agent-modes' skill — PostHog Agent Modes
Validates that the Agent implemented SQL agent mode, feature flag agent mode,
toolkit class, and related components in the PostHog codebase.
"""

import os
import re

import pytest


class TestImplementingAgentModes:
    """Verify PostHog agent modes implementation."""

    REPO_DIR = "/workspace/posthog"

    def test_sql_agent_mode_file_exists(self):
        """SQL agent mode module must exist."""
        candidates = [
            os.path.join(self.REPO_DIR, "ee", "hogai", "sql_agent", "mode.py"),
            os.path.join(self.REPO_DIR, "ee", "hogai", "sql_agent.py"),
        ]
        assert any(os.path.isfile(p) for p in candidates), (
            "SQL agent mode file not found"
        )

    def test_feature_flag_agent_mode_file_exists(self):
        """Feature flag agent mode module must exist."""
        candidates = [
            os.path.join(self.REPO_DIR, "ee", "hogai", "feature_flag_agent", "mode.py"),
            os.path.join(self.REPO_DIR, "ee", "hogai", "feature_flag_agent.py"),
        ]
        assert any(os.path.isfile(p) for p in candidates), (
            "Feature flag agent mode file not found"
        )

    def test_toolkit_class_file_exists(self):
        """Toolkit class must exist for tool registration."""
        candidates = [
            os.path.join(self.REPO_DIR, "ee", "hogai", "toolkit.py"),
            os.path.join(self.REPO_DIR, "ee", "hogai", "tool_registry.py"),
        ]
        found = any(os.path.isfile(p) for p in candidates)
        if not found:
            for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "ee", "hogai")):
                for f in files:
                    if "toolkit" in f.lower() or "tool_registry" in f.lower():
                        found = True
                        break
        assert found, "Toolkit class file not found"

    def test_sql_agent_has_run_sql_method(self):
        """SQL agent mode must have a run_sql or execute_sql method."""
        mode_file = None
        for candidate in [
            os.path.join(self.REPO_DIR, "ee", "hogai", "sql_agent", "mode.py"),
            os.path.join(self.REPO_DIR, "ee", "hogai", "sql_agent.py"),
        ]:
            if os.path.isfile(candidate):
                mode_file = candidate
                break
        assert mode_file is not None, "SQL agent mode file not found"
        with open(mode_file, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"def\s+(run_sql|execute_sql|_run_query)", content), (
            "SQL agent mode missing run_sql/execute_sql method"
        )

    def test_sql_agent_uses_hogql(self):
        """SQL agent must reference HogQL for query execution."""
        mode_file = None
        for candidate in [
            os.path.join(self.REPO_DIR, "ee", "hogai", "sql_agent", "mode.py"),
            os.path.join(self.REPO_DIR, "ee", "hogai", "sql_agent.py"),
        ]:
            if os.path.isfile(candidate):
                mode_file = candidate
                break
        if mode_file is None:
            pytest.skip("SQL agent mode file not found")
        with open(mode_file, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"[Hh]og[Qq][Ll]|hogql", content), (
            "SQL agent mode does not reference HogQL"
        )

    def test_feature_flag_agent_references_feature_flags(self):
        """Feature flag agent must reference feature flag models or APIs."""
        mode_file = None
        for candidate in [
            os.path.join(self.REPO_DIR, "ee", "hogai", "feature_flag_agent", "mode.py"),
            os.path.join(self.REPO_DIR, "ee", "hogai", "feature_flag_agent.py"),
        ]:
            if os.path.isfile(candidate):
                mode_file = candidate
                break
        if mode_file is None:
            pytest.skip("Feature flag agent mode file not found")
        with open(mode_file, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"[Ff]eature[Ff]lag|feature_flag", content), (
            "Feature flag agent does not reference feature flags"
        )

    def test_agent_mode_has_system_prompt(self):
        """At least one agent mode must define a system prompt."""
        hogai_dir = os.path.join(self.REPO_DIR, "ee", "hogai")
        found = False
        for root, dirs, files in os.walk(hogai_dir):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"system_prompt|SYSTEM_PROMPT|SystemMessage", content):
                        found = True
                        break
            if found:
                break
        assert found, "No agent mode defines a system prompt"

    def test_mode_registry_or_dispatcher_exists(self):
        """A mode registry or dispatcher that routes to different agent modes must exist."""
        hogai_dir = os.path.join(self.REPO_DIR, "ee", "hogai")
        found = False
        for root, dirs, files in os.walk(hogai_dir):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"mode_registry|dispatch|get_mode|MODE_MAP", content):
                        found = True
                        break
            if found:
                break
        assert found, "No mode registry/dispatcher found in hogai directory"

    def test_sql_agent_has_validation(self):
        """SQL agent must validate or sanitize SQL queries."""
        mode_file = None
        for candidate in [
            os.path.join(self.REPO_DIR, "ee", "hogai", "sql_agent", "mode.py"),
            os.path.join(self.REPO_DIR, "ee", "hogai", "sql_agent.py"),
        ]:
            if os.path.isfile(candidate):
                mode_file = candidate
                break
        if mode_file is None:
            pytest.skip("SQL agent mode file not found")
        with open(mode_file, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"validat|sanitiz|allow|whitelist|parse", content, re.IGNORECASE), (
            "SQL agent mode has no query validation logic"
        )

    def test_agent_mode_has_tool_definitions(self):
        """At least one agent mode must define or register tools."""
        hogai_dir = os.path.join(self.REPO_DIR, "ee", "hogai")
        found = False
        for root, dirs, files in os.walk(hogai_dir):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"tools\s*=|register_tool|@tool|Tool\(", content):
                        found = True
                        break
            if found:
                break
        assert found, "No tool definitions found in hogai directory"

    def test_agent_mode_tests_exist(self):
        """Test files for agent modes should exist."""
        test_dirs = [
            os.path.join(self.REPO_DIR, "ee", "hogai", "sql_agent", "test"),
            os.path.join(self.REPO_DIR, "ee", "hogai", "tests"),
        ]
        found = False
        for td in test_dirs:
            if os.path.isdir(td):
                found = True
                break
        if not found:
            for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "ee", "hogai")):
                for f in files:
                    if f.startswith("test_") and f.endswith(".py"):
                        found = True
                        break
                if found:
                    break
        assert found, "No test files found for agent modes"
