"""
Test for 'github-actions-templates' skill — GitHub Actions Workflow Templates
Validates that the Agent created reusable workflow YAML templates with
properties JSON metadata files the starter-workflows repo expects.
"""

import os
import json
import pytest


class TestGithubActionsTemplates:
    """Verify GitHub Actions reusable workflow templates."""

    REPO_DIR = "/workspace/starter-workflows"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_ci_workflow_exists(self):
        """ci/ directory must contain at least one new workflow."""
        ci_dir = os.path.join(self.REPO_DIR, "ci")
        assert os.path.isdir(ci_dir), "ci/ directory not found"
        yamls = [f for f in os.listdir(ci_dir) if f.endswith((".yml", ".yaml"))]
        assert len(yamls) >= 1, "No workflow YAML in ci/"

    def test_properties_json_exists(self):
        """Each workflow in ci/ must have a matching .properties.json."""
        ci_dir = os.path.join(self.REPO_DIR, "ci")
        yamls = [f for f in os.listdir(ci_dir) if f.endswith((".yml", ".yaml"))]
        for yml in yamls:
            base = os.path.splitext(yml)[0]
            props = os.path.join(ci_dir, base + ".properties.json")
            assert os.path.isfile(props), f"Missing {base}.properties.json"

    # ------------------------------------------------------------------
    # L2: workflow YAML validation
    # ------------------------------------------------------------------

    def _get_workflow_files(self):
        """Get all workflow YAML files in ci/."""
        ci_dir = os.path.join(self.REPO_DIR, "ci")
        return [
            os.path.join(ci_dir, f)
            for f in os.listdir(ci_dir)
            if f.endswith((".yml", ".yaml"))
        ]

    def test_workflows_are_valid_yaml(self):
        """All workflow files must be valid YAML."""
        import yaml

        for fpath in self._get_workflow_files():
            with open(fpath, "r") as f:
                doc = yaml.safe_load(f)
            assert isinstance(doc, dict), f"{fpath} is not a YAML mapping"

    def test_workflows_have_on_trigger(self):
        """Workflow must define trigger events (on:)."""
        import yaml

        for fpath in self._get_workflow_files():
            with open(fpath, "r") as f:
                doc = yaml.safe_load(f)
            assert "on" in doc or True in doc, f"Workflow {fpath} missing 'on' trigger"

    def test_workflows_have_jobs(self):
        """Each workflow must define jobs."""
        import yaml

        for fpath in self._get_workflow_files():
            with open(fpath, "r") as f:
                doc = yaml.safe_load(f)
            assert "jobs" in doc, f"Workflow {fpath} missing 'jobs'"
            assert len(doc["jobs"]) >= 1, f"Workflow {fpath} has 0 jobs"

    def test_jobs_have_runs_on(self):
        """Each job must specify runs-on."""
        import yaml

        for fpath in self._get_workflow_files():
            with open(fpath, "r") as f:
                doc = yaml.safe_load(f)
            for job_name, job_body in doc.get("jobs", {}).items():
                assert (
                    "runs-on" in job_body
                ), f"Job '{job_name}' in {fpath} missing runs-on"

    def test_jobs_have_steps(self):
        """Each job must have at least one step."""
        import yaml

        for fpath in self._get_workflow_files():
            with open(fpath, "r") as f:
                doc = yaml.safe_load(f)
            for job_name, job_body in doc.get("jobs", {}).items():
                steps = job_body.get("steps", [])
                assert len(steps) >= 1, f"Job '{job_name}' in {fpath} has no steps"

    def test_properties_json_valid(self):
        """Properties JSON must be valid and have required fields."""
        ci_dir = os.path.join(self.REPO_DIR, "ci")
        yamls = [f for f in os.listdir(ci_dir) if f.endswith((".yml", ".yaml"))]
        for yml in yamls:
            base = os.path.splitext(yml)[0]
            props_path = os.path.join(ci_dir, base + ".properties.json")
            if os.path.isfile(props_path):
                with open(props_path, "r") as f:
                    props = json.load(f)
                assert isinstance(props, dict), f"{props_path} is not a JSON object"
                assert "name" in props, f"{props_path} missing 'name'"

    def test_uses_actions_checkout(self):
        """At least one workflow must use actions/checkout."""
        import yaml

        found = False
        for fpath in self._get_workflow_files():
            with open(fpath, "r") as f:
                content = f.read()
            if "actions/checkout" in content:
                found = True
                break
        assert found, "No workflow uses actions/checkout"

    def test_workflow_name_field(self):
        """Workflows must have a name field."""
        import yaml

        for fpath in self._get_workflow_files():
            with open(fpath, "r") as f:
                doc = yaml.safe_load(f)
            assert "name" in doc, f"Workflow {fpath} missing 'name'"
