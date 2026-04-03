"""
Test for 'springboot-tdd' skill — Spring Boot TDD Patterns
Validates Spring Boot test conventions: @WebMvcTest, @MockBean, @DataJpaTest,
@SpringBootTest with TestContainers, MockMvc assertions, and AssertJ usage
in the spring-petclinic project.
"""

import glob
import os
import re

import pytest


class TestSpringbootTdd:
    """Verify Spring Boot TDD patterns in spring-petclinic."""

    REPO_DIR = "/workspace/spring-petclinic"

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _glob_java(self, *subdirs: str, pattern: str = "*.java") -> list[str]:
        base = os.path.join(self.REPO_DIR, *subdirs)
        return glob.glob(os.path.join(base, "**", pattern), recursive=True)

    def _find_test_files(self, suffix: str) -> list[str]:
        """Find test files ending with given suffix under src/test/java/."""
        return [
            f for f in self._glob_java("src", "test", "java")
            if f.endswith(suffix)
        ]

    def _combined_test_content(self) -> str:
        """Concatenate all Java test files."""
        files = self._glob_java("src", "test", "java")
        return "\n".join(self._read_file(f) for f in files)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_controller_and_service_test_files_exist(self):
        """At least one *ControllerTest.java and *ServiceTest.java must exist."""
        ctrl = self._find_test_files("ControllerTest.java") or self._find_test_files("ControllerTests.java")
        svc = self._find_test_files("ServiceTest.java") or self._find_test_files("ServiceTests.java")
        assert ctrl, "No *ControllerTest(s).java found under src/test/java/"
        assert svc, "No *ServiceTest(s).java found under src/test/java/"

    def test_repository_and_integration_test_files_exist(self):
        """At least one *RepositoryTest.java and *IntegrationTest.java must exist."""
        repo_tests = self._find_test_files("RepositoryTest.java") or self._find_test_files("RepositoryTests.java")
        integ_tests = self._find_test_files("IntegrationTest.java") or self._find_test_files("IntegrationTests.java")
        assert repo_tests, "No *RepositoryTest(s).java found"
        assert integ_tests, "No *IntegrationTest(s).java found"

    def test_main_controller_and_build_file_exist(self):
        """A Controller.java must exist; pom.xml must declare spring-boot-starter-test."""
        controllers = [
            f for f in self._glob_java("src", "main", "java")
            if f.endswith("Controller.java")
        ]
        assert controllers, "No *Controller.java found under src/main/java/"
        pom = os.path.join(self.REPO_DIR, "pom.xml")
        build_gradle = os.path.join(self.REPO_DIR, "build.gradle")
        if os.path.isfile(pom):
            content = self._read_file(pom)
            assert "spring-boot-starter-test" in content, (
                "pom.xml missing spring-boot-starter-test"
            )
        elif os.path.isfile(build_gradle):
            content = self._read_file(build_gradle)
            assert "spring-boot-starter-test" in content, (
                "build.gradle missing spring-boot-starter-test"
            )
        else:
            pytest.fail("Neither pom.xml nor build.gradle found")

    # ── semantic_check ───────────────────────────────────────────────────

    def test_controller_test_has_webmvctest_annotation(self):
        """Controller test must use @WebMvcTest annotation."""
        files = self._find_test_files("ControllerTest.java") or self._find_test_files("ControllerTests.java")
        assert files, "No controller test file found"
        combined = "\n".join(self._read_file(f) for f in files)
        assert "@WebMvcTest" in combined, "@WebMvcTest annotation not found"

    def test_service_declared_as_mock_bean(self):
        """Controller test must use @MockBean for service dependency."""
        files = self._find_test_files("ControllerTest.java") or self._find_test_files("ControllerTests.java")
        assert files, "No controller test file found"
        combined = "\n".join(self._read_file(f) for f in files)
        assert "@MockBean" in combined, "@MockBean not found in controller test"

    def test_repository_test_has_datajpatest_annotation(self):
        """Repository test must use @DataJpaTest annotation."""
        files = self._find_test_files("RepositoryTest.java") or self._find_test_files("RepositoryTests.java")
        assert files, "No repository test file found"
        combined = "\n".join(self._read_file(f) for f in files)
        assert "@DataJpaTest" in combined, "@DataJpaTest annotation not found"

    def test_integration_test_uses_testcontainers(self):
        """Integration test must use PostgreSQLContainer / @Container / @SpringBootTest."""
        files = self._find_test_files("IntegrationTest.java") or self._find_test_files("IntegrationTests.java")
        assert files, "No integration test file found"
        combined = "\n".join(self._read_file(f) for f in files)
        assert "@SpringBootTest" in combined, "@SpringBootTest not found"
        has_tc = "PostgreSQLContainer" in combined or "@Container" in combined or "Testcontainers" in combined
        assert has_tc, "TestContainers (PostgreSQLContainer/@Container) not found"

    # ── functional_check (static content verification) ───────────────────

    def test_mockmvc_get_items_returns_200(self):
        """Controller test must verify MockMvc GET with status().isOk()."""
        combined = self._combined_test_content()
        assert "mockMvc" in combined or "MockMvc" in combined, "MockMvc not used"
        assert "isOk" in combined or "status().isOk()" in combined, (
            "isOk() assertion not found in controller tests"
        )

    def test_post_valid_body_expects_201_and_location_header(self):
        """Controller test must verify POST returns 201 Created."""
        combined = self._combined_test_content()
        has_created = "isCreated" in combined or "201" in combined
        assert has_created, "isCreated()/201 assertion not found in tests"

    def test_invalid_post_body_expects_400(self):
        """Controller test must verify invalid POST returns 400 Bad Request."""
        combined = self._combined_test_content()
        has_bad = "isBadRequest" in combined or "400" in combined
        assert has_bad, "isBadRequest()/400 assertion not found"

    def test_get_nonexistent_item_expects_404(self):
        """Controller test must verify GET nonexistent resource returns 404."""
        combined = self._combined_test_content()
        has_notfound = "isNotFound" in combined or "404" in combined
        assert has_notfound, "isNotFound()/404 assertion not found"

    def test_assertj_assertions_used_across_tests(self):
        """AssertJ assertThat() must be used in at least one test class."""
        combined = self._combined_test_content()
        assert "assertThat" in combined, "assertThat() (AssertJ) not used in any test"
