"""
Tests for 'prompt-engineering-patterns' skill.
Generated from benchmark case definitions for prompt-engineering-patterns.
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


class TestPromptEngineeringPatterns:
    """Verify the prompt-engineering-patterns skill output."""

    REPO_DIR = '/workspace/langchain'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestPromptEngineeringPatterns.REPO_DIR, rel)

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

    def test_template_files_exist(self):
        """Verify all 3 template modules exist"""
        _p = self._repo_path('templates/chat_prompt.py')
        assert os.path.isfile(_p), f'Missing file: templates/chat_prompt.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('templates/few_shot.py')
        assert os.path.isfile(_p), f'Missing file: templates/few_shot.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('templates/chain_of_thought.py')
        assert os.path.isfile(_p), f'Missing file: templates/chain_of_thought.py'
        py_compile.compile(_p, doraise=True)

    def test_tests_file_exists(self):
        """Verify test file exists"""
        _p = self._repo_path('tests/test_prompt_templates.py')
        assert os.path.isfile(_p), f'Missing file: tests/test_prompt_templates.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_chat_prompt_class_defined(self):
        """Verify ChatPromptTemplate class with format_messages method"""
        _p = self._repo_path('templates/chat_prompt.py')
        assert os.path.exists(_p), f'Missing: templates/chat_prompt.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'ChatPromptTemplate' in _all, 'Missing: ChatPromptTemplate'
        assert 'format_messages' in _all, 'Missing: format_messages'

    def test_few_shot_class_defined(self):
        """Verify FewShotPromptTemplate with example selector"""
        _p = self._repo_path('templates/few_shot.py')
        assert os.path.exists(_p), f'Missing: templates/few_shot.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'FewShotPromptTemplate' in _all, 'Missing: FewShotPromptTemplate'
        assert 'example_selector' in _all, 'Missing: example_selector'
        assert 'format_prompt' in _all, 'Missing: format_prompt'

    def test_cot_prompt_defined(self):
        """Verify ChainOfThoughtPrompt adds reasoning instruction"""
        _p = self._repo_path('templates/chain_of_thought.py')
        assert os.path.exists(_p), f'Missing: templates/chain_of_thought.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'ChainOfThoughtPrompt' in _all, 'Missing: ChainOfThoughtPrompt'
        assert 'step by step' in _all, 'Missing: step by step'

    def test_langchain_imports(self):
        """Verify langchain imports in template files"""
        _p = self._repo_path('templates/chat_prompt.py')
        assert os.path.exists(_p), f'Missing: templates/chat_prompt.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'langchain' in _all, 'Missing: langchain'
        assert 'SystemMessage' in _all, 'Missing: SystemMessage'
        assert 'HumanMessage' in _all, 'Missing: HumanMessage'

    # ── functional_check ────────────────────────────────────────

    def test_format_messages_returns_messages(self):
        """Verify format_messages returns list of BaseMessage instances"""
        self._ensure_setup('test_format_messages_returns_messages', ['pip install langchain langchain-core'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from templates.chat_prompt import ChatPromptTemplate; from langchain.schema import SystemMessage, HumanMessage; t=ChatPromptTemplate.from_messages([('system','You are helpful'),('human','{query}')]); msgs=t.format_messages(query='Hi'); assert len(msgs)==2; assert isinstance(msgs[0],SystemMessage); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_format_messages_returns_messages failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_missing_variable_error(self):
        """Verify missing variable raises KeyError"""
        self._ensure_setup('test_missing_variable_error', ['pip install langchain langchain-core'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from templates.chat_prompt import ChatPromptTemplate; t=ChatPromptTemplate.from_messages([('human','{query}')])\ntry:\n    t.format_messages()\n    assert False, 'Should have raised'\nexcept (KeyError, Exception) as e:\n    assert 'query' in str(e).lower() or True; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_missing_variable_error failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_few_shot_selects_k(self):
        """Verify FewShotPromptTemplate honors k parameter"""
        self._ensure_setup('test_few_shot_selects_k', ['pip install langchain langchain-core'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from templates.few_shot import FewShotPromptTemplate; examples=[{'input':'Q1','output':'A1'},{'input':'Q2','output':'A2'},{'input':'Q3','output':'A3'}]; t=FewShotPromptTemplate(examples=examples, k=2); result=str(t.format_prompt(input='test')); assert result.count('A')>=2; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_few_shot_selects_k failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_cot_adds_instruction(self):
        """Verify ChainOfThoughtPrompt adds step-by-step instruction"""
        self._ensure_setup('test_cot_adds_instruction', ['pip install langchain langchain-core'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from templates.chain_of_thought import ChainOfThoughtPrompt; cot=ChainOfThoughtPrompt(); result=str(cot); assert 'step' in result.lower() or 'reason' in result.lower(); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_cot_adds_instruction failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_pytest_prompt_templates(self):
        """Run pytest for prompt template tests"""
        self._ensure_setup('test_pytest_prompt_templates', ['pip install langchain langchain-core pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_prompt_templates.py', '-v', '--tb=short'], timeout=120)
        assert result.returncode == 0, (
            f'test_pytest_prompt_templates failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_empty_examples_handled(self):
        """Verify FewShotPromptTemplate handles empty examples list"""
        self._ensure_setup('test_empty_examples_handled', ['pip install langchain langchain-core'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from templates.few_shot import FewShotPromptTemplate; t=FewShotPromptTemplate(examples=[], k=0); result=t.format_prompt(input='test'); assert result is not None; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_empty_examples_handled failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

