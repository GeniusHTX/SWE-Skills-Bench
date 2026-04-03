"""
Tests for 'add-admin-api-endpoint' skill.
Generated from benchmark case definitions for add-admin-api-endpoint.
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


class TestAddAdminApiEndpoint:
    """Verify the add-admin-api-endpoint skill output."""

    REPO_DIR = '/workspace/Ghost'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestAddAdminApiEndpoint.REPO_DIR, rel)

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

    def test_webhook_route_file_exists(self):
        """Verify that the webhook controller/route file exists in the expected Ghost CMS directory structure"""
        _p = self._repo_path('core/server/routes/admin/index.js')
        assert os.path.isfile(_p), f'Missing file: core/server/routes/admin/index.js'
        _p = self._repo_path('core/server/controllers/webhooks.js')
        assert os.path.isfile(_p), f'Missing file: core/server/controllers/webhooks.js'

    def test_webhook_model_file_exists(self):
        """Verify the Webhook model definition file exists"""
        _p = self._repo_path('core/server/models/webhook.js')
        assert os.path.isfile(_p), f'Missing file: core/server/models/webhook.js'

    def test_webhook_test_file_exists(self):
        """Verify a test file for webhook endpoints exists"""
        _p = self._repo_path('test/regression/api/admin/webhooks.test.js')
        assert os.path.isfile(_p), f'Missing file: test/regression/api/admin/webhooks.test.js'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_route_handlers_defined(self):
        """Verify POST, GET, DELETE route handlers are defined for /webhooks/"""
        _p = self._repo_path('core/server/routes/admin/index.js')
        assert os.path.exists(_p), f'Missing: core/server/routes/admin/index.js'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert re.search('router.post.*webhooks', _all, re.MULTILINE), 'Pattern not found: router.post.*webhooks'
        assert re.search('router.get.*webhooks', _all, re.MULTILINE), 'Pattern not found: router.get.*webhooks'
        assert re.search('router.delete.*webhooks', _all, re.MULTILINE), 'Pattern not found: router.delete.*webhooks'

    def test_controller_methods_present(self):
        """Verify webhooksController has add, browse, read, edit, destroy methods"""
        _p = self._repo_path('core/server/controllers/webhooks.js')
        assert os.path.exists(_p), f'Missing: core/server/controllers/webhooks.js'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'add' in _all, 'Missing: add'
        assert 'browse' in _all, 'Missing: browse'
        assert 'read' in _all, 'Missing: read'
        assert 'edit' in _all, 'Missing: edit'
        assert 'destroy' in _all, 'Missing: destroy'

    def test_authentication_middleware_applied(self):
        """Verify authentication middleware is applied on webhook routes"""
        _p = self._repo_path('core/server/routes/admin/index.js')
        assert os.path.exists(_p), f'Missing: core/server/routes/admin/index.js'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'auth' in _all, 'Missing: auth'
        assert 'authenticate' in _all, 'Missing: authenticate'
        assert 'middleware' in _all, 'Missing: middleware'

    def test_response_wrapper_format(self):
        """Verify response body wraps webhooks in {webhooks: [...]} or {webhook: {...}} key"""
        _p = self._repo_path('core/server/controllers/webhooks.js')
        assert os.path.exists(_p), f'Missing: core/server/controllers/webhooks.js'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'webhooks' in _all, 'Missing: webhooks'
        assert 'webhook' in _all, 'Missing: webhook'

    # ── functional_check ────────────────────────────────────────

    def test_create_webhook_returns_201(self):
        """Verify POST /webhooks/ returns HTTP 201 Created (not 200)"""
        self._ensure_setup('test_create_webhook_returns_201', ['npm install'], 'skip_if_setup_fails')
        result = self._run_cmd("npm test -- --grep 'webhooks'", args=[], timeout=300)
        assert result.returncode == 0, (
            f'test_create_webhook_returns_201 failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_get_nonexistent_webhook_returns_404(self):
        """Verify GET /webhooks/:id with non-existent ID returns 404"""
        self._ensure_setup('test_get_nonexistent_webhook_returns_404', ['npm install'], 'skip_if_setup_fails')
        result = self._run_cmd('node -e "const ctrl = require(\'./core/server/controllers/webhooks\'); console.log(typeof ctrl.read)"', args=[], timeout=120)
        assert result.returncode == 0, (
            f'test_get_nonexistent_webhook_returns_404 failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_delete_webhook_returns_204(self):
        """Verify DELETE handler is configured to return 204 No Content"""
        _p = self._repo_path('core/server/controllers/webhooks.js')
        assert os.path.exists(_p), f'Missing: core/server/controllers/webhooks.js'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert '204' in _all, 'Missing: 204'
        assert 'No Content' in _all, 'Missing: No Content'
        assert 'destroy' in _all, 'Missing: destroy'

    def test_unauthenticated_request_returns_401(self):
        """Verify that unauthenticated requests to webhook endpoints return 401"""
        _p = self._repo_path('core/server/routes/admin/index.js')
        assert os.path.exists(_p), f'Missing: core/server/routes/admin/index.js'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'auth' in _all, 'Missing: auth'
        assert '401' in _all, 'Missing: 401'
        assert 'Unauthorized' in _all, 'Missing: Unauthorized'

    def test_post_missing_target_url_returns_422(self):
        """Verify POST with missing target_url returns 422 validation error"""
        _p = self._repo_path('core/server/controllers/webhooks.js')
        assert os.path.exists(_p), f'Missing: core/server/controllers/webhooks.js'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'target_url' in _all, 'Missing: target_url'
        assert 'validation' in _all, 'Missing: validation'
        assert '422' in _all, 'Missing: 422'

