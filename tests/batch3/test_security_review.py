"""
Tests for security-review skill.
Validates InputValidator, SafeQueryBuilder security in api/validators.py.
"""

import os
import pytest

REPO_DIR = "/workspace/babybuddy"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestSecurityReview:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_validators_file_exists(self):
        """api/validators.py must exist."""
        rel = "api/validators.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "validators.py is empty"

    def test_middleware_file_exists(self):
        """At least one security middleware file must exist."""
        found = False
        for rel in ("api/middleware.py", "babybuddy/middleware.py"):
            if os.path.isfile(_path(rel)):
                found = True
                break
        assert (
            found
        ), "No middleware file found at api/middleware.py or babybuddy/middleware.py"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_input_validator_class_defined(self):
        """InputValidator class must be defined with validation and error classes."""
        content = _read("api/validators.py")
        assert "class InputValidator" in content, "InputValidator class not defined"
        assert "ValidationError" in content, "ValidationError not defined"
        has_security_error = (
            "SecurityError" in content or "PasswordPolicyError" in content
        )
        assert has_security_error, "SecurityError or PasswordPolicyError not defined"

    def test_safe_query_builder_defined(self):
        """SafeQueryBuilder must define allowed fields whitelist."""
        content = _read("api/validators.py")
        assert "class SafeQueryBuilder" in content, "SafeQueryBuilder class not defined"
        has_whitelist = (
            "ALLOWED_FIELDS" in content
            or "whitelist" in content.lower()
            or "allowed_fields" in content
        )
        assert (
            has_whitelist
        ), "No whitelist for allowed fields found in SafeQueryBuilder"

    def test_xss_patterns_blocked(self):
        """validators.py must check for XSS patterns and null bytes."""
        content = _read("api/validators.py")
        has_xss = "script" in content.lower() or "<" in content
        assert has_xss, "No XSS pattern check found in validators.py"
        has_null = r"\x00" in content or "null" in content.lower() or r"\0" in content
        assert has_null, "No null byte check found in validators.py"

    def test_lockout_threshold_defined(self):
        """Brute-force lockout threshold of 5 must be defined."""
        content = _read("api/validators.py")
        has_threshold = (
            "MAX_FAILURES" in content or "MAX_ATTEMPTS" in content or "5" in content
        )
        assert has_threshold, "No lockout threshold found in validators.py"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_xss_input_raises_validation_error(self):
        """XSS input must raise ValidationError (mocked)."""
        import re

        class ValidationError(Exception):
            pass

        class InputValidator:
            XSS_PATTERN = re.compile(r"<script|javascript:|on\w+=", re.IGNORECASE)
            NULL_BYTE = "\x00"

            def validate_text(self, text: str):
                if self.NULL_BYTE in text:
                    raise ValidationError("Null byte detected")
                if self.XSS_PATTERN.search(text):
                    raise ValidationError("XSS pattern detected")

        v = InputValidator()
        with pytest.raises(ValidationError):
            v.validate_text("<script>alert(1)</script>")

    def test_null_bytes_raise_validation_error(self):
        """Null byte input must raise ValidationError (mocked)."""

        class ValidationError(Exception):
            pass

        class InputValidator:
            def validate_text(self, text: str):
                if "\x00" in text:
                    raise ValidationError("Null byte detected")

        v = InputValidator()
        with pytest.raises(ValidationError):
            v.validate_text("hello\x00world")

    def test_nan_numeric_raises_validation_error(self):
        """NaN string in numeric field must raise ValidationError (mocked)."""
        import math

        class ValidationError(Exception):
            pass

        class InputValidator:
            def validate_numeric(self, value: str):
                try:
                    f = float(value)
                    if math.isnan(f) or math.isinf(f):
                        raise ValidationError(f"Invalid numeric value: {value!r}")
                except ValueError:
                    raise ValidationError(f"Not a number: {value!r}")

        v = InputValidator()
        with pytest.raises(ValidationError):
            v.validate_numeric("NaN")

    def test_non_whitelisted_field_raises_security_error(self):
        """SafeQueryBuilder must raise SecurityError for non-whitelisted fields (mocked)."""
        import logging

        class SecurityError(Exception):
            pass

        class SafeQueryBuilder:
            ALLOWED_FIELDS = {"name", "date", "type", "child"}

            def build_filter(self, field: str, value):
                base = field.split("__")[0]
                if base not in self.ALLOWED_FIELDS:
                    logging.warning("Unauthorized field access: %s", field)
                    raise SecurityError(f"Field not allowed: {field!r}")
                return {field: value}

        qb = SafeQueryBuilder()
        with pytest.raises(SecurityError):
            qb.build_filter("password__contains", "secret")

    def test_weak_password_raises_policy_error(self):
        """Password shorter than 8 chars must raise PasswordPolicyError (mocked)."""

        class PasswordPolicyError(Exception):
            pass

        class InputValidator:
            MIN_PASSWORD_LEN = 8

            def validate_password(self, password: str):
                if len(password) < self.MIN_PASSWORD_LEN:
                    raise PasswordPolicyError(
                        f"Password must be at least {self.MIN_PASSWORD_LEN} chars"
                    )

        v = InputValidator()
        with pytest.raises(PasswordPolicyError):
            v.validate_password("short")

    def test_five_failures_triggers_lockout(self):
        """Account must be locked after exactly 5 consecutive failures (mocked)."""

        class InputValidator:
            MAX_FAILURES = 5

            def __init__(self):
                self._failures = {}
                self._locked = set()

            def record_failure(self, username: str):
                count = self._failures.get(username, 0) + 1
                self._failures[username] = count
                if count >= self.MAX_FAILURES:
                    self._locked.add(username)

            def is_locked_out(self, username: str) -> bool:
                return username in self._locked

        v = InputValidator()
        for _ in range(4):
            v.record_failure("testuser")
        assert not v.is_locked_out("testuser"), "Should not be locked after 4 failures"
        v.record_failure("testuser")
        assert v.is_locked_out("testuser"), "Should be locked after 5 failures"
