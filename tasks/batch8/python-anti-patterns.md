# Task: Add a Resource Pool Utility Module to Boltons

## Background

Boltons (https://github.com/mahmoud/boltons) is a pure-Python utility library containing 230+ constructs that extend the standard library. The project needs a new `poolutils` module providing a generic, thread-safe resource pool for reusable objects such as database connections, HTTP sessions, or worker threads. The implementation must adhere to boltons' conventions: pure Python, no external dependencies, thorough error handling, clean separation of concerns, and proper typing.

## Files to Create/Modify

- `boltons/poolutils.py` (create) — `ResourcePool` class with configurable min/max size, health checks, idle eviction, and borrow/return semantics
- `tests/test_poolutils.py` (create) — Test suite covering pool lifecycle, concurrency, error scenarios, and edge cases
- `boltons/__init__.py` (modify) — Add `poolutils` to the package's module list if a central registry exists
- `docs/poolutils.rst` (create) — Module documentation following boltons' existing doc style

## Requirements

### ResourcePool Class

- `ResourcePool(factory, *, min_size=0, max_size=10, max_idle_time=300.0, health_check=None, validation_interval=30.0)`
- `factory`: a callable returning a new resource instance; must not accept arguments
- `min_size`: minimum number of resources kept alive in the pool (pre-warmed on construction)
- `max_size`: maximum number of resources; attempts to borrow beyond this limit block up to `timeout` seconds
- `max_idle_time`: seconds after which an idle resource is evicted; `None` disables eviction
- `health_check`: an optional callable `(resource) -> bool` invoked before returning a resource from the pool; unhealthy resources are discarded and replaced
- `validation_interval`: minimum seconds between health checks on the same resource to avoid excessive checking

### Borrow/Return Semantics

- `pool.acquire(timeout=30.0)` borrows a resource, blocking up to `timeout` seconds if the pool is exhausted; raises `PoolExhaustedError` on timeout
- `pool.release(resource)` returns a resource to the pool; if the pool is already at `max_size` (due to concurrent shrink), the resource is discarded
- `pool.acquire()` must be usable as a context manager: `with pool.acquire() as conn: ...` — the resource is automatically released on exit, even if an exception occurs
- If the factory callable raises an exception during `acquire`, the exception must propagate to the caller with the original traceback intact; the pool must not leak a slot

### Thread Safety

- All pool operations (`acquire`, `release`, pool-internal bookkeeping) must be safe for concurrent use from multiple threads
- Internal state must be guarded with `threading.Lock` or `threading.Condition`; no bare global mutable state
- The pool must not deadlock when `acquire` is called from multiple threads simultaneously while the pool is at capacity

### Idle Eviction

- A background reaper removes resources idle longer than `max_idle_time`
- The reaper thread must be a daemon thread so it does not prevent interpreter shutdown
- When `min_size > 0`, the reaper must not evict resources below `min_size` — it must re-create resources to maintain the minimum

### Error Handling

- `PoolExhaustedError(timeout, max_size)`: raised when `acquire` times out; message must include the configured `max_size` and the elapsed wait time
- `PoolClosedError`: raised when `acquire` or `release` is called after `pool.close()`
- `pool.close()` must drain all idle resources, calling an optional `dispose` callable on each resource, and reject further operations
- Resources that raise exceptions during `health_check` must be silently discarded and not returned to callers; the pool must attempt to create a fresh resource in their place

### Statistics

- `pool.stats()` returns a dictionary with keys: `total`, `idle`, `in_use`, `created_count`, `discarded_count`, `timeout_count`
- Statistics counters must be updated atomically

## Expected Functionality

- `ResourcePool(lambda: create_connection(), max_size=5)` creates a pool of up to 5 connections
- `with pool.acquire(timeout=5.0) as conn:` borrows a connection, uses it, and returns it on block exit
- Calling `pool.acquire()` from 6 threads simultaneously when `max_size=5` causes the 6th caller to block and eventually raise `PoolExhaustedError` if no resource is freed within the timeout
- A resource failing `health_check` is discarded and a new resource is transparently created for the caller
- `pool.close()` discards all idle resources and causes subsequent `acquire()` calls to raise `PoolClosedError`
- `pool.stats()` returns `{"total": 5, "idle": 3, "in_use": 2, "created_count": 7, "discarded_count": 2, "timeout_count": 0}`

## Acceptance Criteria

- `ResourcePool` manages a configurable number of reusable resources with borrow/return semantics and context-manager support
- Concurrent access from multiple threads does not produce race conditions, deadlocks, or resource leaks
- Health checks discard unhealthy resources and produce fresh replacements transparently to the caller
- Idle eviction removes resources exceeding `max_idle_time` while preserving `min_size` pre-warmed resources
- `PoolExhaustedError` is raised with a descriptive message when the pool is full and the timeout elapses
- `pool.close()` drains the pool and prevents further operations
- No external dependencies are introduced; the module uses only the Python standard library
- The test suite passes with `pytest` and covers pool lifecycle, thread safety, eviction, health checks, error conditions, and statistics
