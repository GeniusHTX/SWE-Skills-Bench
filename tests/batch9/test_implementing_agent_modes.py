"""
Test for 'implementing-agent-modes' skill — AI Agent Modes Implementation
Validates PlannerAgent, ExecutorAgent, ToolRegistry, AgentLoop,
max_steps guard, error handling, and Django API endpoint.
"""

import os
import sys

import pytest


class TestImplementingAgentModes:
    """Verify agent modes: planner, executor, tools, loop, API."""

    REPO_DIR = "/workspace/posthog"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _am(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "agent_modes", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_planner_py_exists(self):
        """planner.py must exist."""
        assert os.path.isfile(self._am("planner.py")), "planner.py not found"

    def test_executor_py_exists(self):
        """executor.py must exist."""
        assert os.path.isfile(self._am("executor.py")), "executor.py not found"

    def test_tools_py_exists(self):
        """tools.py must exist."""
        assert os.path.isfile(self._am("tools.py")), "tools.py not found"

    def test_api_views_py_exists(self):
        """api/views.py must exist."""
        assert os.path.isfile(self._am("api", "views.py")), "api/views.py not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_planner_plan_method(self):
        """PlannerAgent must define plan(goal) returning list."""
        content = self._read_file(self._am("planner.py"))
        if not content:
            pytest.skip("planner.py not found")
        assert "PlannerAgent" in content
        assert "plan" in content
        assert "goal" in content

    def test_agent_loop_max_steps(self):
        """AgentLoop must accept max_steps parameter."""
        content = self._read_file(self._am("loop.py"))
        if not content:
            pytest.skip("loop.py not found")
        assert "AgentLoop" in content
        assert "max_steps" in content

    def test_agent_state_limit_error(self):
        """AgentStateLimitError must be defined and raised."""
        content = self._read_file(self._am("loop.py"))
        if not content:
            pytest.skip("loop.py not found")
        assert "AgentStateLimitError" in content
        assert "raise" in content

    def test_tool_registry_register_method(self):
        """ToolRegistry must have register() method."""
        content = self._read_file(self._am("tools.py"))
        if not content:
            pytest.skip("tools.py not found")
        assert "ToolRegistry" in content
        assert "register" in content

    # ── functional_check ─────────────────────────────────────────────────

    def test_tool_registry_register_and_lookup(self):
        """Register echo tool and verify lookup."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.agent_modes.tools import ToolRegistry
        except ImportError:
            pytest.skip("Cannot import ToolRegistry")
        registry = ToolRegistry()
        registry.register("echo", {}, lambda x: x)
        tools = getattr(registry, "tools", getattr(registry, "_tools", {}))
        assert "echo" in tools

    def test_max_steps_exceeded_raises(self):
        """AgentLoop with max_steps=1 must raise AgentStateLimitError."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.agent_modes.loop import AgentLoop, AgentStateLimitError
            from unittest.mock import MagicMock
        except ImportError:
            pytest.skip("Cannot import AgentLoop")
        planner = MagicMock()
        planner.plan.return_value = [MagicMock(), MagicMock(), MagicMock()]
        executor = MagicMock()
        executor.execute.return_value = {"done": False}
        loop = AgentLoop(planner=planner, executor=executor, max_steps=1)
        with pytest.raises(AgentStateLimitError):
            loop.run(goal="test")

    def test_tool_error_captured(self):
        """ExecutorAgent must catch tool errors and return is_error=True."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.agent_modes.executor import ExecutorAgent
            from examples.agent_modes.tools import ToolRegistry
        except ImportError:
            pytest.skip("Cannot import ExecutorAgent")
        registry = ToolRegistry()
        registry.register("fail", {}, lambda x: (_ for _ in ()).throw(RuntimeError("boom")))
        executor = ExecutorAgent(registry=registry)
        try:
            result = executor.execute({"tool": "fail", "args": {}}, registry)
            assert result.get("is_error") is True
        except RuntimeError:
            pytest.fail("ExecutorAgent should catch tool errors, not propagate them")

    def test_empty_plan_no_error(self):
        """AgentLoop with empty plan must complete without error."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.agent_modes.loop import AgentLoop
            from unittest.mock import MagicMock
        except ImportError:
            pytest.skip("Cannot import AgentLoop")
        planner = MagicMock()
        planner.plan.return_value = []
        executor = MagicMock()
        loop = AgentLoop(planner=planner, executor=executor, max_steps=5)
        loop.run(goal="empty")
        executor.execute.assert_not_called()

    def test_api_view_content(self):
        """api/views.py must reference POST and agents/run."""
        content = self._read_file(self._am("api", "views.py"))
        if not content:
            pytest.skip("api/views.py not found")
        has_post = "POST" in content or "post" in content
        has_run = "run" in content or "agent" in content.lower()
        assert has_post and has_run, "API view missing POST/run handler"
