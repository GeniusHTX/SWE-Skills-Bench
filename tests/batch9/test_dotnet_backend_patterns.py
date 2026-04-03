"""
Test for 'dotnet-backend-patterns' skill — .NET Backend Development Patterns
Validates CQRS/MediatR command handlers, FluentValidation setup, EF Core
AsNoTracking usage, Result pattern, DI registration, and migration files
in a Clean Architecture .NET project.
"""

import glob
import os
import re

import pytest


class TestDotnetBackendPatterns:
    """Verify .NET backend CQRS/MediatR patterns and Clean Architecture."""

    REPO_DIR = "/workspace/eshop"

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _read_file(path: str) -> str:
        """Read a file and return its content, or empty string on failure."""
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _glob_cs(self, *subdirs: str) -> list[str]:
        """Recursively glob for *.cs files under REPO_DIR/subdirs."""
        base = os.path.join(self.REPO_DIR, *subdirs)
        return glob.glob(os.path.join(base, "**", "*.cs"), recursive=True)

    def _find_startup_file(self) -> str | None:
        """Locate Program.cs or Startup.cs anywhere under src/."""
        for pattern in ["**/Program.cs", "**/Startup.cs"]:
            hits = glob.glob(
                os.path.join(self.REPO_DIR, "src", pattern), recursive=True
            )
            if hits:
                return hits[0]
        return None

    # ── file_path_check ──────────────────────────────────────────────────

    def test_commands_directory_exists(self):
        """src/Application/Commands/ directory must exist with at least one .cs file."""
        commands_dir = os.path.join(self.REPO_DIR, "src", "Application", "Commands")
        assert os.path.isdir(commands_dir), f"{commands_dir} does not exist"
        cs_files = self._glob_cs("src", "Application", "Commands")
        assert len(cs_files) >= 1, "No .cs files found in Commands/"

    def test_validators_directory_exists(self):
        """src/Application/Validators/ directory must exist with at least one .cs file."""
        validators_dir = os.path.join(self.REPO_DIR, "src", "Application", "Validators")
        assert os.path.isdir(validators_dir), f"{validators_dir} does not exist"
        cs_files = self._glob_cs("src", "Application", "Validators")
        assert len(cs_files) >= 1, "No .cs files found in Validators/"

    def test_appdbcontext_file_exists(self):
        """src/Infrastructure/Data/AppDbContext.cs must exist."""
        path = os.path.join(
            self.REPO_DIR, "src", "Infrastructure", "Data", "AppDbContext.cs"
        )
        assert os.path.isfile(path), f"{path} does not exist"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_command_handler_implements_irequesthandler(self):
        """At least one handler in Commands/ must implement IRequestHandler<>."""
        cs_files = self._glob_cs("src", "Application", "Commands")
        assert cs_files, "No .cs files in Commands/"
        found = any(
            ": IRequestHandler<" in self._read_file(f) for f in cs_files
        )
        assert found, "No command handler implements IRequestHandler<>"

    def test_validator_extends_abstractvalidator(self):
        """Validators/ must contain AbstractValidator<T> with RuleFor() chains."""
        cs_files = self._glob_cs("src", "Application", "Validators")
        assert cs_files, "No .cs files in Validators/"
        found_validator = False
        found_rule = False
        for f in cs_files:
            content = self._read_file(f)
            if ": AbstractValidator<" in content:
                found_validator = True
            if "RuleFor(" in content:
                found_rule = True
        assert found_validator, "No validator extends AbstractValidator<T>"
        assert found_rule, "No RuleFor() chains found in validators"

    def test_read_queries_use_asnotracking(self):
        """At least one .cs file under src/ must call .AsNoTracking()."""
        cs_files = self._glob_cs("src")
        assert cs_files, "No .cs files under src/"
        found = any(".AsNoTracking()" in self._read_file(f) for f in cs_files)
        assert found, ".AsNoTracking() not found in any source file"

    def test_result_pattern_used_not_raw_exceptions(self):
        """Application layer should use Result<T> or OneOf<T> instead of raw exceptions."""
        cs_files = self._glob_cs("src", "Application")
        assert cs_files, "No .cs files in Application/"
        found_result = any(
            re.search(r"Result<|OneOf<", self._read_file(f)) for f in cs_files
        )
        assert found_result, "No Result<> or OneOf<> pattern found in Application layer"

    def test_problem_details_422_on_validation_failure(self):
        """Codebase should map validation failures to 422 ProblemDetails (RFC 7807)."""
        cs_files = self._glob_cs("src")
        combined = "\n".join(self._read_file(f) for f in cs_files)
        patterns = ["422", "Status422UnprocessableEntity", "ValidationProblemDetails"]
        found = any(p in combined for p in patterns)
        assert found, "No 422/ProblemDetails mapping found for validation failures"

    # ── functional_check ─────────────────────────────────────────────────

    def test_command_handler_file_count_matches_command_count(self):
        """Each Command class should have a corresponding Handler (IRequestHandler)."""
        cs_files = self._glob_cs("src", "Application", "Commands")
        assert cs_files, "No .cs files in Commands/"
        command_count = 0
        handler_count = 0
        for f in cs_files:
            content = self._read_file(f)
            command_count += len(re.findall(r"class\s+\w+Command\b", content))
            handler_count += len(re.findall(r":\s*IRequestHandler<", content))
        assert handler_count >= command_count, (
            f"Handler count ({handler_count}) < command count ({command_count})"
        )

    def test_di_registration_present_in_startup(self):
        """Program.cs or Startup.cs must register MediatR and DbContext."""
        startup = self._find_startup_file()
        assert startup is not None, "No Program.cs or Startup.cs found under src/"
        content = self._read_file(startup)
        assert "AddMediatR" in content, "AddMediatR registration missing"
        assert "AddDbContext" in content or "DbContext" in content, (
            "AddDbContext registration missing"
        )

    def test_ef_core_migration_files_present(self):
        """Migrations/ directory should exist with at least one migration .cs file."""
        migrations_dir = os.path.join(
            self.REPO_DIR, "src", "Infrastructure", "Data", "Migrations"
        )
        assert os.path.isdir(migrations_dir), f"{migrations_dir} does not exist"
        cs_files = glob.glob(os.path.join(migrations_dir, "*.cs"))
        assert len(cs_files) >= 1, "No migration .cs files found"

    def test_empty_command_fields_blocked_by_validator(self):
        """Validators must include .NotEmpty() or .NotNull() on required fields."""
        cs_files = self._glob_cs("src", "Application", "Validators")
        assert cs_files, "No .cs files in Validators/"
        combined = "\n".join(self._read_file(f) for f in cs_files)
        assert ".NotEmpty()" in combined or ".NotNull()" in combined, (
            "No .NotEmpty() or .NotNull() rule found in validators"
        )
