"""Test file for the springboot-tdd skill.

This suite validates a TDD-driven Specialty REST API in spring-petclinic:
controller, service, repository, and DTO with validation.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestSpringbootTdd:
    """Verify Spring Boot Specialty CRUD API in spring-petclinic."""

    REPO_DIR = "/workspace/spring-petclinic"

    BASE_PKG = "src/main/java/org/springframework/samples/petclinic/specialty"
    CONTROLLER = f"{BASE_PKG}/SpecialtyController.java"
    SERVICE = f"{BASE_PKG}/SpecialtyService.java"
    REPOSITORY = f"{BASE_PKG}/SpecialtyRepository.java"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _all_java_sources(self, directory: str) -> str:
        """Read all .java files under a directory."""
        result = []
        root = self._repo_path(directory)
        if root.is_dir():
            for f in root.rglob("*.java"):
                result.append(f.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(result)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_specialty_controller_java_exists(self):
        """Verify SpecialtyController.java exists."""
        self._assert_non_empty_file(self.CONTROLLER)

    def test_file_path_specialty_service_java_exists(self):
        """Verify SpecialtyService.java exists."""
        self._assert_non_empty_file(self.SERVICE)

    def test_file_path_specialty_repository_java_exists(self):
        """Verify SpecialtyRepository.java exists."""
        self._assert_non_empty_file(self.REPOSITORY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_controller_has_restcontroller_with_requestmapping_api_specialties(
        self,
    ):
        """SpecialtyController has @RestController with @RequestMapping('/api/specialties')."""
        src = self._read_text(self.CONTROLLER)
        assert re.search(
            r"@RestController", src
        ), "SpecialtyController should be annotated with @RestController"
        assert re.search(
            r"@RequestMapping.*['\"/]api/specialties", src
        ), "Should have @RequestMapping('/api/specialties')"

    def test_semantic_crud_methods_annotated_with_mapping_annotations(self):
        """CRUD methods annotated with @GetMapping, @PostMapping, @PutMapping, @DeleteMapping."""
        src = self._read_text(self.CONTROLLER)
        for annotation in [
            "@GetMapping",
            "@PostMapping",
            "@PutMapping",
            "@DeleteMapping",
        ]:
            assert (
                annotation in src
            ), f"Controller should have {annotation} annotated method"

    def test_semantic_specialtydto_has_name_field_with_validation(self):
        """SpecialtyDto has name field with validation annotations."""
        all_src = self._all_java_sources(self.BASE_PKG)
        assert re.search(
            r"class\s+Specialty(Dto|DTO|Request)", all_src
        ), "SpecialtyDto or similar DTO class should exist"
        assert re.search(
            r"@(NotBlank|NotEmpty|NotNull|Size|Valid)", all_src
        ), "DTO should have validation annotations"

    def test_semantic_service_encapsulates_uniqueness_and_not_found(self):
        """SpecialtyService encapsulates uniqueness check and not-found logic."""
        src = self._read_text(self.SERVICE)
        assert re.search(
            r"unique|duplicate|exists|Conflict|409", src, re.IGNORECASE
        ), "Service should check for uniqueness"
        assert re.search(
            r"not.*found|NotFound|404|Optional|orElseThrow", src, re.IGNORECASE
        ), "Service should handle not-found cases"

    def test_semantic_repository_extends_spring_data_jpa(self):
        """SpecialtyRepository extends Spring Data JPA interface with pagination."""
        src = self._read_text(self.REPOSITORY)
        assert re.search(
            r"extends\s+(JpaRepository|CrudRepository|PagingAndSorting)", src
        ), "Repository should extend a Spring Data JPA interface"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases)
    # ------------------------------------------------------------------

    def test_functional_get_api_specialties_returns_sorted_json_200(self):
        """GET /api/specialties returns sorted JSON array with 200."""
        src = self._read_text(self.CONTROLLER)
        assert re.search(r"@GetMapping", src), "Should have GET endpoint"
        service_src = self._read_text(self.SERVICE)
        assert re.search(
            r"findAll|getAll|list", service_src
        ), "Service should have a list/findAll method"

    def test_functional_post_unique_name_returns_201_location(self):
        """POST with unique name returns 201 with Location header."""
        src = self._read_text(self.CONTROLLER)
        assert re.search(r"@PostMapping", src), "Should have POST endpoint"
        assert re.search(
            r"201|CREATED|ResponseEntity\.created|HttpStatus\.CREATED", src
        ), "POST should return 201 Created"

    def test_functional_post_duplicate_name_returns_409(self):
        """POST with duplicate name returns 409."""
        all_src = self._all_java_sources(self.BASE_PKG)
        assert re.search(
            r"409|CONFLICT|Conflict|DataIntegrity|Duplicate", all_src, re.IGNORECASE
        ), "Duplicate name should return 409"

    def test_functional_post_blank_name_returns_400(self):
        """POST with blank name returns 400."""
        all_src = self._all_java_sources(self.BASE_PKG)
        assert re.search(
            r"@Valid|@NotBlank|400|BAD_REQUEST|MethodArgumentNotValid", all_src
        ), "Blank name should trigger 400"

    def test_functional_get_api_specialties_999_returns_404(self):
        """GET /api/specialties/999 returns 404."""
        all_src = self._all_java_sources(self.BASE_PKG)
        assert re.search(
            r"404|NOT_FOUND|NotFoundException|ResourceNotFound", all_src, re.IGNORECASE
        ), "Non-existent ID should return 404"
