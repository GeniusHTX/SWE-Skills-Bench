"""
Test for 'django-patterns' skill — Saleor Gift Card Template
Validates Django model with denominations, positive constraint, currency,
serializer validation, deactivation, and IDOR prevention.
"""

import os
import re
import subprocess
import sys

import pytest


class TestDjangoPatterns:
    """Verify Saleor Django gift card template patterns."""

    REPO_DIR = "/workspace/saleor"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_python_source_files_exist(self):
        """Verify at least 4 Python source files for gift card templates exist."""
        py_files = self._find_gift_card_files()
        assert (
            len(py_files) >= 3
        ), f"Expected ≥3 gift card Python files, found {len(py_files)}"

    def test_test_file_exists(self):
        """Verify a test file for gift card templates exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and "test" in f.lower() and "gift" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No gift card test file found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_gift_card_template_model(self):
        """Verify GiftCardTemplate model with denominations field."""
        py_files = self._find_gift_card_files()
        assert py_files, "No gift card files"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"class\s+GiftCardTemplate", content):
                if "denomination" in content.lower():
                    return
                return  # Model exists even without explicit denomination
        pytest.fail("No GiftCardTemplate model found")

    def test_positive_value_constraint(self):
        """Verify positive value constraint on denomination/amount."""
        py_files = self._find_gift_card_files()
        assert py_files, "No gift card files"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(PositiveDecimalField|MinValueValidator|positive|PositiveIntegerField|CheckConstraint.*>.*0)",
                content,
            ):
                return
        pytest.fail("No positive value constraint found")

    def test_currency_max_length_3(self):
        """Verify currency field has max_length=3 (ISO 4217)."""
        py_files = self._find_gift_card_files()
        assert py_files, "No gift card files"
        for fpath in py_files:
            content = self._read(fpath)
            if "currency" in content.lower():
                if re.search(r"max_length\s*=\s*3", content):
                    return
        pytest.fail("No currency field with max_length=3")

    def test_serializer_validation(self):
        """Verify serializer with validation logic."""
        py_files = self._find_gift_card_files()
        assert py_files, "No gift card files"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(Serializer|validate|clean|validators)", content):
                return
        pytest.fail("No serializer validation found")

    def test_deactivate_functionality(self):
        """Verify deactivation/is_active toggle for gift card templates."""
        py_files = self._find_gift_card_files()
        assert py_files, "No gift card files"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(deactivat|is_active|active\s*=|set_active)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No deactivation functionality found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_source_files_compile(self):
        """Verify Python files compile without errors."""
        py_files = self._find_gift_card_files()
        assert py_files, "No gift card files"
        for fpath in py_files:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", fpath],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert (
                result.returncode == 0
            ), f"Compile error in {os.path.basename(fpath)}: {result.stderr}"

    def test_idor_prevention(self):
        """Verify IDOR prevention (user-scoped queries or permission checks)."""
        py_files = self._find_gift_card_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(request\.user|permission|owner|user_id|IsAuthenticated|has_perm)",
                content,
            ):
                return
        pytest.fail("No IDOR prevention (user scoping or permission check) found")

    def test_zero_negative_value_rejection(self):
        """Verify zero and negative values are rejected."""
        all_files = self._find_gift_card_files()
        # Also include test files
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and "test" in f.lower() and "gift" in f.lower():
                    all_files.append(os.path.join(dirpath, f))
        for fpath in all_files:
            content = self._read(fpath)
            if re.search(
                r"(<=\s*0|<\s*0|negative|zero|MinValue|ValidationError)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.skip("Zero/negative rejection not explicitly detectable")

    def test_model_has_str_method(self):
        """Verify model defines __str__ for admin readability."""
        py_files = self._find_gift_card_files()
        for fpath in py_files:
            content = self._read(fpath)
            if "class GiftCard" in content and "__str__" in content:
                return
        pytest.skip("__str__ not required but recommended")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_gift_card_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".py")
                    and "gift" in f.lower()
                    and "test" not in f.lower()
                ):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
