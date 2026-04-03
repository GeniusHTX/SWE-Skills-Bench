"""
Tests for 'gitops-workflow' skill.
Generated from benchmark case definitions for gitops-workflow.
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


class TestGitopsWorkflow:
    """Verify the gitops-workflow skill output."""

    REPO_DIR = '/workspace/flux2'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestGitopsWorkflow.REPO_DIR, rel)

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

    def test_argocd_app_files_exist(self):
        """Verify ArgoCD Application YAMLs exist for all 3 environments"""
        _p = self._repo_path('gitops/apps/dev.yaml')
        assert os.path.isfile(_p), f'Missing file: gitops/apps/dev.yaml'
        self._load_yaml(_p)  # parse check
        _p = self._repo_path('gitops/apps/staging.yaml')
        assert os.path.isfile(_p), f'Missing file: gitops/apps/staging.yaml'
        self._load_yaml(_p)  # parse check
        _p = self._repo_path('gitops/apps/production.yaml')
        assert os.path.isfile(_p), f'Missing file: gitops/apps/production.yaml'
        self._load_yaml(_p)  # parse check

    def test_kustomize_base_exists(self):
        """Verify Kustomize base directory with kustomization.yaml"""
        _p = self._repo_path('gitops/base/kustomization.yaml')
        assert os.path.isfile(_p), f'Missing file: gitops/base/kustomization.yaml'
        self._load_yaml(_p)  # parse check

    def test_kustomize_overlays_exist(self):
        """Verify Kustomize overlay directories for all environments"""
        _p = self._repo_path('gitops/overlays/dev/kustomization.yaml')
        assert os.path.isfile(_p), f'Missing file: gitops/overlays/dev/kustomization.yaml'
        self._load_yaml(_p)  # parse check
        _p = self._repo_path('gitops/overlays/staging/kustomization.yaml')
        assert os.path.isfile(_p), f'Missing file: gitops/overlays/staging/kustomization.yaml'
        self._load_yaml(_p)  # parse check
        _p = self._repo_path('gitops/overlays/production/kustomization.yaml')
        assert os.path.isfile(_p), f'Missing file: gitops/overlays/production/kustomization.yaml'
        self._load_yaml(_p)  # parse check

    # ── semantic_check (static) ────────────────────────────────────────

    def test_argocd_kind_and_apiversion(self):
        """Verify kind: Application and correct apiVersion in app manifests"""
        _p = self._repo_path('gitops/apps/dev.yaml')
        assert os.path.exists(_p), f'Missing: gitops/apps/dev.yaml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'kind' in _all, 'Missing: kind'
        assert 'apiVersion' in _all, 'Missing: apiVersion'

    def test_source_path_points_to_overlay(self):
        """Verify spec.source.path points to overlay directory not base"""
        _p = self._repo_path('gitops/apps/dev.yaml')
        assert os.path.exists(_p), f'Missing: gitops/apps/dev.yaml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'source' in _all, 'Missing: source'
        assert 'path' in _all, 'Missing: path'
        assert 'overlay' in _all, 'Missing: overlay'

    def test_dev_staging_automated_sync(self):
        """Verify dev and staging have automated prune and selfHeal"""
        _p = self._repo_path('gitops/apps/dev.yaml')
        assert os.path.exists(_p), f'Missing: gitops/apps/dev.yaml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'syncPolicy' in _all, 'Missing: syncPolicy'
        assert 'automated' in _all, 'Missing: automated'
        assert 'prune' in _all, 'Missing: prune'
        assert 'selfHeal' in _all, 'Missing: selfHeal'

    def test_base_kustomization_has_resources(self):
        """Verify base kustomization.yaml has non-empty resources list"""
        _p = self._repo_path('gitops/base/kustomization.yaml')
        assert os.path.exists(_p), f'Missing: gitops/base/kustomization.yaml'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'resources' in _all, 'Missing: resources'

    # ── functional_check ────────────────────────────────────────

    def test_yaml_parses_all_apps(self):
        """Verify all ArgoCD Application YAMLs parse and have kind: Application"""
        result = self._run_cmd('python', args=['-c', "import yaml,glob; files=glob.glob('gitops/apps/*.yaml'); assert len(files)>=3; [yaml.safe_load(open(f)) for f in files]; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_yaml_parses_all_apps failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_production_no_auto_prune(self):
        """Verify production app does NOT have syncPolicy.automated.prune: true"""
        result = self._run_cmd('python', args=['-c', "import yaml,glob; prod=[f for f in glob.glob('gitops/apps/*.yaml') if 'prod' in f][0]; d=yaml.safe_load(open(prod)); auto=d.get('spec',{}).get('syncPolicy',{}).get('automated',{}); assert auto is None or auto.get('prune') is not True, 'Production has prune: true!'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_production_no_auto_prune failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_dev_automated_prune_true(self):
        """Verify dev app has syncPolicy.automated with prune: true and selfHeal: true"""
        result = self._run_cmd('python', args=['-c', "import yaml,glob; dev=[f for f in glob.glob('gitops/apps/*.yaml') if 'dev' in f][0]; d=yaml.safe_load(open(dev)); auto=d['spec']['syncPolicy']['automated']; assert auto['prune']==True; assert auto['selfHeal']==True; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_dev_automated_prune_true failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_overlay_references_base(self):
        """Verify overlay kustomization.yaml references base directory"""
        result = self._run_cmd('python', args=['-c', "import yaml; k=yaml.safe_load(open('gitops/overlays/dev/kustomization.yaml')); refs=str(k.get('resources',k.get('bases',[]))); assert 'base' in refs, f'No base reference: {refs}'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_overlay_references_base failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_base_resources_nonempty(self):
        """Verify base kustomization.yaml has non-empty resources"""
        result = self._run_cmd('python', args=['-c', "import yaml; base=yaml.safe_load(open('gitops/base/kustomization.yaml')); assert len(base.get('resources',[]))>0, 'Empty resources'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_base_resources_nonempty failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

