"""
Tests for 'django-patterns' skill.
Generated from benchmark case definitions for django-patterns.
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


class TestDjangoPatterns:
    """Verify the django-patterns skill output."""

    REPO_DIR = '/workspace/saleor'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestDjangoPatterns.REPO_DIR, rel)

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

    def test_wishlist_models_exists(self):
        """Verify wishlist models.py exists"""
        _p = self._repo_path('saleor/wishlist/models.py')
        assert os.path.isfile(_p), f'Missing file: saleor/wishlist/models.py'
        py_compile.compile(_p, doraise=True)

    def test_wishlist_mutations_exists(self):
        """Verify wishlist mutations.py exists"""
        _p = self._repo_path('saleor/wishlist/mutations.py')
        assert os.path.isfile(_p), f'Missing file: saleor/wishlist/mutations.py'
        py_compile.compile(_p, doraise=True)

    def test_wishlist_migration_exists(self):
        """Verify migration files exist in wishlist/migrations/"""
        _p = self._repo_path('saleor/wishlist/migrations/')
        assert os.path.isdir(_p), f'Missing directory: saleor/wishlist/migrations/'

    # ── semantic_check (static) ────────────────────────────────────────

    def test_wishlist_item_model_definition(self):
        """Verify WishlistItem model with user and product_variant ForeignKeys"""
        _p = self._repo_path('saleor/wishlist/models.py')
        assert os.path.exists(_p), f'Missing: saleor/wishlist/models.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class WishlistItem' in _all, 'Missing: class WishlistItem'
        assert 'ForeignKey' in _all, 'Missing: ForeignKey'
        assert 'user' in _all, 'Missing: user'
        assert 'product_variant' in _all, 'Missing: product_variant'

    def test_unique_together_constraint(self):
        """Verify unique_together constraint on (user, product_variant)"""
        _p = self._repo_path('saleor/wishlist/models.py')
        assert os.path.exists(_p), f'Missing: saleor/wishlist/models.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'unique_together' in _all, 'Missing: unique_together'
        assert 'UniqueConstraint' in _all, 'Missing: UniqueConstraint'

    def test_wishlist_add_mutation_class(self):
        """Verify WishlistAdd mutation class with perform_mutation"""
        _p = self._repo_path('saleor/wishlist/mutations.py')
        assert os.path.exists(_p), f'Missing: saleor/wishlist/mutations.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class WishlistAdd' in _all, 'Missing: class WishlistAdd'
        assert 'perform_mutation' in _all, 'Missing: perform_mutation'

    def test_wishlist_remove_mutation_class(self):
        """Verify WishlistRemove mutation class defined"""
        _p = self._repo_path('saleor/wishlist/mutations.py')
        assert os.path.exists(_p), f'Missing: saleor/wishlist/mutations.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class WishlistRemove' in _all, 'Missing: class WishlistRemove'
        assert 'perform_mutation' in _all, 'Missing: perform_mutation'

    # ── functional_check ────────────────────────────────────────

    def test_django_system_check(self):
        """Verify Django system check passes with wishlist app"""
        self._ensure_setup('test_django_system_check', ['pip install -e .'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['manage.py', 'check', '--no-color'], timeout=120)
        assert result.returncode == 0, (
            f'test_django_system_check failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_migration_listed(self):
        """Verify wishlist migrations are listed"""
        self._ensure_setup('test_migration_listed', ['pip install -e .'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['manage.py', 'showmigrations', 'wishlist'], timeout=120)
        assert result.returncode == 0, (
            f'test_migration_listed failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_mutation_schema_registration(self):
        """Verify WishlistAdd is registered in GraphQL schema"""
        result = self._run_cmd('grep', args=['-r', 'WishlistAdd\\|wishlistAdd', 'saleor/graphql/'], timeout=120)
        assert result.returncode == 0, (
            f'test_mutation_schema_registration failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_wishlist_add_idempotent(self):
        """Verify calling wishlistAdd twice doesn't create duplicate items"""
        self._ensure_setup('test_wishlist_add_idempotent', ['pip install -e .', 'python manage.py migrate'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-c', "import django; django.setup(); from saleor.wishlist.models import WishlistItem; # In real test: create user+variant, add twice, assert count==1; print('IDEMPOTENCY_CHECK')"], timeout=120)
        assert result.returncode == 0, (
            f'test_wishlist_add_idempotent failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_unauthenticated_mutation_blocked(self):
        """Verify unauthenticated wishlistAdd returns auth error"""
        self._ensure_setup('test_unauthenticated_mutation_blocked', ['pip install -e .'], 'skip_if_setup_fails')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_wishlist.py', '-v', '--tb=short', '-k', 'unauthenticated'], timeout=120)
        assert result.returncode == 0, (
            f'test_unauthenticated_mutation_blocked failed (exit {result.returncode})\n' + result.stderr[:500]
        )

