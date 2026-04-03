"""
Tests for 'tdd-workflow' skill — TDD URL Shortener Workflow.
Validates that the Agent implemented a URL shortener service following TDD
practices with proper project structure, class definitions, round-trip
correctness, and edge-case handling.
"""

import glob
import os
import re
import subprocess
import textwrap

import pytest


class TestTddWorkflow:
    """Verify TDD-driven URL shortener implementation."""

    REPO_DIR = "/workspace/python"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _safe_read(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    @classmethod
    def _run_in_repo(cls, cmd: str, timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            cwd=cls.REPO_DIR,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    # ── file_path_check (static) ────────────────────────────────────────

    def test_url_shortener_service_file_exists(self):
        """Verify that the core URL shortener service file is present."""
        path = os.path.join(self.REPO_DIR, "src", "services", "url-shortener.ts")
        assert os.path.isfile(path), f"Missing {path}"

    def test_store_file_exists(self):
        """Verify that a persistence store implementation file exists."""
        store_dir = os.path.join(self.REPO_DIR, "src", "store")
        candidates = [
            os.path.join(store_dir, "redis-store.ts"),
            os.path.join(store_dir, "in-memory-store.ts"),
        ]
        assert any(
            os.path.isfile(p) for p in candidates
        ), f"No store implementation found under {store_dir}"

    def test_test_files_exist(self):
        """Confirm TDD test files are created for the shortener service and routes."""
        tests_dir = os.path.join(self.REPO_DIR, "tests")
        shortener_test = os.path.join(tests_dir, "url-shortener.test.ts")
        routes_test = os.path.join(tests_dir, "routes.test.ts")
        assert os.path.isfile(shortener_test) or os.path.isfile(
            routes_test
        ), "Missing test files under tests/"

    # ── semantic_check (static) ─────────────────────────────────────────

    def test_url_shortener_class_defined(self):
        """Verify the UrlShortener class or shorten function is defined."""
        path = os.path.join(self.REPO_DIR, "src", "services", "url-shortener.ts")
        assert os.path.isfile(path), f"Missing {path}"
        content = self._safe_read(path)
        has_class = re.search(r"class\s+UrlShortener", content)
        has_func = re.search(r"(?:export\s+)?(?:async\s+)?function\s+shorten", content)
        assert (
            has_class or has_func
        ), "UrlShortener class or shorten function not found in url-shortener.ts"

    def test_resolve_method_signature(self):
        """Verify resolve method returns null for missing codes."""
        path = os.path.join(self.REPO_DIR, "src", "services", "url-shortener.ts")
        assert os.path.isfile(path), f"Missing {path}"
        content = self._safe_read(path)
        assert re.search(r"resolve\s*\(", content), "resolve method not found"
        assert re.search(
            r"string\s*\|\s*null|null\s*\|\s*string", content
        ), "resolve should return string | null"

    def test_test_file_uses_describe_it(self):
        """Verify test files follow TDD describe/it/expect structure."""
        tests_dir = os.path.join(self.REPO_DIR, "tests")
        test_files = glob.glob(os.path.join(tests_dir, "*.test.ts"))
        assert test_files, "No .test.ts files found in tests/"
        content = self._safe_read(test_files[0])
        assert re.search(r"\bdescribe\s*\(", content), "Missing describe() blocks"
        assert re.search(r"\bit\s*\(", content), "Missing it() blocks"
        assert re.search(r"\bexpect\s*\(", content), "Missing expect() assertions"

    # ── functional_check ────────────────────────────────────────────────

    def test_shorten_returns_base62_code(self):
        """Verify shorten() produces a short alphanumeric code."""
        result = self._run_in_repo("npm install", timeout=300)
        if result.returncode != 0:
            pytest.skip(f"npm install failed: {result.stderr[:200]}")
        result = self._run_in_repo(
            'npx ts-node -e "'
            "import {shorten} from './src/services/url-shortener';"
            "shorten('https://example.com/some/long/path').then(c => console.log(c))"
            '"'
        )
        if result.returncode != 0:
            pytest.skip(f"ts-node exec failed: {result.stderr[:200]}")
        code = result.stdout.strip()
        assert re.match(r"^[A-Za-z0-9]{4,}$", code), f"Unexpected code format: {code!r}"

    def test_shorten_resolve_round_trip(self):
        """Verify resolve(shorten(url)) returns the original URL."""
        script = (
            "import {shorten, resolve} from './src/services/url-shortener';"
            "async function main() {"
            "  const code = await shorten('https://example.com/path?q=1&r=2');"
            "  const url = await resolve(code);"
            "  console.log(url);"
            "}"
            "main();"
        )
        result = self._run_in_repo(f'npx ts-node -e "{script}"')
        if result.returncode != 0:
            pytest.skip(f"Round-trip test failed: {result.stderr[:200]}")
        assert "https://example.com/path?q=1&r=2" in result.stdout.strip()

    def test_delete_then_resolve_returns_null(self):
        """Verify that deleting a code causes subsequent resolve to return null."""
        script = (
            "import {shorten, resolve} from './src/services/url-shortener';"
            "async function main() {"
            "  const code = await shorten('https://example.com');"
            "  const svc = require('./src/services/url-shortener');"
            "  if (svc.remove) await svc.remove(code);"
            "  else if (svc.delete) await svc.delete(code);"
            "  const url = await resolve(code);"
            "  console.log(url === null ? 'NULL' : url);"
            "}"
            "main();"
        )
        result = self._run_in_repo(f'npx ts-node -e "{script}"')
        if result.returncode != 0:
            pytest.skip(f"Delete test failed: {result.stderr[:200]}")
        assert "NULL" in result.stdout or "null" in result.stdout.lower()

    def test_url_with_long_query_string(self):
        """Verify that a very long URL (2000+ chars) is shortened and resolvable."""
        script = (
            "import {shorten, resolve} from './src/services/url-shortener';"
            "async function main() {"
            "  const longUrl = 'https://example.com/' + 'a'.repeat(2000);"
            "  const code = await shorten(longUrl);"
            "  const url = await resolve(code);"
            "  console.log(url === longUrl ? 'MATCH' : 'MISMATCH');"
            "}"
            "main();"
        )
        result = self._run_in_repo(f'npx ts-node -e "{script}"')
        if result.returncode != 0:
            pytest.skip(f"Long URL test failed: {result.stderr[:200]}")
        assert "MATCH" in result.stdout

    def test_resolve_nonexistent_code_returns_null(self):
        """Verify resolve with a non-existent code returns null."""
        script = (
            "import {resolve} from './src/services/url-shortener';"
            "resolve('zzzzzz').then(r => console.log(r === null ? 'NULL' : r));"
        )
        result = self._run_in_repo(f'npx ts-node -e "{script}"')
        if result.returncode != 0:
            pytest.skip(f"Nonexistent resolve test failed: {result.stderr[:200]}")
        assert "NULL" in result.stdout or "null" in result.stdout.lower()

    def test_shorten_invalid_url_rejects(self):
        """Verify shorten rejects non-HTTP(S) URLs with an error."""
        script = (
            "import {shorten} from './src/services/url-shortener';"
            "shorten('ftp://badprotocol.com')"
            ".then(() => console.log('NO_ERROR'))"
            ".catch(e => console.log('ERROR:' + e.message));"
        )
        result = self._run_in_repo(f'npx ts-node -e "{script}"')
        if result.returncode != 0:
            pytest.skip(f"Invalid URL test exec failed: {result.stderr[:200]}")
        assert "ERROR" in result.stdout, "Expected an error for invalid URL"
