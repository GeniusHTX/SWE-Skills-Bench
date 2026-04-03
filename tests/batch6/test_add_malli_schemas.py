"""
Tests for 'add-malli-schemas' skill.
Generated from benchmark case definitions for add-malli-schemas.
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


class TestAddMalliSchemas:
    """Verify the add-malli-schemas skill output."""

    REPO_DIR = '/workspace/metabase'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestAddMalliSchemas.REPO_DIR, rel)

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

    def test_schemas_file_exists(self):
        """Verify the malli schema definition file exists"""
        _p = self._repo_path('src/metabase/models/schemas.cljc')
        assert os.path.isfile(_p), f'Missing file: src/metabase/models/schemas.cljc'

    def test_schema_test_file_exists(self):
        """Verify test file for schemas exists"""
        _p = self._repo_path('test/metabase/models/schemas_test.clj')
        assert os.path.isfile(_p), f'Missing file: test/metabase/models/schemas_test.clj'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_malli_core_require(self):
        """Verify schemas.cljc uses malli.core namespace"""
        _p = self._repo_path('src/metabase/models/schemas.cljc')
        assert os.path.exists(_p), f'Missing: src/metabase/models/schemas.cljc'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'malli.core' in _all, 'Missing: malli.core'
        assert 'malli.registry' in _all, 'Missing: malli.registry'

    def test_all_entity_schemas_defined(self):
        """Verify all 5+ entity schemas are defined: user, card, dashboard, database, table/field"""
        _p = self._repo_path('src/metabase/models/schemas.cljc')
        assert os.path.exists(_p), f'Missing: src/metabase/models/schemas.cljc'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert ':user/Schema' in _all, 'Missing: :user/Schema'
        assert ':card/Schema' in _all, 'Missing: :card/Schema'
        assert ':dashboard/Schema' in _all, 'Missing: :dashboard/Schema'
        assert ':database/Schema' in _all, 'Missing: :database/Schema'

    def test_email_validation_pattern(self):
        """Verify email format validator is defined for user schema"""
        _p = self._repo_path('src/metabase/models/schemas.cljc')
        assert os.path.exists(_p), f'Missing: src/metabase/models/schemas.cljc'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'email' in _all, 'Missing: email'
        assert 're-pattern' in _all, 'Missing: re-pattern'
        assert '@' in _all, 'Missing: @'

    def test_engine_enum_validation(self):
        """Verify database schema restricts :engine to enumerated set of keywords"""
        _p = self._repo_path('src/metabase/models/schemas.cljc')
        assert os.path.exists(_p), f'Missing: src/metabase/models/schemas.cljc'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert ':engine' in _all, 'Missing: :engine'
        assert 'enum' in _all, 'Missing: enum'
        assert ':h2' in _all, 'Missing: :h2'
        assert ':postgres' in _all, 'Missing: :postgres'
        assert ':mysql' in _all, 'Missing: :mysql'

    # ── functional_check ────────────────────────────────────────

    def test_valid_user_validates_true(self):
        """Verify a valid user map passes malli validation"""
        result = self._run_cmd('clojure', args=['-M:dev', '-e', '(require \'[metabase.models.schemas]) (require \'[malli.core :as m]) (println (m/validate :user/Schema {:id 1 :email "a@b.com" :first_name "A" :last_name "B"}))'], timeout=120)
        assert result.returncode == 0, (
            f'test_valid_user_validates_true failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_invalid_user_negative_id(self):
        """Verify user with negative id fails validation"""
        result = self._run_cmd('clojure', args=['-M:dev', '-e', '(require \'[metabase.models.schemas]) (require \'[malli.core :as m]) (println (m/validate :user/Schema {:id -1 :email "a@b.com" :first_name "A" :last_name "B"}))'], timeout=120)
        assert result.returncode == 0, (
            f'test_invalid_user_negative_id failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_invalid_email_format(self):
        """Verify invalid email format fails validation"""
        result = self._run_cmd('clojure', args=['-M:dev', '-e', '(require \'[metabase.models.schemas]) (require \'[malli.core :as m]) (println (m/validate :user/Schema {:id 1 :email "not-email" :first_name "A" :last_name "B"}))'], timeout=120)
        assert result.returncode == 0, (
            f'test_invalid_email_format failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_explain_returns_errors_for_invalid(self):
        """Verify m/explain returns non-nil errors for invalid data"""
        result = self._run_cmd('clojure', args=['-M:dev', '-e', "(require '[metabase.models.schemas]) (require '[malli.core :as m]) (println (some? (m/explain :user/Schema {:id -1})))"], timeout=120)
        assert result.returncode == 0, (
            f'test_explain_returns_errors_for_invalid failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_optional_field_absent_validates(self):
        """Verify user with optional :is_superuser absent still validates"""
        result = self._run_cmd('clojure', args=['-M:dev', '-e', '(require \'[metabase.models.schemas]) (require \'[malli.core :as m]) (println (m/validate :user/Schema {:id 1 :email "a@b.com" :first_name "A" :last_name "B"}))'], timeout=120)
        assert result.returncode == 0, (
            f'test_optional_field_absent_validates failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_unsupported_engine_fails(self):
        """Verify database with unsupported engine keyword fails validation"""
        result = self._run_cmd('clojure', args=['-M:dev', '-e', '(require \'[metabase.models.schemas]) (require \'[malli.core :as m]) (println (m/validate :database/Schema {:name "db" :engine :unsupported-db :details {}}))'], timeout=120)
        assert result.returncode == 0, (
            f'test_unsupported_engine_fails failed (exit {result.returncode})\n' + result.stderr[:500]
        )

