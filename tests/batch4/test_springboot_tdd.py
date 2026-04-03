"""
Test for 'springboot-tdd' skill — Visit Scheduling TDD
Validates that the Agent created VisitSchedulingService, Controller,
ScheduleVisitRequest, and corresponding tests for the Spring PetClinic project.
"""

import os

import pytest


class TestSpringbootTdd:
    """Verify Spring PetClinic visit scheduling TDD implementation."""

    REPO_DIR = "/workspace/spring-petclinic"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    # ---- file_path_check ----

    def test_visit_package_exists(self):
        """Verifies the visit package directory exists."""
        path = os.path.join(
            self.REPO_DIR,
            "src/main/java/org/springframework/samples/petclinic/visit",
        )
        assert os.path.exists(path), f"Expected path not found: {path}"

    def test_visitschedulingservice_java_exists(self):
        """Verifies VisitSchedulingService.java exists."""
        found = False
        for root, _dirs, files in os.walk(self.REPO_DIR):
            if "VisitSchedulingService.java" in files:
                found = True
                break
        assert found, "VisitSchedulingService.java not found anywhere in repo"

    def test_visitschedulecontroller_java_exists(self):
        """Verifies VisitScheduleController.java exists."""
        found = False
        for root, _dirs, files in os.walk(self.REPO_DIR):
            if "VisitScheduleController.java" in files:
                found = True
                break
        assert found, "VisitScheduleController.java not found anywhere in repo"

    def test_schedulevisitrequest_java_exists(self):
        """Verifies ScheduleVisitRequest.java exists."""
        found = False
        for root, _dirs, files in os.walk(self.REPO_DIR):
            if "ScheduleVisitRequest.java" in files:
                found = True
                break
        assert found, "ScheduleVisitRequest.java not found anywhere in repo"

    # ---- semantic_check ----

    def test_sem_service_file_readable(self):
        """Reads VisitSchedulingService.java from the visit package."""
        visit_dir = os.path.join(
            self.REPO_DIR,
            "src/main/java/org/springframework/samples/petclinic/visit",
        )
        svc = open(os.path.join(visit_dir, "VisitSchedulingService.java")).read()
        assert len(svc) > 0, "VisitSchedulingService.java is empty"

    def test_sem_schedule_method_present(self):
        """Verifies schedule() method exists in VisitSchedulingService."""
        visit_dir = os.path.join(
            self.REPO_DIR,
            "src/main/java/org/springframework/samples/petclinic/visit",
        )
        svc = open(os.path.join(visit_dir, "VisitSchedulingService.java")).read()
        assert (
            "schedule(" in svc
        ), "schedule() method not found in VisitSchedulingService"

    def test_sem_conflict_handling(self):
        """Verifies conflict (409) handling in VisitSchedulingService."""
        visit_dir = os.path.join(
            self.REPO_DIR,
            "src/main/java/org/springframework/samples/petclinic/visit",
        )
        svc = open(os.path.join(visit_dir, "VisitSchedulingService.java")).read()
        assert (
            "409" in svc or "Conflict" in svc or "ConflictException" in svc
        ), "Conflict handling not found"

    def test_sem_not_found_handling(self):
        """Verifies not-found (404) handling in VisitSchedulingService (edge case)."""
        visit_dir = os.path.join(
            self.REPO_DIR,
            "src/main/java/org/springframework/samples/petclinic/visit",
        )
        svc = open(os.path.join(visit_dir, "VisitSchedulingService.java")).read()
        assert (
            "404" in svc
            or "NotFoundException" in svc
            or "EntityNotFoundException" in svc
        ), "Not found handling missing"

    def test_sem_controller_file_readable(self):
        """Reads VisitScheduleController.java from the visit package."""
        visit_dir = os.path.join(
            self.REPO_DIR,
            "src/main/java/org/springframework/samples/petclinic/visit",
        )
        ctrl = open(os.path.join(visit_dir, "VisitScheduleController.java")).read()
        assert len(ctrl) > 0, "VisitScheduleController.java is empty"

    def test_sem_controller_post_mapping(self):
        """Verifies POST mapping annotation in controller."""
        visit_dir = os.path.join(
            self.REPO_DIR,
            "src/main/java/org/springframework/samples/petclinic/visit",
        )
        ctrl = open(os.path.join(visit_dir, "VisitScheduleController.java")).read()
        assert (
            "@PostMapping" in ctrl or "PostMapping" in ctrl
        ), "POST mapping missing in controller"

    # ---- functional_check ----

    def test_func_service_test_readable(self):
        """Reads VisitSchedulingServiceTest.java from test directory."""
        test_dir = os.path.join(
            self.REPO_DIR,
            "src/test/java/org/springframework/samples/petclinic/visit",
        )
        svc_test = open(
            os.path.join(test_dir, "VisitSchedulingServiceTest.java")
        ).read()
        assert len(svc_test) > 0, "VisitSchedulingServiceTest.java is empty"

    def test_func_service_test_has_test_annotations(self):
        """Verifies @Test annotations exist in VisitSchedulingServiceTest."""
        test_dir = os.path.join(
            self.REPO_DIR,
            "src/test/java/org/springframework/samples/petclinic/visit",
        )
        svc_test = open(
            os.path.join(test_dir, "VisitSchedulingServiceTest.java")
        ).read()
        assert "@Test" in svc_test, "No @Test annotations in VisitSchedulingServiceTest"

    def test_func_service_test_conflict_case(self):
        """Verifies conflict test case in VisitSchedulingServiceTest."""
        test_dir = os.path.join(
            self.REPO_DIR,
            "src/test/java/org/springframework/samples/petclinic/visit",
        )
        svc_test = open(
            os.path.join(test_dir, "VisitSchedulingServiceTest.java")
        ).read()
        assert (
            "conflict" in svc_test.lower() or "409" in svc_test
        ), "Conflict test case missing"

    def test_func_service_test_not_found_case(self):
        """Verifies 404 test case in VisitSchedulingServiceTest (failure scenario)."""
        test_dir = os.path.join(
            self.REPO_DIR,
            "src/test/java/org/springframework/samples/petclinic/visit",
        )
        svc_test = open(
            os.path.join(test_dir, "VisitSchedulingServiceTest.java")
        ).read()
        assert (
            "notFound" in svc_test.lower()
            or "404" in svc_test
            or "NotFoundException" in svc_test
        ), "404 test case missing"

    def test_func_controller_test_readable(self):
        """Reads VisitScheduleControllerTest.java from test directory."""
        test_dir = os.path.join(
            self.REPO_DIR,
            "src/test/java/org/springframework/samples/petclinic/visit",
        )
        ctrl_test = open(
            os.path.join(test_dir, "VisitScheduleControllerTest.java")
        ).read()
        assert len(ctrl_test) > 0, "VisitScheduleControllerTest.java is empty"

    def test_func_controller_test_uses_mockmvc(self):
        """Verifies MockMvc usage in controller test."""
        test_dir = os.path.join(
            self.REPO_DIR,
            "src/test/java/org/springframework/samples/petclinic/visit",
        )
        ctrl_test = open(
            os.path.join(test_dir, "VisitScheduleControllerTest.java")
        ).read()
        assert (
            "MockMvc" in ctrl_test or "WebMvcTest" in ctrl_test
        ), "MockMvc not used in controller test"

    def test_func_controller_test_201_status(self):
        """Verifies 201 status check in controller test."""
        test_dir = os.path.join(
            self.REPO_DIR,
            "src/test/java/org/springframework/samples/petclinic/visit",
        )
        ctrl_test = open(
            os.path.join(test_dir, "VisitScheduleControllerTest.java")
        ).read()
        assert (
            "status().isCreated()" in ctrl_test or "201" in ctrl_test
        ), "201 status not checked in controller test"

    def test_func_integration_test_readable(self):
        """Reads VisitSchedulingIntegrationTest.java from test directory."""
        test_dir = os.path.join(
            self.REPO_DIR,
            "src/test/java/org/springframework/samples/petclinic/visit",
        )
        int_test = open(
            os.path.join(test_dir, "VisitSchedulingIntegrationTest.java")
        ).read()
        assert len(int_test) > 0, "VisitSchedulingIntegrationTest.java is empty"
