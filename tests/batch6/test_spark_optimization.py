"""
Tests for 'spark-optimization' skill.
Generated from benchmark case definitions for spark-optimization.
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


class TestSparkOptimization:
    """Verify the spark-optimization skill output."""

    REPO_DIR = '/workspace/spark'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestSparkOptimization.REPO_DIR, rel)

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

    def test_etl_modules_exist(self):
        """Verify ETL source modules exist"""
        _p = self._repo_path('etl/spark_config.py')
        assert os.path.isfile(_p), f'Missing file: etl/spark_config.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('etl/jobs/clickstream_daily.py')
        assert os.path.isfile(_p), f'Missing file: etl/jobs/clickstream_daily.py'
        py_compile.compile(_p, doraise=True)

    def test_etl_test_file_exists(self):
        """Verify test file exists"""
        _p = self._repo_path('tests/test_etl.py')
        assert os.path.isfile(_p), f'Missing file: tests/test_etl.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_create_spark_session_function(self):
        """Verify create_spark_session function defined in spark_config"""
        _p = self._repo_path('etl/spark_config.py')
        assert os.path.exists(_p), f'Missing: etl/spark_config.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'def create_spark_session' in _all, 'Missing: def create_spark_session'
        assert 'SparkSession' in _all, 'Missing: SparkSession'
        assert 'builder' in _all, 'Missing: builder'
        assert 'config' in _all, 'Missing: config'

    def test_aqe_enabled_in_config(self):
        """Verify AQE explicitly enabled in Spark config"""
        _p = self._repo_path('etl/spark_config.py')
        assert os.path.exists(_p), f'Missing: etl/spark_config.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'spark.sql.adaptive.enabled' in _all, 'Missing: spark.sql.adaptive.enabled'
        assert 'true' in _all, 'Missing: true'

    def test_shuffle_partitions_tuned(self):
        """Verify shuffle partitions tuned below default 200"""
        _p = self._repo_path('etl/spark_config.py')
        assert os.path.exists(_p), f'Missing: etl/spark_config.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'spark.sql.shuffle.partitions' in _all, 'Missing: spark.sql.shuffle.partitions'

    def test_broadcast_or_cache_usage(self):
        """Verify broadcast join or cache/persist used in job"""
        _p = self._repo_path('etl/jobs/clickstream_daily.py')
        assert os.path.exists(_p), f'Missing: etl/jobs/clickstream_daily.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'broadcast' in _all, 'Missing: broadcast'
        assert 'persist' in _all, 'Missing: persist'
        assert 'cache' in _all, 'Missing: cache'
        assert 'StorageLevel' in _all, 'Missing: StorageLevel'

    # ── functional_check ────────────────────────────────────────

    def test_create_spark_session_returns_session(self):
        """Verify create_spark_session returns valid SparkSession"""
        self._ensure_setup('test_create_spark_session_returns_session', ['pip install pyspark'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from etl.spark_config import create_spark_session; spark=create_spark_session('test'); from pyspark.sql import SparkSession; assert isinstance(spark, SparkSession); spark.stop(); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_create_spark_session_returns_session failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_aqe_config_value(self):
        """Verify AQE config is true at runtime"""
        self._ensure_setup('test_aqe_config_value', ['pip install pyspark'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from etl.spark_config import create_spark_session; spark=create_spark_session('test'); assert spark.conf.get('spark.sql.adaptive.enabled')=='true'; spark.stop(); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_aqe_config_value failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_shuffle_partitions_below_200(self):
        """Verify shuffle partitions tuned below 200 at runtime"""
        self._ensure_setup('test_shuffle_partitions_below_200', ['pip install pyspark'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from etl.spark_config import create_spark_session; spark=create_spark_session('test'); val=int(spark.conf.get('spark.sql.shuffle.partitions')); assert val<200; spark.stop(); print(f'PASS: partitions={val}')"], timeout=120)
        assert result.returncode == 0, (
            f'test_shuffle_partitions_below_200 failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_run_job_output_schema(self):
        """Verify run_job produces output with correct schema"""
        self._ensure_setup('test_run_job_output_schema', ['pip install pyspark pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_etl.py', '-v', '-k', 'test_output_schema'], timeout=120)
        assert result.returncode == 0, (
            f'test_run_job_output_schema failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_run_job_empty_input(self):
        """Verify run_job with empty input returns empty DataFrame"""
        self._ensure_setup('test_run_job_empty_input', ['pip install pyspark pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_etl.py', '-v', '-k', 'test_empty_input'], timeout=120)
        assert result.returncode == 0, (
            f'test_run_job_empty_input failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_full_etl_suite(self):
        """Run the full ETL test suite"""
        self._ensure_setup('test_full_etl_suite', ['pip install pyspark pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_etl.py', '-v', '--tb=short'], timeout=120)
        assert result.returncode == 0, (
            f'test_full_etl_suite failed (exit {result.returncode})\n' + result.stderr[:500]
        )

