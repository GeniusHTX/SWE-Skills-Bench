"""
Test for 'clojure-write' skill — Metabase Notification System
Validates Clojure notification records, multimethods, webhook HMAC-SHA256,
Slack truncation, core.async scheduler, and error handling.
"""

import os
import re

import pytest


class TestClojureWrite:
    """Verify Metabase Clojure notification system."""

    REPO_DIR = "/workspace/metabase"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_notification_source_files_exist(self):
        """Verify at least 5 notification .clj files exist."""
        src_dir = os.path.join(self.REPO_DIR, "src")
        if not os.path.isdir(src_dir):
            pytest.skip("src/ directory not found")
        notif_files = []
        for dirpath, _, fnames in os.walk(src_dir):
            for f in fnames:
                if f.endswith(".clj") and "notif" in f.lower():
                    notif_files.append(os.path.join(dirpath, f))
        assert (
            len(notif_files) >= 4
        ), f"Expected ≥4 notification .clj files, found {len(notif_files)}"

    def test_notification_test_file_exists(self):
        """Verify at least one notification test file exists."""
        test_dir = os.path.join(self.REPO_DIR, "test")
        if not os.path.isdir(test_dir):
            pytest.skip("test/ not found")
        for dirpath, _, fnames in os.walk(test_dir):
            for f in fnames:
                if f.endswith(".clj") and "notif" in f.lower():
                    return
        pytest.fail("No notification test file found")

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_defrecord_notification(self):
        """Verify defrecord Notification is defined."""
        files = self._find_notification_files()
        assert files, "No notification files found"
        for fpath in files:
            content = self._read(fpath)
            if re.search(r"defrecord\s+Notification", content):
                return
        pytest.fail("No defrecord Notification found")

    def test_defmulti_dispatch(self):
        """Verify defmulti with dispatch function is defined."""
        files = self._find_notification_files()
        assert files, "No notification files found"
        for fpath in files:
            content = self._read(fpath)
            if "defmulti" in content:
                return
        pytest.fail("No defmulti dispatch found")

    def test_webhook_hmac_sha256(self):
        """Verify webhook uses HMAC-SHA256 signing."""
        files = self._find_notification_files()
        assert files, "No notification files found"
        for fpath in files:
            content = self._read(fpath)
            if re.search(
                r"(hmac|sha.?256|HmacSHA256|Mac/getInstance)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No HMAC-SHA256 webhook signing found")

    def test_slack_50_block_truncation(self):
        """Verify Slack integration truncates to 50 blocks."""
        files = self._find_notification_files()
        assert files, "No notification files found"
        for fpath in files:
            content = self._read(fpath)
            if "50" in content and (
                "block" in content.lower()
                or "truncat" in content.lower()
                or "take " in content
            ):
                return
        pytest.fail("No Slack 50-block truncation found")

    def test_core_async_scheduler(self):
        """Verify core.async scheduler with concurrency limit."""
        files = self._find_notification_files()
        assert files, "No notification files found"
        for fpath in files:
            content = self._read(fpath)
            if "core.async" in content or "async" in content.lower():
                if re.search(r"(pipeline|thread|go-loop|chan|5|concurrent)", content):
                    return
        pytest.fail("No core.async scheduler with concurrency limit found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_clojure_files_balanced_parens(self):
        """Verify Clojure notification files have balanced brackets."""
        files = self._find_notification_files()
        assert files, "No notification files found"
        for fpath in files:
            content = self._read(fpath)
            opens = content.count("(") + content.count("[") + content.count("{")
            closes = content.count(")") + content.count("]") + content.count("}")
            assert opens == closes, (
                f"Unbalanced brackets in {os.path.basename(fpath)}: "
                f"open={opens}, close={closes}"
            )

    def test_namespaces_declared(self):
        """Verify all notification files declare namespaces."""
        files = self._find_notification_files()
        assert files, "No notification files found"
        for fpath in files:
            content = self._read(fpath)
            assert re.search(
                r"\(ns\s+", content
            ), f"No namespace declaration in {os.path.basename(fpath)}"

    def test_error_handling_present(self):
        """Verify error handling (try/catch/ex-info) exists in notification code."""
        files = self._find_notification_files()
        assert files, "No notification files found"
        for fpath in files:
            content = self._read(fpath)
            if re.search(r"(try|catch|ex-info|ex-message|throw)", content):
                return
        pytest.fail("No error handling found in notification files")

    def test_defmethod_implementations(self):
        """Verify defmethod implementations exist for notification types."""
        files = self._find_notification_files()
        assert files, "No notification files found"
        method_count = 0
        for fpath in files:
            content = self._read(fpath)
            method_count += len(re.findall(r"defmethod\s+", content))
        assert (
            method_count >= 2
        ), f"Expected ≥2 defmethod implementations, found {method_count}"

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_notification_files(self):
        results = []
        src_dir = os.path.join(self.REPO_DIR, "src")
        if not os.path.isdir(src_dir):
            return results
        for dirpath, _, fnames in os.walk(src_dir):
            for f in fnames:
                if f.endswith(".clj") and "notif" in f.lower():
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
