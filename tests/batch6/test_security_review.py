"""
Tests for 'security-review' skill.
Generated from benchmark case definitions for security-review.
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


class TestSecurityReview:
    """Verify the security-review skill output."""

    REPO_DIR = '/workspace/babybuddy'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestSecurityReview.REPO_DIR, rel)

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

    def test_security_config_exists(self):
        """Verify security configuration module exists"""
        _p = self._repo_path('src/config/security.ts')
        assert os.path.isfile(_p), f'Missing file: src/config/security.ts'

    def test_auth_middleware_exists(self):
        """Verify auth middleware module exists"""
        _p = self._repo_path('src/middleware/auth.ts')
        assert os.path.isfile(_p), f'Missing file: src/middleware/auth.ts'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_helmet_configuration(self):
        """Verify configureHelmet uses helmet with CSP directives"""
        _p = self._repo_path('src/config/security.ts')
        assert os.path.exists(_p), f'Missing: src/config/security.ts'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'helmet' in _all, 'Missing: helmet'
        assert 'configureHelmet' in _all, 'Missing: configureHelmet'
        assert 'contentSecurityPolicy' in _all, 'Missing: contentSecurityPolicy'
        assert 'hsts' in _all, 'Missing: hsts'

    def test_jwt_verify_not_decode(self):
        """Verify validateJWT uses jwt.verify not jwt.decode"""
        _p = self._repo_path('src/middleware/auth.ts')
        assert os.path.exists(_p), f'Missing: src/middleware/auth.ts'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'jwt.verify' in _all, 'Missing: jwt.verify'
        assert 'validateJWT' in _all, 'Missing: validateJWT'
        assert 'req.user' in _all, 'Missing: req.user'

    def test_no_hardcoded_secret(self):
        """Verify JWT_SECRET loaded from env, not hardcoded"""
        _p = self._repo_path('src/middleware/auth.ts')
        assert os.path.exists(_p), f'Missing: src/middleware/auth.ts'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'process.env.JWT_SECRET' in _all, 'Missing: process.env.JWT_SECRET'
        assert 'process.env' in _all, 'Missing: process.env'

    def test_sanitize_input_middleware(self):
        """Verify sanitizeInput strips XSS from body fields"""
        _p = self._repo_path('src/middleware/auth.ts')
        assert os.path.exists(_p), f'Missing: src/middleware/auth.ts'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'sanitizeInput' in _all, 'Missing: sanitizeInput'
        assert 'script' in _all, 'Missing: script'
        assert 'replace' in _all, 'Missing: replace'
        assert 'sanitize' in _all, 'Missing: sanitize'

    # ── functional_check ────────────────────────────────────────

    def test_typescript_compiles(self):
        """Verify TypeScript compiles without errors"""
        self._ensure_setup('test_typescript_compiles', ['npm install'], 'fail_if_missing')
        result = self._run_cmd('npx', args=['tsc', '--noEmit'], timeout=120)
        assert result.returncode == 0, (
            f'test_typescript_compiles failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_valid_jwt_passes(self):
        """Verify valid JWT token passes middleware and sets req.user"""
        self._ensure_setup('test_valid_jwt_passes', ['npm install'], 'fail_if_missing')
        result = self._run_cmd('npm', args=['test', '--', '--testNamePattern', 'valid JWT'], timeout=300)
        assert result.returncode == 0, (
            f'test_valid_jwt_passes failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_expired_jwt_returns_401(self):
        """Verify expired JWT returns 401"""
        self._ensure_setup('test_expired_jwt_returns_401', ['npm install'], 'fail_if_missing')
        result = self._run_cmd('npm', args=['test', '--', '--testNamePattern', 'expired token'], timeout=300)
        assert result.returncode == 0, (
            f'test_expired_jwt_returns_401 failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_missing_token_returns_401(self):
        """Verify missing Authorization header returns 401"""
        self._ensure_setup('test_missing_token_returns_401', ['npm install'], 'fail_if_missing')
        result = self._run_cmd('npm', args=['test', '--', '--testNamePattern', 'no token'], timeout=300)
        assert result.returncode == 0, (
            f'test_missing_token_returns_401 failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_rate_limit_exceeded_429(self):
        """Verify rate limit returns 429 after exceeding threshold"""
        self._ensure_setup('test_rate_limit_exceeded_429', ['npm install'], 'fail_if_missing')
        result = self._run_cmd('npm', args=['test', '--', '--testNamePattern', 'rate limit'], timeout=300)
        assert result.returncode == 0, (
            f'test_rate_limit_exceeded_429 failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_helmet_headers_present(self):
        """Verify helmet sets security headers like x-content-type-options"""
        self._ensure_setup('test_helmet_headers_present', ['npm install'], 'fail_if_missing')
        result = self._run_cmd('npm', args=['test', '--', '--testNamePattern', 'helmet headers'], timeout=300)
        assert result.returncode == 0, (
            f'test_helmet_headers_present failed (exit {result.returncode})\n' + result.stderr[:500]
        )

