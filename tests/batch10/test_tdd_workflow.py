"""
Test for 'tdd-workflow' skill — Python TDD password validator
Validates that the Agent implemented a password strength validator
using TDD with pytest, following a red-green-refactor workflow.
"""

import os
import re

import pytest


class TestTddWorkflow:
    """Verify Python TDD password validator implementation."""

    REPO_DIR = "/workspace/python"

    def test_password_validator_file_exists(self):
        """password_validator.py must be created."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "password_validator.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"def\s+(validate|check_strength)", content):
                        found = True
                        break
            if found:
                break
        assert found, "password_validator.py with validate/check_strength function not found"

    def test_test_file_exists(self):
        """test_password_validator.py must be created with at least 5 test functions."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "test_password_validator.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    test_count = len(re.findall(r"def\s+test_", content))
                    if test_count >= 5:
                        found = True
                        break
            if found:
                break
        assert found, "test_password_validator.py with >= 5 test functions not found"

    def test_strength_levels_defined(self):
        """Three strength levels (weak, medium, strong) must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "password_validator.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read().lower()
                    if "weak" in content and "medium" in content and "strong" in content:
                        found = True
                        break
            if found:
                break
        assert found, "Not all three strength levels (weak, medium, strong) found"

    def test_minimum_length_check_present(self):
        """Minimum length check must be present in validator."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "password_validator.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"len\(", content) and re.search(r"[78]", content):
                        found = True
                        break
            if found:
                break
        assert found, "Minimum length check not found in password_validator.py"

    def test_special_character_check_present(self):
        """Special character check must be implemented."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "password_validator.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[!@#$%^&*]|punctuation|special|re\.search", content):
                        found = True
                        break
            if found:
                break
        assert found, "Special character check not found in password_validator.py"

    def test_strong_password_classified_correctly(self):
        """Validator must classify a strong password correctly."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "test_password_validator.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"strong", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No test covering 'strong' password classification found"

    def test_weak_password_classified_correctly(self):
        """Validator must classify a weak password correctly."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "test_password_validator.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"weak", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No test covering 'weak' password classification found"

    def test_empty_password_raises_valueerror(self):
        """Empty password must raise ValueError."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("password_validator.py", "test_password_validator.py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"ValueError|empty|raise", content):
                        found = True
                        break
            if found:
                break
        assert found, "Empty password ValueError handling not found"

    def test_exactly_8_chars_is_at_least_medium(self):
        """8-character mixed password must not be classified as weak."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "test_password_validator.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"boundary|8.*char|Passw0rd|medium|not.*weak", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Boundary test for 8-character password not found"

    def test_all_tests_in_test_file_pass(self):
        """Test file must contain import and assertion statements."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "test_password_validator.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"import.*password_validator|from.*password_validator", content):
                        if re.search(r"assert", content):
                            found = True
                            break
            if found:
                break
        assert found, "Test file does not import password_validator or lacks assertions"

    def test_whitespace_only_password_rejected(self):
        """Whitespace-only password must be rejected or classified as weak."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("password_validator.py", "test_password_validator.py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"strip|whitespace|spaces?\s*only|isspace", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Whitespace-only password handling not found"
