"""
Tests for 'clojure-write' skill.
Generated from benchmark case definitions for clojure-write.
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


class TestClojureWrite:
    """Verify the clojure-write skill output."""

    REPO_DIR = '/workspace/metabase'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestClojureWrite.REPO_DIR, rel)

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

    def test_queries_clj_exists(self):
        """Verify audit queries namespace file exists"""
        _p = self._repo_path('src/metabase/audit/queries.clj')
        assert os.path.isfile(_p), f'Missing file: src/metabase/audit/queries.clj'

    def test_queries_test_exists(self):
        """Verify test file for audit queries exists"""
        _p = self._repo_path('test/metabase/audit/queries_test.clj')
        assert os.path.isfile(_p), f'Missing file: test/metabase/audit/queries_test.clj'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_query_audit_log_defn(self):
        """Verify query-audit-log function is defined with docstring"""
        _p = self._repo_path('src/metabase/audit/queries.clj')
        assert os.path.exists(_p), f'Missing: src/metabase/audit/queries.clj'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'defn query-audit-log' in _all, 'Missing: defn query-audit-log'

    def test_format_audit_entry_defn(self):
        """Verify format-audit-entry function is defined"""
        _p = self._repo_path('src/metabase/audit/queries.clj')
        assert os.path.exists(_p), f'Missing: src/metabase/audit/queries.clj'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'defn format-audit-entry' in _all, 'Missing: defn format-audit-entry'

    def test_aggregate_by_user_defn(self):
        """Verify aggregate-by-user function is defined"""
        _p = self._repo_path('src/metabase/audit/queries.clj')
        assert os.path.exists(_p), f'Missing: src/metabase/audit/queries.clj'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'defn aggregate-by-user' in _all, 'Missing: defn aggregate-by-user'

    def test_db_namespace_require(self):
        """Verify namespace requires DB layer (metabase.db or next.jdbc or honeysql)"""
        _p = self._repo_path('src/metabase/audit/queries.clj')
        assert os.path.exists(_p), f'Missing: src/metabase/audit/queries.clj'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'metabase.db' in _all, 'Missing: metabase.db'
        assert 'next.jdbc' in _all, 'Missing: next.jdbc'
        assert 'honeysql' in _all, 'Missing: honeysql'

    # ── functional_check ────────────────────────────────────────

    def test_query_returns_seq(self):
        """Verify query-audit-log returns a seq (not nil) for valid input"""
        result = self._run_cmd('clojure', args=['-M:dev', '-e', "(require '[metabase.audit.queries :as audit]) (println (sequential? (audit/query-audit-log {:limit 5 :offset 0})))"], timeout=120)
        assert result.returncode == 0, (
            f'test_query_returns_seq failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_format_entry_required_keys(self):
        """Verify format-audit-entry output has :timestamp :user-id :action keys"""
        result = self._run_cmd('clojure', args=['-M:dev', '-e', '(require \'[metabase.audit.queries :as audit]) (let [e (audit/format-audit-entry {:id 1 :user_id 1 :action "create" :created_at "2024-01-01"})] (println (every? #(contains? e %) [:timestamp :user-id :action])))'], timeout=120)
        assert result.returncode == 0, (
            f'test_format_entry_required_keys failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_empty_result_returns_empty_seq(self):
        """Verify empty result returns empty seq (not nil)"""
        result = self._run_cmd('clojure', args=['-M:dev', '-e', "(require '[metabase.audit.queries :as audit]) (let [r (audit/query-audit-log {:user-id -999 :limit 5 :offset 0})] (println (and (not (nil? r)) (empty? r))))"], timeout=120)
        assert result.returncode == 0, (
            f'test_empty_result_returns_empty_seq failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_count_audit_events_nonneg(self):
        """Verify count-audit-events returns non-negative integer"""
        result = self._run_cmd('clojure', args=['-M:dev', '-e', "(require '[metabase.audit.queries :as audit]) (println (>= (audit/count-audit-events {}) 0))"], timeout=120)
        assert result.returncode == 0, (
            f'test_count_audit_events_nonneg failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_invalid_user_id_type_throws(self):
        """Verify string user-id throws ExceptionInfo with :status 400"""
        result = self._run_cmd('clojure', args=['-M:dev', '-e', '(require \'[metabase.audit.queries :as audit]) (try (audit/query-audit-log {:user-id "not-an-int"}) (println false) (catch clojure.lang.ExceptionInfo e (println (= 400 (:status (ex-data e))))))'], timeout=120)
        assert result.returncode == 0, (
            f'test_invalid_user_id_type_throws failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_limit_zero_returns_empty(self):
        """Verify limit=0 returns empty result set"""
        result = self._run_cmd('clojure', args=['-M:dev', '-e', "(require '[metabase.audit.queries :as audit]) (println (empty? (audit/query-audit-log {:limit 0 :offset 0})))"], timeout=120)
        assert result.returncode == 0, (
            f'test_limit_zero_returns_empty failed (exit {result.returncode})\n' + result.stderr[:500]
        )

