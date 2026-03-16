"""
Test for 'springboot-tdd' skill — Spring Boot TDD Workflow
Validates that the Agent added REST endpoints with TDD approach in the
Spring PetClinic application: controller, service, model, and tests.
"""

import os
import subprocess
import pytest


class TestSpringbootTdd:
    """Verify Spring Boot TDD implementation in PetClinic."""

    REPO_DIR = "/workspace/spring-petclinic"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_controller_exists(self):
        """A new controller Java file must exist."""
        src_dir = os.path.join(self.REPO_DIR, "src", "main", "java")
        found = []
        for root, dirs, files in os.walk(src_dir):
            for f in files:
                if f.endswith("Controller.java") and "Visit" in f:
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No Visit*Controller.java found"

    def test_service_exists(self):
        """A service class for the feature must exist."""
        src_dir = os.path.join(self.REPO_DIR, "src", "main", "java")
        found = []
        for root, dirs, files in os.walk(src_dir):
            for f in files:
                if f.endswith("Service.java") and "Visit" in f:
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No Visit*Service.java found"

    def test_test_file_exists(self):
        """Test class for the controller must exist."""
        test_dir = os.path.join(self.REPO_DIR, "src", "test", "java")
        found = []
        for root, dirs, files in os.walk(test_dir):
            for f in files:
                if "Visit" in f and f.endswith("Test.java"):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No Visit*Test.java found"

    # ------------------------------------------------------------------
    # L2: compilation & test execution
    # ------------------------------------------------------------------

    def test_maven_compile(self):
        """./mvnw compile must succeed."""
        result = subprocess.run(
            ["./mvnw", "compile", "-q", "-B"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert (
            result.returncode == 0
        ), f"Maven compile failed:\n{result.stdout[-2000:]}\n{result.stderr[-1000:]}"

    def test_maven_tests_pass(self):
        """./mvnw test must pass."""
        result = subprocess.run(
            ["./mvnw", "test", "-q", "-B"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert (
            result.returncode == 0
        ), f"Maven tests failed:\n{result.stdout[-2000:]}\n{result.stderr[-1000:]}"

    def test_controller_has_rest_annotations(self):
        """Controller must use Spring REST annotations."""
        src_dir = os.path.join(self.REPO_DIR, "src", "main", "java")
        for root, dirs, files in os.walk(src_dir):
            for f in files:
                if f.endswith("Controller.java") and "Visit" in f:
                    fpath = os.path.join(root, f)
                    with open(fpath, "r") as fh:
                        content = fh.read()
                    rest_annotations = [
                        "@RestController",
                        "@Controller",
                        "@GetMapping",
                        "@PostMapping",
                        "@RequestMapping",
                    ]
                    found = any(a in content for a in rest_annotations)
                    assert found, f"{f} missing REST annotations"
                    return
        pytest.fail("Controller file not found for annotation check")

    def test_service_has_transactional(self):
        """Service should use @Transactional or @Service."""
        src_dir = os.path.join(self.REPO_DIR, "src", "main", "java")
        for root, dirs, files in os.walk(src_dir):
            for f in files:
                if f.endswith("Service.java") and "Visit" in f:
                    fpath = os.path.join(root, f)
                    with open(fpath, "r") as fh:
                        content = fh.read()
                    annotations = ["@Service", "@Transactional", "@Component"]
                    found = any(a in content for a in annotations)
                    assert found, f"{f} missing Spring service annotations"
                    return

    def test_test_uses_spring_testing(self):
        """Test class must use Spring test annotations."""
        test_dir = os.path.join(self.REPO_DIR, "src", "test", "java")
        for root, dirs, files in os.walk(test_dir):
            for f in files:
                if "Visit" in f and f.endswith("Test.java"):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r") as fh:
                        content = fh.read()
                    annotations = [
                        "@SpringBootTest",
                        "@WebMvcTest",
                        "@MockBean",
                        "@DataJpaTest",
                        "@AutoConfigureMockMvc",
                        "@Test",
                    ]
                    found = sum(1 for a in annotations if a in content)
                    assert found >= 2, f"{f} needs Spring test annotations"
                    return

    def test_controller_has_validation(self):
        """Controller should validate inputs with @Valid or similar."""
        src_dir = os.path.join(self.REPO_DIR, "src", "main", "java")
        for root, dirs, files in os.walk(src_dir):
            for f in files:
                if f.endswith("Controller.java") and "Visit" in f:
                    fpath = os.path.join(root, f)
                    with open(fpath, "r") as fh:
                        content = fh.read()
                    validation = [
                        "@Valid",
                        "@NotNull",
                        "@NotBlank",
                        "@RequestBody",
                        "BindingResult",
                    ]
                    found = any(v in content for v in validation)
                    assert found, f"{f} missing input validation"
                    return

    def test_at_least_5_test_methods(self):
        """Test class must have at least 5 @Test methods."""
        test_dir = os.path.join(self.REPO_DIR, "src", "test", "java")
        for root, dirs, files in os.walk(test_dir):
            for f in files:
                if "Visit" in f and f.endswith("Test.java"):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r") as fh:
                        content = fh.read()
                    test_count = content.count("@Test")
                    assert (
                        test_count >= 5
                    ), f"{f} has only {test_count} @Test methods, need >= 5"
                    return
