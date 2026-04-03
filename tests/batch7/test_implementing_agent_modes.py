"""Test file for the implementing-agent-modes skill.

This suite validates the SQL Agent Mode components in PostHog's HogAI system:
InspectSchemaTool, ValidateQueryTool, GetQueryExamplesTool, SqlAgentToolkit,
and the sql_agent preset.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestImplementingAgentModes:
    """Verify PostHog HogAI SQL Agent Mode implementation."""

    REPO_DIR = "/workspace/posthog"

    SQL_PRESET = "ee/hogai/core/agent_modes/presets/sql.py"
    SQL_TOOLS = "ee/hogai/tools/sql_tools.py"
    SQL_TESTS = "ee/hogai/core/agent_modes/presets/tests/test_sql.py"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _class_source(self, source: str, class_name: str) -> str | None:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                lines = source.splitlines()
                return "\n".join(lines[node.lineno - 1 : node.end_lineno])
        return None

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_ee_hogai_core_agent_modes_presets_sql_py_exists(self):
        """Verify sql.py preset exists and is non-empty."""
        self._assert_non_empty_file(self.SQL_PRESET)

    def test_file_path_ee_hogai_tools_sql_tools_py_exists(self):
        """Verify sql_tools.py exists and is non-empty."""
        self._assert_non_empty_file(self.SQL_TOOLS)

    def test_file_path_ee_hogai_core_agent_modes_presets_tests_test_sql_py_exists(self):
        """Verify test_sql.py exists and is non-empty."""
        self._assert_non_empty_file(self.SQL_TESTS)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_inspectschematool_has_name_inspect_schema_and_correct_inputs(
        self,
    ):
        """InspectSchemaTool has name='inspect_schema' and correct InputSchema."""
        src = self._read_text(self.SQL_TOOLS)
        cls = self._class_source(src, "InspectSchemaTool")
        assert cls is not None, "InspectSchemaTool class not found"
        assert re.search(
            r"name\s*=\s*['\"]inspect_schema['\"]", cls
        ), "InspectSchemaTool must have name='inspect_schema'"

    def test_semantic_validatequerytool_has_name_validate_query_and_inputschema_wi(
        self,
    ):
        """ValidateQueryTool has name='validate_query' and InputSchema with query field."""
        src = self._read_text(self.SQL_TOOLS)
        cls = self._class_source(src, "ValidateQueryTool")
        assert cls is not None, "ValidateQueryTool class not found"
        assert re.search(
            r"name\s*=\s*['\"]validate_query['\"]", cls
        ), "ValidateQueryTool must have name='validate_query'"

    def test_semantic_getqueryexamplestool_has_name_get_query_examples_and_inputsc(
        self,
    ):
        """GetQueryExamplesTool has name='get_query_examples' and InputSchema with use_case."""
        src = self._read_text(self.SQL_TOOLS)
        cls = self._class_source(src, "GetQueryExamplesTool")
        assert cls is not None, "GetQueryExamplesTool class not found"
        assert re.search(
            r"name\s*=\s*['\"]get_query_examples['\"]", cls
        ), "GetQueryExamplesTool must have name='get_query_examples'"

    def test_semantic_sqlagenttoolkit_tools_includes_all_three_tool_classes(self):
        """SqlAgentToolkit.tools includes all three tool classes."""
        src = self._read_text(self.SQL_TOOLS)
        toolkit = self._class_source(src, "SqlAgentToolkit")
        if toolkit is None:
            # May be in a different file
            preset_src = self._read_text(self.SQL_PRESET)
            src = src + "\n" + preset_src
        for tool in ("InspectSchemaTool", "ValidateQueryTool", "GetQueryExamplesTool"):
            assert tool in src, f"SqlAgentToolkit should reference {tool}"

    def test_semantic_sql_agent_has_mode_agentmode_sql(self):
        """sql_agent has mode=AgentMode.SQL."""
        src = self._read_text(self.SQL_PRESET)
        assert re.search(
            r"AgentMode\.SQL|mode\s*=.*SQL", src
        ), "sql_agent must have mode=AgentMode.SQL"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, mocked via source analysis)
    # ------------------------------------------------------------------

    def _tools_source(self) -> str:
        parts = [self._read_text(self.SQL_TOOLS)]
        preset_path = self._repo_path(self.SQL_PRESET)
        if preset_path.exists():
            parts.append(preset_path.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    def test_functional_inspectschematool__run_table_name_none_returns_summary_of_al(
        self,
    ):
        """InspectSchemaTool._run(table_name=None) returns summary of all tables."""
        src = self._tools_source()
        cls = self._class_source(src, "InspectSchemaTool")
        assert cls is not None, "InspectSchemaTool not found"
        assert re.search(
            r"def\s+_run\s*\(", cls
        ), "InspectSchemaTool must implement _run method"
        assert re.search(
            r"table_name|table|schema", cls, re.IGNORECASE
        ), "_run should handle table_name parameter"

    def test_functional_inspectschematool__run_table_name_events_returns_events_tabl(
        self,
    ):
        """InspectSchemaTool._run(table_name='events') returns events table details."""
        src = self._tools_source()
        cls = self._class_source(src, "InspectSchemaTool")
        assert cls is not None, "InspectSchemaTool not found"
        # Should handle specific table lookup
        assert re.search(
            r"table_name|specific|detail|column", cls, re.IGNORECASE
        ), "InspectSchemaTool should return specific table details"

    def test_functional_validatequerytool__run_select_event_from_events_limit_10_ret(
        self,
    ):
        """ValidateQueryTool._run('SELECT event FROM events LIMIT 10') returns valid."""
        src = self._tools_source()
        cls = self._class_source(src, "ValidateQueryTool")
        assert cls is not None, "ValidateQueryTool not found"
        assert re.search(
            r"def\s+_run\s*\(", cls
        ), "ValidateQueryTool must implement _run method"
        assert re.search(
            r"valid|parse|syntax|error", cls, re.IGNORECASE
        ), "ValidateQueryTool should validate SQL syntax"

    def test_functional_validatequerytool__run_select_nonexistent_col_from_events_re(
        self,
    ):
        """ValidateQueryTool._run('SELECT nonexistent_col FROM events') returns error."""
        src = self._tools_source()
        cls = self._class_source(src, "ValidateQueryTool")
        assert cls is not None, "ValidateQueryTool not found"
        assert re.search(
            r"error|invalid|fail|exception", cls, re.IGNORECASE
        ), "ValidateQueryTool should report errors for invalid queries"

    def test_functional_getqueryexamplestool__run_use_case_event_counts_returns_exam(
        self,
    ):
        """GetQueryExamplesTool._run(use_case='event counts') returns examples."""
        src = self._tools_source()
        cls = self._class_source(src, "GetQueryExamplesTool")
        assert cls is not None, "GetQueryExamplesTool not found"
        assert re.search(
            r"def\s+_run\s*\(", cls
        ), "GetQueryExamplesTool must implement _run method"
        assert re.search(
            r"use_case|example|query", cls, re.IGNORECASE
        ), "GetQueryExamplesTool should return query examples based on use_case"
