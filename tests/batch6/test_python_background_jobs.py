"""
Tests for 'python-background-jobs' skill.
Generated from benchmark case definitions for python-background-jobs.
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


class TestPythonBackgroundJobs:
    """Verify the python-background-jobs skill output."""

    REPO_DIR = '/workspace/celery'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestPythonBackgroundJobs.REPO_DIR, rel)

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

    def test_tasks_module_exists(self):
        """Verify order processing tasks module exists"""
        _p = self._repo_path('app/tasks/order_tasks.py')
        assert os.path.isfile(_p), f'Missing file: app/tasks/order_tasks.py'
        py_compile.compile(_p, doraise=True)

    def test_models_module_exists(self):
        """Verify OrderStatus enum and order model exist"""
        _p = self._repo_path('app/models/order.py')
        assert os.path.isfile(_p), f'Missing file: app/models/order.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_order_status_enum_values(self):
        """Verify OrderStatus enum defines all 7 required states"""
        _p = self._repo_path('app/models/order.py')
        assert os.path.exists(_p), f'Missing: app/models/order.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'PENDING' in _all, 'Missing: PENDING'
        assert 'VALIDATING' in _all, 'Missing: VALIDATING'
        assert 'PAYMENT_PROCESSING' in _all, 'Missing: PAYMENT_PROCESSING'
        assert 'RESERVING_INVENTORY' in _all, 'Missing: RESERVING_INVENTORY'
        assert 'COMPLETED' in _all, 'Missing: COMPLETED'
        assert 'FAILED' in _all, 'Missing: FAILED'
        assert 'NOTIFYING' in _all, 'Missing: NOTIFYING'

    def test_celery_chain_composition(self):
        """Verify tasks are composed using celery.chain"""
        _p = self._repo_path('app/tasks/order_tasks.py')
        assert os.path.exists(_p), f'Missing: app/tasks/order_tasks.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'chain' in _all, 'Missing: chain'
        assert 'validate_order' in _all, 'Missing: validate_order'
        assert 'process_payment' in _all, 'Missing: process_payment'
        assert 'reserve_inventory' in _all, 'Missing: reserve_inventory'
        assert 'send_notification' in _all, 'Missing: send_notification'

    def test_retry_decorator_on_payment(self):
        """Verify process_payment has retry configuration for ConnectionError only"""
        _p = self._repo_path('app/tasks/order_tasks.py')
        assert os.path.exists(_p), f'Missing: app/tasks/order_tasks.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'autoretry_for' in _all, 'Missing: autoretry_for'
        assert 'ConnectionError' in _all, 'Missing: ConnectionError'
        assert 'max_retries' in _all, 'Missing: max_retries'

    def test_idempotency_pattern(self):
        """Verify reserve_inventory has idempotency check"""
        _p = self._repo_path('app/tasks/order_tasks.py')
        assert os.path.exists(_p), f'Missing: app/tasks/order_tasks.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'already_reserved' in _all, 'Missing: already_reserved'
        assert 'idempotency' in _all, 'Missing: idempotency'
        assert 'reserved' in _all, 'Missing: reserved'

    # ── functional_check ────────────────────────────────────────

    def test_validate_order_success(self):
        """Verify validate_order passes a valid order and updates status"""
        self._ensure_setup('test_validate_order_success', ['pip install celery pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_validate_order.py', '-v', '-k', 'test_valid_order'], timeout=120)
        assert result.returncode == 0, (
            f'test_validate_order_success failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_validate_order_missing_fields(self):
        """Verify validate_order rejects order missing required fields"""
        self._ensure_setup('test_validate_order_missing_fields', ['pip install celery pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_validate_order.py', '-v', '-k', 'test_missing_fields'], timeout=120)
        assert result.returncode == 0, (
            f'test_validate_order_missing_fields failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_process_payment_declined(self):
        """Verify PaymentDeclinedError is not retried and sets FAILED"""
        self._ensure_setup('test_process_payment_declined', ['pip install celery pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_process_payment.py', '-v', '-k', 'test_declined'], timeout=120)
        assert result.returncode == 0, (
            f'test_process_payment_declined failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_reserve_inventory_idempotent(self):
        """Verify calling reserve_inventory twice does not double-reserve"""
        self._ensure_setup('test_reserve_inventory_idempotent', ['pip install celery pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_reserve_inventory.py', '-v', '-k', 'test_idempotent'], timeout=120)
        assert result.returncode == 0, (
            f'test_reserve_inventory_idempotent failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_notification_failure_does_not_fail_order(self):
        """Verify send_notification failure does not set order to FAILED"""
        self._ensure_setup('test_notification_failure_does_not_fail_order', ['pip install celery pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_notification.py', '-v', '-k', 'test_notification_fails_gracefully'], timeout=120)
        assert result.returncode == 0, (
            f'test_notification_failure_does_not_fail_order failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_full_pipeline_success(self):
        """Run the full chain end-to-end with a valid order"""
        self._ensure_setup('test_full_pipeline_success', ['pip install celery pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_order_pipeline.py', '-v', '-k', 'test_full_success'], timeout=120)
        assert result.returncode == 0, (
            f'test_full_pipeline_success failed (exit {result.returncode})\n' + result.stderr[:500]
        )

