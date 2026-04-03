"""
Test for 'springboot-tdd' skill — Spring PetClinic TDD
Validates Medication entity, JPQL queries, @NotBlank validation,
@PreAuthorize security, and test-driven development patterns.
"""

import os
import re

import pytest


class TestSpringbootTdd:
    """Verify Spring Boot TDD patterns in PetClinic."""

    REPO_DIR = "/workspace/spring-petclinic"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_java_source_exists(self):
        """Verify Java source directory exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".java"):
                    found = True
                    break
            if found:
                break
        assert found, "No Java source files found"

    def test_medication_entity_exists(self):
        """Verify Medication entity file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".java") and "medication" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No Medication entity file found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_entity_annotation(self):
        """Verify @Entity annotation on Medication."""
        java_files = self._find_java_files()
        for fpath in java_files:
            content = self._read(fpath)
            if "medication" in fpath.lower() or "Medication" in content:
                if "@Entity" in content:
                    return
        pytest.fail("No @Entity annotation on Medication")

    def test_jpql_queries(self):
        """Verify JPQL or @Query annotations."""
        java_files = self._find_java_files()
        for fpath in java_files:
            content = self._read(fpath)
            if re.search(
                r"(@Query|JPQL|@NamedQuery|createQuery|CriteriaBuilder)", content
            ):
                return
        pytest.fail("No JPQL/@Query found")

    def test_not_blank_validation(self):
        """Verify @NotBlank or @NotNull validation annotations."""
        java_files = self._find_java_files()
        for fpath in java_files:
            content = self._read(fpath)
            if re.search(r"(@NotBlank|@NotNull|@NotEmpty|@Valid)", content):
                return
        pytest.fail("No @NotBlank/@NotNull validation found")

    def test_preauthorize_security(self):
        """Verify @PreAuthorize or security annotations."""
        java_files = self._find_java_files()
        for fpath in java_files:
            content = self._read(fpath)
            if re.search(
                r"(@PreAuthorize|@Secured|@RolesAllowed|@EnableGlobalMethodSecurity)",
                content,
            ):
                return
        pytest.fail("No @PreAuthorize/security annotation found")

    def test_repository_pattern(self):
        """Verify Repository interface pattern."""
        java_files = self._find_java_files()
        for fpath in java_files:
            content = self._read(fpath)
            if re.search(
                r"(extends\s+(JpaRepository|CrudRepository|Repository)|@Repository)",
                content,
            ):
                return
        pytest.fail("No Repository pattern found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_build_file_exists(self):
        """Verify Maven/Gradle build file exists."""
        for bf in ["pom.xml", "build.gradle", "build.gradle.kts"]:
            if os.path.exists(os.path.join(self.REPO_DIR, bf)):
                return
        pytest.fail("No build file found")

    def test_test_files_exist(self):
        """Verify test files exist (TDD)."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".java") and ("test" in f.lower() or "Test" in f):
                    found = True
                    break
            if found:
                break
        assert found, "No test files found"

    def test_controller_layer(self):
        """Verify controller/REST endpoint layer."""
        java_files = self._find_java_files()
        for fpath in java_files:
            content = self._read(fpath)
            if re.search(
                r"(@Controller|@RestController|@RequestMapping|@GetMapping|@PostMapping)",
                content,
            ):
                return
        pytest.fail("No controller layer found")

    def test_service_layer(self):
        """Verify service layer with @Service."""
        java_files = self._find_java_files()
        for fpath in java_files:
            content = self._read(fpath)
            if re.search(r"(@Service|@Transactional)", content):
                return
        pytest.fail("No @Service layer found")

    def test_spring_boot_application(self):
        """Verify @SpringBootApplication entry point."""
        java_files = self._find_java_files()
        for fpath in java_files:
            content = self._read(fpath)
            if "@SpringBootApplication" in content:
                return
        pytest.fail("No @SpringBootApplication found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_java_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".java"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
