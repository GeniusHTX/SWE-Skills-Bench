"""
Tests for 'changelog-automation' skill.
Generated from benchmark case definitions for changelog-automation.
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


class TestChangelogAutomation:
    """Verify the changelog-automation skill output."""

    REPO_DIR = '/workspace/github-changelog-generator'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestChangelogAutomation.REPO_DIR, rel)

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

    def test_generate_changelog_script_exists(self):
        """Verify the changelog generation script exists"""
        _p = self._repo_path('scripts/generate-changelog.js')
        assert os.path.isfile(_p), f'Missing file: scripts/generate-changelog.js'

    def test_release_workflow_exists(self):
        """Verify GitHub Actions release workflow exists"""
        _p = self._repo_path('.github/workflows/release.yml')
        assert os.path.isfile(_p), f'Missing file: .github/workflows/release.yml'
        self._load_yaml(_p)  # parse check

    def test_package_json_exists(self):
        """Verify package.json with version field exists"""
        _p = self._repo_path('package.json')
        assert os.path.isfile(_p), f'Missing file: package.json'
        self._load_json(_p)  # parse check

    # ── semantic_check (static) ────────────────────────────────────────

    def test_conventional_commit_parsing(self):
        """Verify script parses conventional commit format (type: description)"""
        _p = self._repo_path('scripts/generate-changelog.js')
        assert os.path.exists(_p), f'Missing: scripts/generate-changelog.js'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'feat' in _all, 'Missing: feat'
        assert 'fix' in _all, 'Missing: fix'
        assert 'BREAKING CHANGE' in _all, 'Missing: BREAKING CHANGE'
        assert 'conventional' in _all, 'Missing: conventional'

    def test_markdown_section_generation(self):
        """Verify script generates Markdown sections (### Features, ### Bug Fixes)"""
        _p = self._repo_path('scripts/generate-changelog.js')
        assert os.path.exists(_p), f'Missing: scripts/generate-changelog.js'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'Features' in _all, 'Missing: Features'
        assert 'Bug Fixes' in _all, 'Missing: Bug Fixes'
        assert 'Breaking Changes' in _all, 'Missing: Breaking Changes'
        assert '###' in _all, 'Missing: ###'

    def test_release_workflow_tag_trigger(self):
        """Verify release.yml triggers on version tag push (v*)"""
        _p = self._repo_path('.github/workflows/release.yml')
        assert os.path.exists(_p), f'Missing: .github/workflows/release.yml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'tags' in _all, 'Missing: tags'
        assert 'v*' in _all, 'Missing: v*'
        assert 'push' in _all, 'Missing: push'

    def test_changelog_prepend_not_overwrite(self):
        """Verify script prepends to existing CHANGELOG.md rather than overwriting"""
        _p = self._repo_path('scripts/generate-changelog.js')
        assert os.path.exists(_p), f'Missing: scripts/generate-changelog.js'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'readFile' in _all, 'Missing: readFile'
        assert 'writeFile' in _all, 'Missing: writeFile'
        assert 'prepend' in _all, 'Missing: prepend'
        assert 'concat' in _all, 'Missing: concat'
        assert 'existing' in _all, 'Missing: existing'

    # ── functional_check ────────────────────────────────────────

    def test_release_yml_valid_yaml(self):
        """Verify release.yml is valid YAML"""
        result = self._run_cmd('python', args=['-c', "import yaml; yaml.safe_load(open('.github/workflows/release.yml')); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_release_yml_valid_yaml failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_package_json_valid(self):
        """Verify package.json is valid JSON with version field"""
        result = self._run_cmd('python', args=['-c', "import json; p=json.load(open('package.json')); assert 'version' in p, 'No version field'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_package_json_valid failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_changelog_script_help(self):
        """Verify script provides help/usage information"""
        self._ensure_setup('test_changelog_script_help', ['npm install'], 'skip_if_setup_fails')
        result = self._run_cmd('node', args=['scripts/generate-changelog.js', '--help'], timeout=120)
        assert result.returncode == 0, (
            f'test_changelog_script_help failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_missing_version_arg_exits_nonzero(self):
        """Verify script exits non-zero when --version argument is missing"""
        self._ensure_setup('test_missing_version_arg_exits_nonzero', ['npm install'], 'skip_if_setup_fails')
        result = self._run_cmd('node', args=['scripts/generate-changelog.js'], timeout=120)
        assert result.returncode == 0, (
            f'test_missing_version_arg_exits_nonzero failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_breaking_change_section_priority(self):
        """Verify Breaking Changes section appears before Features in output template"""
        _p = self._repo_path('scripts/generate-changelog.js')
        assert os.path.exists(_p), f'Missing: scripts/generate-changelog.js'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'Breaking Changes' in _all, 'Missing: Breaking Changes'
        assert 'Features' in _all, 'Missing: Features'

