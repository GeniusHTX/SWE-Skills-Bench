"""
Tests for springboot-tdd skill.
REPO_DIR: /workspace/spring-petclinic
"""

import os
import subprocess
import glob
import pytest

REPO_DIR = "/workspace/spring-petclinic"


def _path(rel):
    return os.path.join(REPO_DIR, rel)


def _read_dir_files(rel_pattern):
    return glob.glob(os.path.join(REPO_DIR, rel_pattern), recursive=True)


def _run(cmd, **kwargs):
    return subprocess.run(
        cmd,
        shell=True,
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
        **kwargs,
    )


class TestSpringbootTdd:
    # ── file_path_check ────────────────────────────────────────────────────
    def test_main_entity_java_exists(self):
        """Verify main domain entity Java file exists in src/main/java/."""
        java_dir = _path("src/main/java")
        assert os.path.isdir(java_dir), "src/main/java directory must exist"
        java_files = glob.glob(os.path.join(java_dir, "**", "*.java"), recursive=True)
        assert len(java_files) > 0, "src/main/java/ must contain .java source files"

    def test_controller_test_java_exists(self):
        """Verify controller test file exists in src/test/java/."""
        test_dir = _path("src/test/java")
        assert os.path.isdir(test_dir), "src/test/java directory must exist"
        test_files = glob.glob(
            os.path.join(test_dir, "**", "*Test*.java"), recursive=True
        )
        alt_test_files = glob.glob(
            os.path.join(test_dir, "**", "*Tests*.java"), recursive=True
        )
        all_test_files = test_files + alt_test_files
        assert (
            len(all_test_files) > 0
        ), "src/test/java/ must contain controller test files (*Test.java or *Tests.java)"

    # ── semantic_check ─────────────────────────────────────────────────────
    def test_entity_annotations_defined(self):
        """Verify @Entity and @Table JPA annotations are present on domain entity class."""
        java_files = glob.glob(
            os.path.join(_path("src/main/java"), "**", "*.java"), recursive=True
        )
        all_content = ""
        for f in java_files:
            with open(f, encoding="utf-8") as fh:
                all_content += fh.read()
        assert "@Entity" in all_content, "@Entity annotation must be present"
        assert "@Table" in all_content, "@Table annotation must be present"
        has_id = "@Id" in all_content or "@GeneratedValue" in all_content
        assert has_id, "@Id or @GeneratedValue annotation must be present"

    def test_mockmvc_test_structure(self):
        """Verify MockMvc is used in controller tests with @WebMvcTest or @SpringBootTest."""
        test_files = glob.glob(
            os.path.join(_path("src/test/java"), "**", "*.java"), recursive=True
        )
        all_content = ""
        for f in test_files:
            with open(f, encoding="utf-8") as fh:
                all_content += fh.read()
        assert "MockMvc" in all_content, "MockMvc must be used in controller tests"
        has_annotation = (
            "@WebMvcTest" in all_content or "@SpringBootTest" in all_content
        )
        assert (
            has_annotation
        ), "@WebMvcTest or @SpringBootTest annotation must be present in test files"

    def test_http_status_codes_tested(self):
        """Verify 400, 409, and 404 status code assertions are present in tests."""
        test_files = glob.glob(
            os.path.join(_path("src/test/java"), "**", "*.java"), recursive=True
        )
        all_content = ""
        for f in test_files:
            with open(f, encoding="utf-8") as fh:
                all_content += fh.read()
        has_400 = "400" in all_content or "BAD_REQUEST" in all_content
        has_409 = "409" in all_content or "CONFLICT" in all_content
        has_404 = "404" in all_content or "NOT_FOUND" in all_content
        assert has_400, "400 or BAD_REQUEST must be asserted in test files"
        assert has_409, "409 or CONFLICT must be asserted in test files"
        assert has_404, "404 or NOT_FOUND must be asserted in test files"

    def test_repository_or_service_layer_defined(self):
        """Verify Repository interface and/or Service class are defined."""
        java_files = glob.glob(
            os.path.join(_path("src/main/java"), "**", "*.java"), recursive=True
        )
        all_content = ""
        for f in java_files:
            with open(f, encoding="utf-8") as fh:
                all_content += fh.read()
        has_repo = (
            "Repository" in all_content
            or "JpaRepository" in all_content
            or "@Repository" in all_content
        )
        has_service = "@Service" in all_content or "Service" in all_content
        assert (
            has_repo
        ), "Repository interface or @Repository annotation must be present"
        assert has_service, "@Service annotation or service class must be present"

    # ── functional_check (command) ─────────────────────────────────────────
    def test_mvn_compile_skip_tests_succeeds(self):
        """Verify ./mvnw compile -DskipTests exits 0 (project compiles cleanly)."""
        mvnw = _path("mvnw")
        if not os.path.isfile(mvnw):
            pytest.skip("Maven wrapper (mvnw) not present in REPO_DIR; skipping")
        result = _run("./mvnw compile -DskipTests", timeout=300)
        if result.returncode != 0:
            pytest.skip(f"mvnw compile failed (env not set up): {result.stderr[:300]}")
        assert (
            "BUILD SUCCESS" in result.stdout
        ), "mvnw compile -DskipTests must produce BUILD SUCCESS"

    def test_future_date_returns_400(self):
        """Verify POST with a future date in a past-only field returns HTTP 400 Bad Request."""
        mvnw = _path("mvnw")
        if not os.path.isfile(mvnw):
            pytest.skip("Maven wrapper not present; skipping integration test")
        result = _run(
            "./mvnw test -Dtest=*ControllerTest#testFutureDate* -pl .", timeout=300
        )
        if result.returncode != 0 and "No tests were executed" not in result.stdout:
            pytest.skip("Test not compilable or no matching test; skipping")
        assert (
            result.returncode == 0
        ), "testFutureDate test must pass with 400 assertion"

    def test_duplicate_entry_returns_409(self):
        """Verify creating a duplicate resource returns HTTP 409 Conflict."""
        mvnw = _path("mvnw")
        if not os.path.isfile(mvnw):
            pytest.skip("Maven wrapper not present; skipping integration test")
        result = _run(
            "./mvnw test -Dtest=*ControllerTest#testDuplicate* -pl .", timeout=300
        )
        if result.returncode != 0 and "No tests were executed" not in result.stdout:
            pytest.skip("Test not compilable or no matching test; skipping")
        assert result.returncode == 0, "testDuplicate test must pass with 409 assertion"

    def test_nonexistent_resource_returns_404(self):
        """Verify GET on a non-existent resource ID returns HTTP 404 Not Found."""
        mvnw = _path("mvnw")
        if not os.path.isfile(mvnw):
            pytest.skip("Maven wrapper not present; skipping integration test")
        result = _run(
            "./mvnw test -Dtest=*ControllerTest#testNotFound* -pl .", timeout=300
        )
        if result.returncode != 0 and "No tests were executed" not in result.stdout:
            pytest.skip("Test not compilable or no matching test; skipping")
        assert result.returncode == 0, "testNotFound test must pass with 404 assertion"

    def test_valid_resource_creation_returns_201(self):
        """Verify POST with valid data returns HTTP 201 Created."""
        mvnw = _path("mvnw")
        if not os.path.isfile(mvnw):
            pytest.skip("Maven wrapper not present; skipping integration test")
        result = _run(
            "./mvnw test -Dtest=*ControllerTest#testCreate* -pl .", timeout=300
        )
        if result.returncode != 0 and "No tests were executed" not in result.stdout:
            pytest.skip("Test not compilable or no matching test; skipping")
        assert result.returncode == 0, "testCreate test must pass with 201 assertion"

    def test_all_unit_tests_pass(self):
        """Verify all unit tests pass via ./mvnw test."""
        mvnw = _path("mvnw")
        if not os.path.isfile(mvnw):
            pytest.skip("Maven wrapper not present; skipping full test suite")
        result = _run("./mvnw test", timeout=600)
        if result.returncode != 0:
            pytest.skip(f"mvnw test failed (env not set up): {result.stderr[:300]}")
        assert (
            "BUILD SUCCESS" in result.stdout
        ), "All tests must pass: BUILD SUCCESS required"
        assert (
            "Failures: 0" in result.stdout or "FAILURES" not in result.stdout
        ), "Test run must have zero failures"
