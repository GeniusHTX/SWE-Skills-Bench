"""
Tests for implementing-agent-modes skill.
Validates AgentModeDefinition, Toolkit, and Trajectory classes in posthog repository.
"""

import os
import sys
import importlib
import pytest

REPO_DIR = "/workspace/posthog"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _try_import(module_path: str):
    if REPO_DIR not in sys.path:
        sys.path.insert(0, REPO_DIR)
    try:
        parts = module_path.rsplit(".", 1)
        mod = importlib.import_module(parts[0])
        return getattr(mod, parts[1]) if len(parts) > 1 else mod
    except (ImportError, AttributeError) as exc:
        pytest.skip(f"Module not importable: {exc}")


class TestImplementingAgentModes:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_mode_definition_file_exists(self):
        """posthog/agent/mode_definition.py must exist and be non-empty."""
        rel = "posthog/agent/mode_definition.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "mode_definition.py is empty"

    def test_toolkit_and_trajectory_files_exist(self):
        """toolkit.py and trajectory.py must exist in posthog/agent."""
        for rel in ["posthog/agent/toolkit.py", "posthog/agent/trajectory.py"]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_agent_mode_definition_class_defined(self):
        """mode_definition.py must define AgentModeDefinition with name and max_iterations."""
        content = _read("posthog/agent/mode_definition.py")
        assert (
            "class AgentModeDefinition" in content
        ), "AgentModeDefinition class not found"
        assert (
            "max_iterations" in content
        ), "max_iterations field not found in AgentModeDefinition"

    def test_toolkit_defines_exception_types(self):
        """toolkit.py must define all four exception classes."""
        content = _read("posthog/agent/toolkit.py")
        for exc in [
            "ToolNotAllowedError",
            "ConfirmationRequired",
            "IterationLimitExceeded",
            "MutationNotAllowedError",
        ]:
            assert (
                f"class {exc}" in content
            ), f"{exc} exception class not found in toolkit.py"

    def test_trajectory_defines_success_rate(self):
        """trajectory.py must define Trajectory class with success_rate."""
        content = _read("posthog/agent/trajectory.py")
        assert "class Trajectory" in content, "Trajectory class not found"
        assert (
            "success_rate" in content
        ), "success_rate property/method not found in Trajectory"

    def test_mode_definition_has_to_dict_from_dict(self):
        """mode_definition.py must define to_dict and from_dict methods."""
        content = _read("posthog/agent/mode_definition.py")
        assert "def to_dict" in content, "to_dict method not found"
        assert "def from_dict" in content, "from_dict method not found"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_agent_mode_name_alphanumeric_underscore_valid(self):
        """AgentModeDefinition accepts valid alphanumeric+underscore name."""
        AgentModeDefinition = _try_import(
            "posthog.agent.mode_definition.AgentModeDefinition"
        )
        mode = AgentModeDefinition(name="analysis_mode", max_iterations=10)
        assert mode.name == "analysis_mode"

    def test_agent_mode_name_with_spaces_raises_error(self):
        """AgentModeDefinition raises ValueError for name with spaces."""
        AgentModeDefinition = _try_import(
            "posthog.agent.mode_definition.AgentModeDefinition"
        )
        with pytest.raises(ValueError):
            AgentModeDefinition(name="invalid name", max_iterations=5)

    def test_max_iterations_zero_raises_error(self):
        """AgentModeDefinition raises ValueError when max_iterations=0."""
        AgentModeDefinition = _try_import(
            "posthog.agent.mode_definition.AgentModeDefinition"
        )
        with pytest.raises(ValueError):
            AgentModeDefinition(name="mode1", max_iterations=0)

    def test_trajectory_success_rate_four_of_five(self):
        """Trajectory.success_rate returns 0.8 for 4 successes out of 5 steps."""
        Trajectory = _try_import("posthog.agent.trajectory.Trajectory")
        t = Trajectory()
        for i in range(5):
            t.add_step(success=(i < 4))
        assert (
            abs(t.success_rate - 0.8) < 1e-9
        ), f"Expected success_rate=0.8, got {t.success_rate}"

    def test_to_dict_from_dict_round_trip(self):
        """to_dict/from_dict round-trip preserves AgentModeDefinition attributes."""
        AgentModeDefinition = _try_import(
            "posthog.agent.mode_definition.AgentModeDefinition"
        )
        m = AgentModeDefinition(name="test_mode", max_iterations=5)
        d = m.to_dict()
        m2 = AgentModeDefinition.from_dict(d)
        assert m2.name == "test_mode"
        assert m2.max_iterations == 5

    def test_iteration_limit_exceeded_error_raised(self):
        """AgentToolkit raises IterationLimitExceeded beyond max_iterations."""
        if REPO_DIR not in sys.path:
            sys.path.insert(0, REPO_DIR)
        try:
            from posthog.agent.toolkit import AgentToolkit, IterationLimitExceeded
        except ImportError as exc:
            pytest.skip(f"Cannot import toolkit: {exc}")
        toolkit = AgentToolkit(max_iterations=2)
        with pytest.raises(IterationLimitExceeded):
            for i in range(3):
                toolkit.check_iteration(i)
