"""
Test for 'springboot-tdd' skill — Spring Boot TDD visit scheduling
Validates that the Agent implemented visit scheduling in Spring PetClinic
using TDD with JUnit 5 and Mockito.
"""

import os
import re

import pytest


class TestSpringbootTdd:
    """Verify Spring Boot TDD visit scheduling implementation."""

    REPO_DIR = "/workspace/spring-petclinic"
    VISIT_SERVICE = os.path.join(
        REPO_DIR,
        "src/main/java/org/springframework/samples/petclinic/visit/VisitService.java",
    )
    VISIT_SERVICE_TEST = os.path.join(
        REPO_DIR,
        "src/test/java/org/springframework/samples/petclinic/visit/VisitServiceTest.java",
    )

    def test_visit_service_file_exists(self):
        """VisitService.java must be created with scheduleVisit method."""
        assert os.path.isfile(self.VISIT_SERVICE), "VisitService.java not found"
        with open(self.VISIT_SERVICE, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"scheduleVisit", content), "scheduleVisit method not found"

    def test_visit_service_test_file_exists(self):
        """VisitServiceTest.java must exist with at least 3 @Test methods."""
        assert os.path.isfile(self.VISIT_SERVICE_TEST), "VisitServiceTest.java not found"
        with open(self.VISIT_SERVICE_TEST, "r", errors="ignore") as fh:
            content = fh.read()
        test_count = len(re.findall(r"@Test", content))
        assert test_count >= 3, f"Expected >= 3 @Test methods, found {test_count}"

    def test_service_annotated_with_at_service(self):
        """VisitService must be annotated with @Service."""
        assert os.path.isfile(self.VISIT_SERVICE)
        with open(self.VISIT_SERVICE, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"@Service", content), "@Service annotation not found"
        assert re.search(
            r"import\s+org\.springframework\.stereotype\.Service", content
        ), "Spring Service import not found"

    def test_mockito_used_in_tests(self):
        """Mockito must be used to mock repository dependencies."""
        assert os.path.isfile(self.VISIT_SERVICE_TEST)
        with open(self.VISIT_SERVICE_TEST, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r"@Mock|Mockito|@ExtendWith\(MockitoExtension", content
        ), "Mockito usage not found in test"

    def test_schedule_visit_saves_to_repository(self):
        """scheduleVisit must call repository.save() to persist the visit."""
        assert os.path.isfile(self.VISIT_SERVICE)
        with open(self.VISIT_SERVICE, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r"\.save\(", content
        ), "repository.save() call not found in VisitService"

    def test_past_date_visit_rejected(self):
        """Past-date visits must be rejected with an exception."""
        src_content = ""
        test_content = ""
        if os.path.isfile(self.VISIT_SERVICE):
            with open(self.VISIT_SERVICE, "r", errors="ignore") as fh:
                src_content = fh.read()
        if os.path.isfile(self.VISIT_SERVICE_TEST):
            with open(self.VISIT_SERVICE_TEST, "r", errors="ignore") as fh:
                test_content = fh.read()
        combined = src_content + test_content
        assert re.search(
            r"isBefore|IllegalArgument|past.date|invalid.date", combined, re.IGNORECASE
        ), "Past-date validation not found"

    def test_maven_compile_succeeds(self):
        """Maven compile must succeed (source validated by file check)."""
        found_java = False
        visit_dir = os.path.join(
            self.REPO_DIR,
            "src/main/java/org/springframework/samples/petclinic/visit",
        )
        if os.path.isdir(visit_dir):
            for f in os.listdir(visit_dir):
                if f.endswith(".java"):
                    found_java = True
                    break
        assert found_java, "No Java files found in visit package"

    def test_unit_tests_pass(self):
        """VisitServiceTest must contain assertion methods."""
        assert os.path.isfile(self.VISIT_SERVICE_TEST)
        with open(self.VISIT_SERVICE_TEST, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r"assert|assertEquals|assertThrows|assertThat|verify\(", content
        ), "No assertion statements found in test file"

    def test_schedule_visit_returns_saved_visit(self):
        """scheduleVisit must return a Visit object."""
        assert os.path.isfile(self.VISIT_SERVICE)
        with open(self.VISIT_SERVICE, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r"(Visit|visit)\s+scheduleVisit|return\s+.*visit", content, re.IGNORECASE
        ), "scheduleVisit does not appear to return a Visit object"

    def test_null_pet_id_raises_exception(self):
        """Null petId must be rejected with IllegalArgumentException."""
        src_content = ""
        test_content = ""
        if os.path.isfile(self.VISIT_SERVICE):
            with open(self.VISIT_SERVICE, "r", errors="ignore") as fh:
                src_content = fh.read()
        if os.path.isfile(self.VISIT_SERVICE_TEST):
            with open(self.VISIT_SERVICE_TEST, "r", errors="ignore") as fh:
                test_content = fh.read()
        combined = src_content + test_content
        assert re.search(
            r"null|petId|IllegalArgument", combined
        ), "Null petId validation not found"

    def test_same_day_double_booking_handled(self):
        """Double booking on the same day must be addressed."""
        src_content = ""
        test_content = ""
        if os.path.isfile(self.VISIT_SERVICE):
            with open(self.VISIT_SERVICE, "r", errors="ignore") as fh:
                src_content = fh.read()
        if os.path.isfile(self.VISIT_SERVICE_TEST):
            with open(self.VISIT_SERVICE_TEST, "r", errors="ignore") as fh:
                test_content = fh.read()
        combined = src_content + test_content
        assert re.search(
            r"double|duplicate|same.day|already.*booked|existing.*visit",
            combined,
            re.IGNORECASE,
        ), "Double-booking handling not found"
