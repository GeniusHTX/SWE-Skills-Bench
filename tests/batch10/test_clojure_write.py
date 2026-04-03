"""
Test for 'clojure-write' skill — Metabase LRU+TTL Cache Namespace
Validates that the Agent created an LRU+TTL cache in Clojure for Metabase
with dataset API integration.
"""

import os
import re

import pytest


class TestClojureWrite:
    """Verify Metabase LRU+TTL cache implementation."""

    REPO_DIR = "/workspace/metabase"

    def test_cache_namespace_exists(self):
        """LRU+TTL cache namespace must exist."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"cache|lru|ttl", content, re.IGNORECASE) and re.search(r"defn|ns\s", content):
                        found = True
                        break
            if found:
                break
        assert found, "Cache namespace not found"

    def test_cache_has_lru_eviction(self):
        """Cache must implement LRU eviction policy."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"lru|least.recently.used|evict", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No LRU eviction logic found"

    def test_cache_has_ttl_expiry(self):
        """Cache must implement TTL-based expiry."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"ttl|time.to.live|expir|System/currentTimeMillis|nanoTime", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No TTL expiry logic found"

    def test_cache_has_get_and_put(self):
        """Cache must expose get and put operations."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"cache", content, re.IGNORECASE):
                        if re.search(r"defn\s+.*get|defn\s+.*put|defn\s+.*lookup|defn\s+.*store", content):
                            found = True
                            break
            if found:
                break
        assert found, "Cache does not expose get/put operations"

    def test_cache_is_thread_safe(self):
        """Cache should use atoms, refs, or agents for thread safety."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"cache", content, re.IGNORECASE):
                        if re.search(r"atom|ref\s|agent|swap!|reset!|dosync|ConcurrentHashMap", content):
                            found = True
                            break
            if found:
                break
        assert found, "Cache does not use thread-safe constructs"

    def test_dataset_api_integration(self):
        """Cache must be integrated with the dataset API."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj") and "dataset" in f.lower():
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"cache|cached", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Cache not integrated with dataset API"

    def test_max_size_configurable(self):
        """Cache max size should be configurable."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"max.size|capacity|limit|:size", content, re.IGNORECASE) and re.search(r"cache", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Cache max size not configurable"

    def test_cache_invalidation_function(self):
        """Cache must have an invalidation/clear function."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"invalidat|clear|evict-all|flush|purge", content, re.IGNORECASE) and re.search(r"cache", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Cache has no invalidation function"

    def test_tests_exist_for_cache(self):
        """Tests for the cache namespace must exist."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "test")):
            for f in files:
                if f.endswith(".clj"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"cache|ttl|lru", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No tests for cache namespace"

    def test_namespace_properly_defined(self):
        """Cache file must have a proper Clojure namespace declaration."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"cache", content, re.IGNORECASE) and re.search(r"\(ns\s+", content):
                        found = True
                        break
            if found:
                break
        assert found, "Cache file missing proper namespace declaration"

    def test_cache_metrics_or_logging(self):
        """Cache should log hits/misses or expose metrics."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"cache", content, re.IGNORECASE) and re.search(r"hit|miss|log|metric|counter", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Cache has no hit/miss logging or metrics"
