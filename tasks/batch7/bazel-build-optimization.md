# Task: Implement a Remote Cache Hit Rate Analyzer for Bazel

## Background

Bazel (https://github.com/bazelbuild/bazel) supports remote caching to share build artifacts across machines. However, diagnosing poor cache hit rates requires manually parsing Build Event Protocol (BEP) output. The task is to implement a Java-based cache analysis module within Bazel that parses BEP events, computes per-target and aggregate cache hit rates, identifies targets that are frequently rebuilt due to input changes, and produces a structured analysis report.

## Files to Create/Modify

- `src/main/java/com/google/devtools/build/lib/remote/CacheHitAnalyzer.java` (create) — Analyzes BEP events to compute cache hit statistics per target and aggregate
- `src/main/java/com/google/devtools/build/lib/remote/CacheAnalysisReport.java` (create) — Data classes for the structured analysis report
- `src/main/java/com/google/devtools/build/lib/remote/InputChangeTracker.java` (create) — Tracks which input files cause the most cache misses across builds
- `src/test/java/com/google/devtools/build/lib/remote/CacheHitAnalyzerTest.java` (create) — Unit tests for the cache analysis logic
- `src/test/java/com/google/devtools/build/lib/remote/InputChangeTrackerTest.java` (create) — Unit tests for input change tracking
- `src/main/java/com/google/devtools/build/lib/remote/BUILD` (modify) — Add new source files to the Bazel BUILD target

## Requirements

### `CacheHitAnalyzer`

```java
public class CacheHitAnalyzer {
    public CacheHitAnalyzer(List<BuildEventStreamProtos.BuildEvent> events);
    public CacheAnalysisReport analyze();
}
```

#### Analysis Logic

1. Iterate over all BEP events of type `ActionExecuted`
2. For each action, determine cache status:
   - `CACHE_HIT` — Action result was fetched from remote cache
   - `CACHE_MISS` — Action was executed locally (cache miss)
   - `LOCAL_ONLY` — Action is not cacheable (e.g., local test execution)
3. Group actions by their target label (e.g., `//src/main/java/com/google/devtools/build/lib:build-base`)
4. For each target, compute:
   - Total actions, cache hits, cache misses, hit rate (as a percentage)
   - Total execution time saved by cache hits (from action timing metadata)
5. Compute aggregate statistics across all targets

### `CacheAnalysisReport`

```java
public class CacheAnalysisReport {
    private final AggregateStats aggregate;
    private final List<TargetCacheStats> perTarget;
    private final List<FrequentMiss> topMisses;
    
    public record AggregateStats(
        int totalActions,
        int cacheHits,
        int cacheMisses,
        int notCacheable,
        double hitRatePercent,
        Duration totalTimeSaved,
        Duration totalBuildTime
    ) {}
    
    public record TargetCacheStats(
        String targetLabel,
        int totalActions,
        int cacheHits,
        int cacheMisses,
        double hitRatePercent,
        Duration timeSaved,
        String worstInputChange    // Most frequently changed input for this target
    ) {}
    
    public record FrequentMiss(
        String targetLabel,
        int missCount,
        String primaryCause,      // "input_change", "config_change", "new_target", "cache_eviction"
        List<String> changedInputs
    ) {}
}
```

#### Report Contents

- `aggregate` — Overall cache statistics for the build
- `perTarget` — Per-target breakdown sorted by miss count descending (worst offenders first)
- `topMisses` — Top 20 targets with the most cache misses, with root cause classification

### `InputChangeTracker`

```java
public class InputChangeTracker {
    public void recordAction(String targetLabel, List<String> inputDigests, List<String> inputPaths, boolean cacheHit);
    public Map<String, Integer> getFrequentlyChangedInputs(int topN);
    public String getPrimaryCauseForTarget(String targetLabel);
}
```

#### Cache Miss Classification

Classify each cache miss into one of these causes:
- `"input_change"` — One or more input files have different digests compared to the previous action for the same target
- `"config_change"` — The action configuration (command line, environment) differs
- `"new_target"` — No previous action record exists for this target (first build)
- `"cache_eviction"` — Inputs match a previous build but the cache entry is missing (evicted)

#### Input Tracking

- Maintain a history of input digests per target to detect changes
- `getFrequentlyChangedInputs(topN)` returns the N input files that appear most often in cache misses across all targets
- This helps identify "volatile" files (e.g., generated timestamps, build metadata) that defeat caching

### Output Format

The report must support two output formats:
- `toJson()` — JSON representation suitable for CI dashboards
- `toText()` — Human-readable text summary with a table of per-target stats

Text format example:
```
=== Bazel Remote Cache Analysis ===
Total Actions: 1,234 | Hits: 1,100 (89.1%) | Misses: 120 | Not Cacheable: 14
Time Saved: 45m 30s | Build Time: 12m 15s

Top Cache Misses:
  //src/main/java/...:target-a    15 misses (input_change: src/main/Input.java)
  //src/test/java/...:target-b    12 misses (config_change)
  ...

Frequently Changed Inputs:
  src/main/java/gen/BuildInfo.java    changed in 45 targets
  src/main/resources/version.txt      changed in 23 targets
```

## Expected Functionality

- Given 1000 `ActionExecuted` events with 850 cache hits and 150 misses: the aggregate hit rate is 85%
- The per-target breakdown lists targets sorted by miss count
- `InputChangeTracker` identifies that `src/main/java/gen/BuildInfo.java` triggers the most cache misses
- The report classifies misses correctly: a target that has never been built before gets `"new_target"` cause

## Acceptance Criteria

- `CacheHitAnalyzer` correctly parses BEP `ActionExecuted` events and classifies cache status
- Per-target stats accurately aggregate hit/miss counts and timing
- `InputChangeTracker` maintains input digest history and identifies frequently changed files
- Cache miss classification correctly distinguishes input_change, config_change, new_target, and cache_eviction
- `toJson()` produces valid JSON and `toText()` produces human-readable output
- Top misses list includes root cause and changed input files
- New files are properly added to the BUILD file
- All unit tests pass with synthetic BEP event data
