"""
Test for 'springboot-tdd' skill — Spring Boot TDD Appointment API
Validates that the Agent implemented a Spring Boot appointment REST API
with Controller, Service, Repository, time conflict detection, and MockMvc tests.
"""

import os
import re
import subprocess
import glob as globmod

import pytest


class TestSpringbootTdd:
    """Verify Spring Boot TDD appointment API implementation."""

    REPO_DIR = "/workspace/spring-petclinic"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _glob(self, pattern: str):
        return globmod.glob(os.path.join(self.REPO_DIR, pattern), recursive=True)

    # ── file_path_check ─────────────────────────────────────────────

    def test_appointment_controller_exists(self):
        """Verify AppointmentController.java exists under src/main/java."""
        matches = self._glob("src/main/java/**/AppointmentController.java")
        assert matches, "Missing: AppointmentController.java"

    def test_appointment_service_exists(self):
        """Verify AppointmentService.java exists under src/main/java."""
        matches = self._glob("src/main/java/**/AppointmentService.java")
        assert matches, "Missing: AppointmentService.java"

    def test_appointment_repository_exists(self):
        """Verify AppointmentRepository.java and Appointment.java entity exist."""
        repo_matches = self._glob("src/main/java/**/AppointmentRepository.java")
        entity_matches = self._glob("src/main/java/**/Appointment.java")
        assert repo_matches, "Missing: AppointmentRepository.java"
        assert entity_matches, "Missing: Appointment.java"

    def test_test_class_exists(self):
        """Verify test class exists under src/test."""
        matches = (
            self._glob("src/test/java/**/AppointmentControllerTest.java")
            or self._glob("src/test/java/**/AppointmentServiceTest.java"))
        assert matches, "Missing: Test class for Appointment"

    # ── semantic_check ──────────────────────────────────────────────

    def test_rest_controller_annotation(self):
        """Verify @RestController and @RequestMapping annotations present."""
        matches = self._glob("src/main/java/**/AppointmentController.java")
        assert matches, "Controller not found"
        content = self._read(matches[0])
        assert "@RestController" in content, "@RestController not found"
        assert "@RequestMapping" in content, "@RequestMapping not found"

    def test_jpa_repository_extension(self):
        """Verify AppointmentRepository extends JpaRepository."""
        matches = self._glob("src/main/java/**/AppointmentRepository.java")
        assert matches, "Repository not found"
        content = self._read(matches[0])
        assert "JpaRepository" in content, "JpaRepository not found"

    def test_conflict_detection_in_service(self):
        """Verify AppointmentService checks for time conflicts before saving."""
        matches = self._glob("src/main/java/**/AppointmentService.java")
        assert matches, "Service not found"
        content = self._read(matches[0])
        found = any(kw in content for kw in (
            "conflict", "Conflict", "AppointmentConflictException"))
        assert found, "Conflict detection not found in service"

    def test_web_mvc_test_setup(self):
        """Verify test class uses @WebMvcTest or @SpringBootTest with MockMvc."""
        matches = (
            self._glob("src/test/java/**/AppointmentControllerTest.java")
            or self._glob("src/test/java/**/AppointmentServiceTest.java"))
        assert matches, "Test class not found"
        content = self._read(matches[0])
        found = any(kw in content for kw in (
            "@WebMvcTest", "@SpringBootTest", "MockMvc"))
        assert found, "MockMvc or test annotations not found"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_repo(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")

    def test_post_returns_201_created(self):
        """MockMvc POST /api/appointments with valid body returns 201."""
        self._skip_unless_repo()
        result = subprocess.run(
            ["./mvnw", "test", "-pl", ".",
             "-Dtest=AppointmentControllerTest#testCreateAppointmentReturns201"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=300,
        )
        assert result.returncode == 0, f"Test failed: {result.stderr}"

    def test_get_nonexistent_returns_404(self):
        """MockMvc GET /api/appointments/999 returns 404."""
        self._skip_unless_repo()
        result = subprocess.run(
            ["./mvnw", "test", "-pl", ".",
             "-Dtest=AppointmentControllerTest#testGetMissingAppointmentReturns404"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=300,
        )
        assert result.returncode == 0, f"Test failed: {result.stderr}"

    def test_post_missing_patient_returns_400(self):
        """MockMvc POST missing required 'patient' field returns 400."""
        self._skip_unless_repo()
        result = subprocess.run(
            ["./mvnw", "test", "-pl", ".",
             "-Dtest=AppointmentControllerTest#testCreateWithMissingPatientReturns400"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=300,
        )
        assert result.returncode == 0, f"Test failed: {result.stderr}"
