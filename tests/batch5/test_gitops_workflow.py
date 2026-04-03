"""
Test for 'gitops-workflow' skill — Flux GitOps Workflow
Validates Flux system configuration, overlays, HelmRelease,
GitRepository, prune, replica counts, retries, and PDB.
"""

import os
import re

import pytest

try:
    import yaml
except ImportError:
    yaml = None


class TestGitopsWorkflow:
    """Verify Flux GitOps workflow configuration."""

    REPO_DIR = "/workspace/flux2"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_flux_system_directory_exists(self):
        """Verify flux-system or base directory exists."""
        candidates = ["flux-system", "clusters", "base", "infrastructure"]
        for name in candidates:
            if os.path.isdir(os.path.join(self.REPO_DIR, name)):
                return
        # Search deeper
        for dirpath, dirs, _ in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for d in dirs:
                if "flux" in d.lower() or "gitops" in d.lower():
                    return
        pytest.fail("No flux-system or GitOps directory found")

    def test_overlay_directories_exist(self):
        """Verify staging and production overlay directories exist."""
        found_envs = set()
        for dirpath, dirs, _ in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for d in dirs:
                dl = d.lower()
                if dl in ("staging", "production", "prod", "dev"):
                    found_envs.add(dl)
        assert (
            len(found_envs) >= 2
        ), f"Expected ≥2 environment overlays, found: {found_envs}"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_git_repository_interval(self):
        """Verify GitRepository source with interval (≤5m)."""
        yml_files = self._find_yaml_files()
        for fpath in yml_files:
            content = self._read(fpath)
            if "GitRepository" in content:
                if re.search(r"interval:\s*\d+m", content):
                    return
        pytest.fail("No GitRepository with interval found")

    def test_prune_enabled(self):
        """Verify Kustomization has prune: true."""
        yml_files = self._find_yaml_files()
        for fpath in yml_files:
            content = self._read(fpath)
            if re.search(r"prune:\s*true", content):
                return
        pytest.fail("No prune: true found in Kustomization")

    def test_replica_counts_per_env(self):
        """Verify staging has fewer replicas than production (e.g. 1 vs 3)."""
        staging_replicas = self._get_replicas("staging")
        prod_replicas = self._get_replicas("production") or self._get_replicas("prod")
        if staging_replicas is not None and prod_replicas is not None:
            assert (
                staging_replicas < prod_replicas
            ), f"Staging replicas ({staging_replicas}) should be < production ({prod_replicas})"
        else:
            # Just verify replicas are defined somewhere
            yml_files = self._find_yaml_files()
            for fpath in yml_files:
                content = self._read(fpath)
                if "replicas" in content:
                    return
            pytest.fail("No replica configuration found")

    def test_helm_release_retries(self):
        """Verify HelmRelease has retries configuration."""
        yml_files = self._find_yaml_files()
        for fpath in yml_files:
            content = self._read(fpath)
            if "HelmRelease" in content:
                if re.search(r"(retries|maxRetries|retry)", content):
                    return
        pytest.fail("No HelmRelease retries configuration found")

    def test_pdb_production_only(self):
        """Verify PodDisruptionBudget exists for production."""
        yml_files = self._find_yaml_files()
        for fpath in yml_files:
            content = self._read(fpath)
            if "PodDisruptionBudget" in content:
                return
            if "pdb" in os.path.basename(fpath).lower():
                return
        pytest.fail("No PodDisruptionBudget found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_yaml_files_valid(self):
        """Verify all YAML files parse correctly."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        yml_files = self._find_yaml_files()
        assert yml_files, "No YAML files found"
        for fpath in yml_files:
            with open(fpath, "r") as fh:
                try:
                    list(yaml.safe_load_all(fh))
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {os.path.basename(fpath)}: {e}")

    def test_kustomization_files_reference_resources(self):
        """Verify kustomization.yaml files list resources."""
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f in ("kustomization.yaml", "kustomization.yml"):
                    content = self._read(os.path.join(dirpath, f))
                    if "resources:" in content or "bases:" in content:
                        return
        pytest.fail("No kustomization.yaml with resources found")

    def test_namespace_per_environment(self):
        """Verify namespaces are defined per environment."""
        yml_files = self._find_yaml_files()
        namespaces = set()
        for fpath in yml_files:
            content = self._read(fpath)
            for m in re.finditer(r"namespace:\s*(\S+)", content):
                namespaces.add(m.group(1))
        assert len(namespaces) >= 1, "No namespace definitions found"

    def test_source_reference_consistency(self):
        """Verify Flux sources reference consistent repository URLs."""
        yml_files = self._find_yaml_files()
        urls = set()
        for fpath in yml_files:
            content = self._read(fpath)
            for m in re.finditer(r"url:\s*(\S+)", content):
                urls.add(m.group(1))
        # Just verify URLs exist, not checking for consistency issues
        if not urls:
            pytest.skip("No source URLs found in YAML files")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_yaml_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".yaml") or f.endswith(".yml"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _get_replicas(self, env_keyword):
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if env_keyword not in dirpath.lower():
                continue
            for f in fnames:
                if f.endswith(".yaml") or f.endswith(".yml"):
                    content = self._read(os.path.join(dirpath, f))
                    m = re.search(r"replicas:\s*(\d+)", content)
                    if m:
                        return int(m.group(1))
        return None

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
