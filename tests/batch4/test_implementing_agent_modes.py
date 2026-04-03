"""
Test for 'implementing-agent-modes' skill — Implementing Agent Modes
Validates agent Python files in the PostHog repo for tool registration,
agent loop functions, max iterations, step records, and agent types.
"""

import os
import re
import ast
import glob
import pytest


class TestImplementingAgentModes:
    """Tests for agent mode implementations in the posthog repo."""

    REPO_DIR = "/workspace/posthog"

    def _find_agent_files(self):
        """Find all agent-related Python files."""
        files = glob.glob(
            os.path.join(self.REPO_DIR, "**/agents/**/*.py"), recursive=True
        ) + glob.glob(os.path.join(self.REPO_DIR, "**/*agent*.py"), recursive=True)
        return list(set(files))

    def _read_agent_text(self):
        """Read and concatenate all agent files."""
        files = self._find_agent_files()
        return "\n".join(open(f, errors="ignore").read() for f in files)

    def _get_func_defs(self):
        """Get all function names from agent files via AST."""
        func_defs = []
        for f in self._find_agent_files():
            try:
                tree = ast.parse(open(f, errors="ignore").read())
                for n in ast.walk(tree):
                    if isinstance(n, ast.FunctionDef):
                        func_defs.append(n.name)
            except SyntaxError:
                continue
        return func_defs

    # --- File Path Checks ---

    def test_agents_py_exists(self):
        """Verifies that agent Python files exist under agents/ directory."""
        files = glob.glob(
            os.path.join(self.REPO_DIR, "**/agents/**/*.py"), recursive=True
        )
        assert len(files) > 0, "No Python files found under agents/"

    def test_agent_modes_py_exists(self):
        """Verifies that agent_modes*.py file exists."""
        files = glob.glob(
            os.path.join(self.REPO_DIR, "**/*agent_modes*.py"), recursive=True
        ) + glob.glob(os.path.join(self.REPO_DIR, "**/*agent*.py"), recursive=True)
        assert len(files) > 0, "No agent_modes*.py or *agent*.py files found"

    def test_py_exists(self):
        """Verifies that .py files exist in the repo."""
        files = glob.glob(os.path.join(self.REPO_DIR, "**/*.py"), recursive=True)
        assert len(files) > 0, "No Python files found"

    # --- Semantic Checks ---

    def test_sem_agent_files_found(self):
        """Agent files can be collected and read."""
        files = self._find_agent_files()
        assert len(files) > 0, "No agent files found"

    def test_sem_agent_text_readable(self):
        """Agent code text can be concatenated."""
        agent_text = self._read_agent_text()
        assert len(agent_text) > 0, "Agent text is empty"

    def test_sem_has_register_tool(self):
        """Agent code has 'register_tool' or 'tool_registry'."""
        agent_text = self._read_agent_text()
        assert (
            "register_tool" in agent_text or "tool_registry" in agent_text
        ), "No tool registration pattern found"

    def test_sem_has_max_iterations(self):
        """Agent code references 'max_iterations' or 'MAX_ITERATIONS'."""
        agent_text = self._read_agent_text()
        assert (
            "max_iterations" in agent_text or "MAX_ITERATIONS" in agent_text
        ), "No max_iterations pattern found"

    def test_sem_has_step_record(self):
        """Agent code has StepRecord, AgentResult, or steps tracking."""
        agent_text = self._read_agent_text()
        assert (
            "StepRecord" in agent_text
            or "AgentResult" in agent_text
            or "steps" in agent_text
        ), "No step record / result tracking found"

    # --- Functional Checks ---

    def test_func_ast_parse_agent_files(self):
        """Agent files can be parsed by AST."""
        func_defs = self._get_func_defs()
        assert len(func_defs) > 0, "No functions found in agent files"

    def test_func_has_register_function(self):
        """Agent code defines 'register_tool' or 'register' function."""
        func_defs = self._get_func_defs()
        assert (
            "register_tool" in func_defs or "register" in func_defs
        ), "No register_tool or register function found"

    def test_func_has_run_function(self):
        """Agent code defines 'run' function."""
        func_defs = self._get_func_defs()
        assert "run" in func_defs, "No 'run' function found"

    def test_func_has_available_tools_or_get_tools(self):
        """Agent code defines 'available_tools' or 'get_tools' function."""
        func_defs = self._get_func_defs()
        assert (
            "available_tools" in func_defs or "get_tools" in func_defs
        ), "No available_tools or get_tools function found"

    def test_func_max_iterations_error_handling(self):
        """Agent code handles MaxIterationsError or max_iterations."""
        agent_text = self._read_agent_text()
        assert (
            "MaxIterationsError" in agent_text or "max_iterations" in agent_text
        ), "No max iterations error handling"

    def test_func_thought_pattern(self):
        """Agent code has Thought or thought pattern."""
        agent_text = self._read_agent_text()
        assert (
            "Thought" in agent_text or "thought" in agent_text
        ), "No thought pattern found"

    def test_func_observation_pattern(self):
        """Agent code has observation or Observation pattern."""
        agent_text = self._read_agent_text()
        assert (
            "observation" in agent_text or "Observation" in agent_text
        ), "No observation pattern found"

    def test_func_specific_agent_type(self):
        """Agent code has InsightAgent or DataQueryAgent."""
        agent_text = self._read_agent_text()
        assert (
            "InsightAgent" in agent_text or "DataQueryAgent" in agent_text
        ), "No InsightAgent or DataQueryAgent found"
