"""
Test for 'springboot-tdd' skill — Pet Weight Tracking Feature
Validates that the Agent created a weight tracking feature for Spring PetClinic
with JPA entity, repository, controller, schema, and TDD tests.
"""

import os
import re
import subprocess

import pytest


class TestSpringbootTdd:
    """Verify Spring PetClinic pet weight tracking feature."""

    REPO_DIR = "/workspace/spring-petclinic"
    WEIGHT_PKG = "src/main/java/org/springframework/samples/petclinic/weight"
    TEST_PKG = "src/test/java/org/springframework/samples/petclinic/weight"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_weight_record_entity_exists(self):
        """WeightRecord.java entity must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.WEIGHT_PKG, "WeightRecord.java")
        )

    def test_weight_repository_exists(self):
        """WeightRepository.java must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.WEIGHT_PKG, "WeightRepository.java")
        )

    def test_weight_controller_exists(self):
        """WeightController.java must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.WEIGHT_PKG, "WeightController.java")
        )

    def test_weight_tests_exist(self):
        """WeightControllerTests.java must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.TEST_PKG, "WeightControllerTests.java")
        )

    # ------------------------------------------------------------------
    # L1: Entity structure
    # ------------------------------------------------------------------

    def test_entity_has_jpa_annotations(self):
        """WeightRecord.java must use JPA annotations."""
        content = self._read(self.WEIGHT_PKG, "WeightRecord.java")
        patterns = [r"@Entity", r"@Table", r"@Id"]
        found = sum(1 for p in patterns if re.search(p, content))
        assert found >= 2, "WeightRecord missing JPA annotations"

    def test_entity_has_weight_field(self):
        """Entity must have a weight value field."""
        content = self._read(self.WEIGHT_PKG, "WeightRecord.java")
        patterns = [r"weight", r"value", r"Double|double|BigDecimal|float"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "WeightRecord has no weight value field"

    def test_entity_has_unit_field(self):
        """Entity must have a unit of measurement field."""
        content = self._read(self.WEIGHT_PKG, "WeightRecord.java")
        patterns = [r"unit", r"Unit", r"measurement"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "WeightRecord has no unit field"

    def test_entity_has_date_field(self):
        """Entity must have a measurement date field."""
        content = self._read(self.WEIGHT_PKG, "WeightRecord.java")
        patterns = [
            r"date",
            r"Date",
            r"LocalDate",
            r"Instant",
            r"timestamp",
            r"measuredAt",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "WeightRecord has no date field"

    def test_entity_references_pet(self):
        """Entity must reference Pet entity."""
        content = self._read(self.WEIGHT_PKG, "WeightRecord.java")
        patterns = [r"Pet\s", r"@ManyToOne", r"pet_id", r"petId"]
        assert any(
            re.search(p, content) for p in patterns
        ), "WeightRecord does not reference Pet"

    # ------------------------------------------------------------------
    # L2: Repository
    # ------------------------------------------------------------------

    def test_repository_extends_spring_data(self):
        """Repository must extend a Spring Data interface."""
        content = self._read(self.WEIGHT_PKG, "WeightRepository.java")
        patterns = [
            r"extends\s+(JpaRepository|CrudRepository|Repository)",
            r"@Repository",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "WeightRepository does not extend Spring Data"

    # ------------------------------------------------------------------
    # L2: Controller endpoints
    # ------------------------------------------------------------------

    def test_controller_has_endpoints(self):
        """Controller must define REST endpoints."""
        content = self._read(self.WEIGHT_PKG, "WeightController.java")
        patterns = [
            r"@GetMapping",
            r"@PostMapping",
            r"@RequestMapping",
            r"@RestController",
        ]
        found = sum(1 for p in patterns if re.search(p, content))
        assert found >= 2, "Controller missing REST endpoint annotations"

    def test_controller_has_validation(self):
        """Controller should validate weight input (reject zero/negative)."""
        content = self._read(self.WEIGHT_PKG, "WeightController.java")
        patterns = [
            r"@Valid",
            r"@Positive",
            r"@Min",
            r"validation",
            r"BindingResult",
            r"reject",
            r"error",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Controller does not validate weight input"

    # ------------------------------------------------------------------
    # L2: Schema
    # ------------------------------------------------------------------

    def test_schema_sql_has_weight_table(self):
        """schema.sql must define a weight records table."""
        schema_path = os.path.join(
            self.REPO_DIR, "src", "main", "resources", "db", "hsqldb", "schema.sql"
        )
        assert os.path.isfile(schema_path), "schema.sql not found"
        with open(schema_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r"CREATE\s+TABLE.*weight", content, re.IGNORECASE
        ), "schema.sql does not define weight records table"

    # ------------------------------------------------------------------
    # L2: Tests structure
    # ------------------------------------------------------------------

    def test_test_class_has_test_methods(self):
        """Test class must define @Test methods."""
        content = self._read(self.TEST_PKG, "WeightControllerTests.java")
        tests = re.findall(r"@Test", content)
        assert len(tests) >= 3, f"Only {len(tests)} @Test method(s) — need at least 3"

    def test_tests_cover_validation(self):
        """Tests should cover weight validation cases."""
        content = self._read(self.TEST_PKG, "WeightControllerTests.java")
        patterns = [r"invalid", r"negative", r"zero", r"bad.*request", r"400"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Tests do not cover validation failure cases"
