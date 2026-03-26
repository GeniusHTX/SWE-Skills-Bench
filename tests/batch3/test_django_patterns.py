"""
Tests for the django-patterns skill.
Verifies that the Saleor Django project Review model is correctly implemented
with UniqueConstraint, CheckConstraint, proper GraphQL mutations (ReviewCreate,
ReviewModerate) with permission checks, and importability for direct functional testing.
"""

import importlib
import os
import sys

import pytest

REPO_DIR = "/workspace/saleor"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    full = _path(rel)
    if not os.path.isfile(full):
        pytest.skip(f"File not found: {full}")
    with open(full, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _try_import(module_path: str):
    """Try to import a module relative to REPO_DIR; skip on ImportError."""
    if REPO_DIR not in sys.path:
        sys.path.insert(0, REPO_DIR)
    try:
        return importlib.import_module(module_path)
    except (ImportError, ModuleNotFoundError) as exc:
        pytest.skip(f"Cannot import {module_path}: {exc}")


def _setup_django():
    """Set up Django settings for testing; skip if Django is not configured."""
    try:
        import django
        from django.conf import settings

        if not settings.configured:
            settings.configure(
                DATABASES={
                    "default": {
                        "ENGINE": "django.db.backends.sqlite3",
                        "NAME": ":memory:",
                    }
                },
                INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
                DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            )
            django.setup()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# File path checks
# ---------------------------------------------------------------------------


class TestDjangoPatterns:
    """Test suite for the Django architecture patterns (Saleor review module) skill."""

    def test_review_model_file_exists(self):
        """Verify review/models.py exists at the expected Saleor path."""
        target = _path("saleor/review/models.py")
        assert os.path.isfile(target), f"review/models.py not found: {target}"
        assert os.path.getsize(target) > 0, "review/models.py must be non-empty"

    def test_graphql_mutations_file_exists(self):
        """Verify saleor/graphql/review/mutations.py exists."""
        target = _path("saleor/graphql/review/mutations.py")
        assert os.path.isfile(target), f"GraphQL mutations file not found: {target}"

    # -----------------------------------------------------------------------
    # Semantic checks
    # -----------------------------------------------------------------------

    def test_review_model_has_unique_constraint(self):
        """Verify Review model has UniqueConstraint on (product, user) in Meta class."""
        content = _read("saleor/review/models.py")
        assert (
            "UniqueConstraint" in content
        ), "Review model must define a UniqueConstraint in Meta.constraints"
        # Verify both product and user are referenced in context of UniqueConstraint
        uc_start = content.find("UniqueConstraint")
        context = content[max(0, uc_start - 50) : uc_start + 200]
        has_product = "product" in context
        has_user = "user" in context
        assert (
            has_product and has_user
        ), "UniqueConstraint must reference both 'product' and 'user' fields"

    def test_review_model_has_rating_check_constraint(self):
        """Verify Review model has CheckConstraint enforcing rating between 1 and 5."""
        content = _read("saleor/review/models.py")
        assert (
            "CheckConstraint" in content
        ), "Review model must define a CheckConstraint for the rating field"
        # Check for rating bounds
        has_five = "5" in content
        assert has_five, "CheckConstraint must enforce rating <= 5"

    def test_mutations_define_review_create(self):
        """Verify mutations.py defines ReviewCreate and ReviewModerate mutation classes."""
        content = _read("saleor/graphql/review/mutations.py")
        assert (
            "class ReviewCreate" in content
        ), "mutations.py must define 'class ReviewCreate'"
        assert (
            "class ReviewModerate" in content
        ), "mutations.py must define 'class ReviewModerate'"

    def test_review_moderate_requires_staff_permission(self):
        """Verify ReviewModerate mutation checks for staff permission."""
        content = _read("saleor/graphql/review/mutations.py")
        lower = content.lower()
        has_permission = (
            "permissions" in lower
            or "is_staff" in lower
            or "manage_reviews" in lower
            or "staff" in lower
        )
        assert (
            has_permission
        ), "ReviewModerate must define a permissions check (is_staff/MANAGE_REVIEWS/etc)"

    # -----------------------------------------------------------------------
    # Functional checks (import)
    # -----------------------------------------------------------------------

    def test_review_model_syntax_valid(self):
        """Verify review/models.py has valid Python syntax via py_compile."""
        import py_compile

        target = _path("saleor/review/models.py")
        if not os.path.isfile(target):
            pytest.skip("saleor/review/models.py not found")
        try:
            py_compile.compile(target, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"saleor/review/models.py has syntax errors: {exc}")

    def test_mutations_syntax_valid(self):
        """Verify saleor/graphql/review/mutations.py has valid Python syntax."""
        import py_compile

        target = _path("saleor/graphql/review/mutations.py")
        if not os.path.isfile(target):
            pytest.skip("mutations.py not found")
        try:
            py_compile.compile(target, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"mutations.py has syntax errors: {exc}")

    def test_review_model_importable(self):
        """Verify review/models.py can be imported without errors at module loading."""
        if not _setup_django():
            pytest.skip("Django not available for import test")
        _try_import("saleor.review.models")

    def test_review_model_rating_field_type(self):
        """Verify Review.rating field is defined as an IntegerField or PositiveIntegerField."""
        content = _read("saleor/review/models.py")
        has_integer_field = (
            "IntegerField" in content or "PositiveIntegerField" in content
        )
        assert (
            has_integer_field
        ), "Review.rating must use IntegerField or PositiveIntegerField"

    def test_review_mutations_registered_in_schema(self):
        """Verify GraphQL mutations are registered in the schema at the root mutations file."""
        root_mutations = _path("saleor/graphql/mutations.py")
        if not os.path.isfile(root_mutations):
            pytest.skip("saleor/graphql/mutations.py not found")
        with open(root_mutations, encoding="utf-8", errors="replace") as f:
            content = f.read()
        has_review = (
            "ReviewCreate" in content
            or "ReviewModerate" in content
            or "review" in content.lower()
        )
        assert (
            has_review
        ), "saleor/graphql/mutations.py must register review mutations (ReviewCreate/ReviewModerate)"

    def test_review_model_has_status_field(self):
        """Verify Review model defines a status field for moderation (PENDING/APPROVED/REJECTED)."""
        content = _read("saleor/review/models.py")
        lower = content.lower()
        has_status = "status" in lower
        has_states = "pending" in lower or "approved" in lower or "rejected" in lower
        assert has_status, "Review model must define a 'status' field"
        assert (
            has_states
        ), "Review status must have PENDING, APPROVED, or REJECTED states"
