"""
Test for 'implementing-jsc-classes-zig' skill — BunHasher JSC Class
Validates that the Agent created a JavaScript hash class using Bun's
Zig-JSC bindings with class definition, Zig implementation, and tests.
"""

import os
import re

import pytest


class TestImplementingJscClassesZig:
    """Verify BunHasher JSC class implementation."""

    REPO_DIR = "/workspace/bun"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_classes_ts_exists(self):
        """BunHasher.classes.ts must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "src/bun.js/api/BunHasher.classes.ts")
        )

    def test_zig_implementation_exists(self):
        """BunHasher.zig must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "src/bun.js/api/BunHasher.zig")
        )

    def test_test_file_exists(self):
        """hasher.test.ts test file must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "test/js/bun/hasher.test.ts"))

    # ------------------------------------------------------------------
    # L1: Class definition structure
    # ------------------------------------------------------------------

    def test_classes_ts_uses_define(self):
        """BunHasher.classes.ts must use define() pattern."""
        content = self._read("src/bun.js/api/BunHasher.classes.ts")
        assert re.search(
            r"define\(", content
        ), "BunHasher.classes.ts does not use define()"

    def test_classes_ts_declares_constructor(self):
        """Class definition must declare a constructor."""
        content = self._read("src/bun.js/api/BunHasher.classes.ts")
        patterns = [r"construct", r"constructor", r"init"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Class definition missing constructor"

    def test_classes_ts_declares_methods(self):
        """Class definition must declare prototype methods."""
        content = self._read("src/bun.js/api/BunHasher.classes.ts")
        patterns = [r"hash", r"digest", r"update", r"prototype", r"method"]
        found = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
        assert found >= 2, "Class definition missing method declarations"

    def test_classes_ts_declares_getter(self):
        """Class definition must declare a property getter."""
        content = self._read("src/bun.js/api/BunHasher.classes.ts")
        patterns = [r"get\b", r"getter", r"property", r"algorithm", r"name"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Class definition missing property getter"

    def test_classes_ts_has_finalize(self):
        """Class definition must enable finalization for cleanup."""
        content = self._read("src/bun.js/api/BunHasher.classes.ts")
        patterns = [r"finalize", r"deinit", r"destructor", r"cleanup"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Class definition missing finalization"

    # ------------------------------------------------------------------
    # L2: Zig implementation
    # ------------------------------------------------------------------

    def test_zig_has_struct(self):
        """BunHasher.zig must define a struct."""
        content = self._read("src/bun.js/api/BunHasher.zig")
        assert re.search(r"(pub\s+)?const\s+\w+\s*=\s*struct", content) or re.search(
            r"struct\s*\{", content
        ), "BunHasher.zig does not define a struct"

    def test_zig_supports_multiple_algorithms(self):
        """Zig implementation must support multiple hash algorithms."""
        content = self._read("src/bun.js/api/BunHasher.zig")
        algorithms = [
            r"sha256",
            r"sha512",
            r"md5",
            r"sha1",
            r"blake2",
            r"sha384",
            r"xxhash",
            r"SHA256",
            r"SHA512",
            r"MD5",
        ]
        found = sum(1 for a in algorithms if re.search(a, content, re.IGNORECASE))
        assert (
            found >= 2
        ), f"Only {found} hash algorithm(s) referenced — need at least 2"

    def test_zig_accepts_string_input(self):
        """Zig must accept string input for hashing."""
        content = self._read("src/bun.js/api/BunHasher.zig")
        patterns = [r"string", r"String", r"\[\]u8", r"slice", r"toJSString"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Zig does not accept string input"

    def test_zig_accepts_binary_input(self):
        """Zig must accept binary (Uint8Array) input."""
        content = self._read("src/bun.js/api/BunHasher.zig")
        patterns = [r"Uint8Array", r"ArrayBuffer", r"TypedArray", r"binary", r"bytes"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Zig does not accept binary input"

    def test_zig_has_finalizer(self):
        """Zig must implement memory cleanup in finalizer."""
        content = self._read("src/bun.js/api/BunHasher.zig")
        patterns = [r"finalize", r"deinit", r"destroy", r"free", r"allocator"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Zig missing finalizer/cleanup"

    def test_zig_has_public_functions(self):
        """Zig must expose at least 3 public functions."""
        content = self._read("src/bun.js/api/BunHasher.zig")
        pub_fns = re.findall(r"pub\s+fn\s+\w+", content)
        assert (
            len(pub_fns) >= 3
        ), f"Only {len(pub_fns)} public function(s) — need at least 3"

    # ------------------------------------------------------------------
    # L2: Test suite
    # ------------------------------------------------------------------

    def test_test_has_algorithm_tests(self):
        """Test file must test each supported hash algorithm."""
        content = self._read("test/js/bun/hasher.test.ts")
        patterns = [r"sha256|sha512|md5|sha1|blake2", r"algorithm"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Tests do not cover hash algorithms"

    def test_test_covers_input_types(self):
        """Test file must test various input types."""
        content = self._read("test/js/bun/hasher.test.ts")
        input_patterns = [
            r'""',  # empty string
            r"Uint8Array",  # binary
            r"unicode|emoji|utf",  # unicode
        ]
        found = sum(1 for p in input_patterns if re.search(p, content, re.IGNORECASE))
        assert found >= 2, "Tests do not cover enough input types"

    def test_test_verifies_determinism(self):
        """Tests should verify deterministic output."""
        content = self._read("test/js/bun/hasher.test.ts")
        patterns = [r"equal|toBe|toEqual|same|match", r"expect.*digest.*toBe"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Tests do not verify deterministic output"

    def test_test_has_enough_cases(self):
        """Test file must have at least 4 test cases."""
        content = self._read("test/js/bun/hasher.test.ts")
        test_count = len(re.findall(r"(it|test)\s*\(", content))
        assert test_count >= 4, f"Only {test_count} test case(s) — need at least 4"
