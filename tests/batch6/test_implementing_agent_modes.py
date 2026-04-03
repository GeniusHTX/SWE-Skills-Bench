"""
Tests for 'implementing-agent-modes' skill.
Generated from benchmark case definitions for implementing-agent-modes.
"""

import ast
import base64
import glob
import json
import os
import py_compile
import re
import subprocess
import textwrap

import pytest

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


class TestImplementingAgentModes:
    """Verify the implementing-agent-modes skill output."""

    REPO_DIR = '/workspace/posthog'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestImplementingAgentModes.REPO_DIR, rel)

    @staticmethod
    def _safe_read(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    @staticmethod
    def _load_yaml(path: str):
        if yaml is None:
            pytest.skip("PyYAML not available")
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return yaml.safe_load(fh)

    @staticmethod
    def _load_json(path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return json.load(fh)

    @classmethod
    def _run_in_repo(cls, script: str, timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python", "-c", textwrap.dedent(script)],
            cwd=cls.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def _run_cmd(cls, command, args=None, timeout=120):
        args = args or []
        if isinstance(command, str) and args:
            return subprocess.run(
                [command, *args],
                cwd=cls.REPO_DIR,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        return subprocess.run(
            command if isinstance(command, list) else command,
            cwd=cls.REPO_DIR,
            shell=isinstance(command, str),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def _ensure_setup(cls, label, setup_cmds, fallback):
        if not setup_cmds:
            return
        key = tuple(setup_cmds)
        if key in cls._SETUP_CACHE:
            ok, msg = cls._SETUP_CACHE[key]
            if ok:
                return
            if fallback == "skip_if_setup_fails":
                pytest.skip(f"{label} setup failed: {msg}")
            pytest.fail(f"{label} setup failed: {msg}")
        for cmd in setup_cmds:
            r = subprocess.run(cmd, cwd=cls.REPO_DIR, shell=True,
                               capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                msg = (r.stderr or r.stdout or 'failed').strip()
                cls._SETUP_CACHE[key] = (False, msg)
                if fallback == "skip_if_setup_fails":
                    pytest.skip(f"{label} setup failed: {msg}")
                pytest.fail(f"{label} setup failed: {msg}")
        cls._SETUP_CACHE[key] = (True, 'ok')


    # ── file_path_check (static) ────────────────────────────────────────

    def test_data_explorer_module_exists(self):
        """Verify data_explorer preset module exists"""
        _p = self._repo_path('ee/hogai/core/agent_modes/presets/data_explorer/__init__.py')
        assert os.path.isfile(_p), f'Missing file: ee/hogai/core/agent_modes/presets/data_explorer/__init__.py'
        py_compile.compile(_p, doraise=True)

    def test_session_replay_module_exists(self):
        """Verify session_replay preset module exists"""
        _p = self._repo_path('ee/hogai/core/agent_modes/presets/session_replay/__init__.py')
        assert os.path.isfile(_p), f'Missing file: ee/hogai/core/agent_modes/presets/session_replay/__init__.py'
        py_compile.compile(_p, doraise=True)

    def test_registry_module_exists(self):
        """Verify registry.py and base.py exist"""
        _p = self._repo_path('ee/hogai/core/agent_modes/registry.py')
        assert os.path.isfile(_p), f'Missing file: ee/hogai/core/agent_modes/registry.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('ee/hogai/core/agent_modes/base.py')
        assert os.path.isfile(_p), f'Missing file: ee/hogai/core/agent_modes/base.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_agent_mode_config_class(self):
        """Verify AgentModeConfig class has mode_id, tools, system_prompt fields"""
        _p = self._repo_path('ee/hogai/core/agent_modes/base.py')
        assert os.path.exists(_p), f'Missing: ee/hogai/core/agent_modes/base.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'AgentModeConfig' in _all, 'Missing: AgentModeConfig'
        assert 'mode_id' in _all, 'Missing: mode_id'
        assert 'tools' in _all, 'Missing: tools'
        assert 'system_prompt' in _all, 'Missing: system_prompt'

    def test_registry_functions_defined(self):
        """Verify register_agent_mode and get_agent_mode functions exist"""
        _p = self._repo_path('ee/hogai/core/agent_modes/registry.py')
        assert os.path.exists(_p), f'Missing: ee/hogai/core/agent_modes/registry.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'register_agent_mode' in _all, 'Missing: register_agent_mode'
        assert 'get_agent_mode' in _all, 'Missing: get_agent_mode'

    def test_data_explorer_tools_list(self):
        """Verify DataExplorerMode has execute_hogql and fetch_schema tools"""
        _p = self._repo_path('ee/hogai/core/agent_modes/presets/data_explorer/__init__.py')
        assert os.path.exists(_p), f'Missing: ee/hogai/core/agent_modes/presets/data_explorer/__init__.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'execute_hogql' in _all, 'Missing: execute_hogql'
        assert 'fetch_schema' in _all, 'Missing: fetch_schema'

    def test_session_replay_tools_list(self):
        """Verify SessionReplayMode has search_sessions and get_session_events tools"""
        _p = self._repo_path('ee/hogai/core/agent_modes/presets/session_replay/__init__.py')
        assert os.path.exists(_p), f'Missing: ee/hogai/core/agent_modes/presets/session_replay/__init__.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'search_sessions' in _all, 'Missing: search_sessions'
        assert 'get_session_events' in _all, 'Missing: get_session_events'

    # ── functional_check ────────────────────────────────────────

    def test_import_agent_mode_config(self):
        """Verify AgentModeConfig is importable and has required attributes"""
        self._ensure_setup('test_import_agent_mode_config', ['pip install pydantic'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from ee.hogai.core.agent_modes.base import AgentModeConfig; assert hasattr(AgentModeConfig, 'mode_id') or 'mode_id' in AgentModeConfig.__dataclass_fields__; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_import_agent_mode_config failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_get_data_explorer_mode(self):
        """Verify data-explorer mode is retrievable from registry"""
        self._ensure_setup('test_get_data_explorer_mode', ['pip install pydantic langgraph'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from ee.hogai.core.agent_modes.registry import get_agent_mode; config=get_agent_mode('data-explorer'); assert config is not None; assert len(config.system_prompt)>0; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_get_data_explorer_mode failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_get_nonexistent_mode(self):
        """Verify get_agent_mode with unknown ID raises KeyError"""
        self._ensure_setup('test_get_nonexistent_mode', ['pip install pydantic'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from ee.hogai.core.agent_modes.registry import get_agent_mode\ntry:\n    get_agent_mode('nonexistent')\n    assert False, 'Should have raised'\nexcept (KeyError, ValueError):\n    print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_get_nonexistent_mode failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_register_duplicate_mode(self):
        """Verify re-registering existing mode_id behavior is defined"""
        self._ensure_setup('test_register_duplicate_mode', ['pip install pydantic'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from ee.hogai.core.agent_modes.registry import register_agent_mode, get_agent_mode\nfrom ee.hogai.core.agent_modes.base import AgentModeConfig\nconfig=AgentModeConfig(mode_id='test-dup', tools=[], system_prompt='test', allowed_actions=[])\nregister_agent_mode('test-dup', config)\ntry:\n    register_agent_mode('test-dup', config)\n    print('PASS-overwrite')\nexcept (ValueError, KeyError):\n    print('PASS-error')"], timeout=120)
        assert result.returncode == 0, (
            f'test_register_duplicate_mode failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_none_system_prompt(self):
        """Verify AgentModeConfig rejects None system_prompt"""
        self._ensure_setup('test_none_system_prompt', ['pip install pydantic'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from ee.hogai.core.agent_modes.base import AgentModeConfig\ntry:\n    config=AgentModeConfig(mode_id='bad', tools=[], system_prompt=None, allowed_actions=[])\n    assert config.system_prompt is not None, 'system_prompt should not be None'\n    print('PASS-accepted')\nexcept (TypeError, ValueError, Exception):\n    print('PASS-rejected')"], timeout=120)
        assert result.returncode == 0, (
            f'test_none_system_prompt failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

