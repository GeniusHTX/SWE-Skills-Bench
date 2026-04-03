# Task: Add a Task Result Aggregation Utility to Celery

## Background

Celery (https://github.com/celery/celery) is a distributed task queue framework. When running large fan-out workloads (e.g., processing thousands of items via `group`), collecting and aggregating results is cumbersome — users must manually iterate over `GroupResult` and handle failures. The task is to implement a result aggregation utility in Celery's `contrib` module that collects results from a group of tasks, handles partial failures, applies a configurable reducer, and provides progress tracking.

## Files to Create/Modify

- `celery/contrib/result_aggregator.py` (create) — `ResultAggregator` class that aggregates results from a `GroupResult` with streaming, failure handling, and reduction
- `celery/contrib/__init__.py` (modify) — Export `ResultAggregator` from the contrib package
- `t/unit/contrib/test_result_aggregator.py` (create) — Unit tests covering all aggregation modes, failure handling, and progress tracking

## Requirements

### `ResultAggregator` Class

```python
class ResultAggregator:
    def __init__(self, group_result, on_result=None, on_error=None, timeout=None, max_failures=None):
```

#### Constructor Parameters

- `group_result` — A `celery.result.GroupResult` instance containing the async results to aggregate
- `on_result` — Optional callback `Callable[[int, Any], None]` invoked with `(task_index, result)` as each task completes
- `on_error` — Optional callback `Callable[[int, Exception], None]` invoked with `(task_index, exception)` for each failed task
- `timeout` — Optional float (seconds) — maximum time to wait for all results; raises `TimeoutError` if exceeded
- `max_failures` — Optional int — if the number of failed tasks exceeds this threshold, stop aggregation early and raise `MaxFailuresExceeded`

#### Methods

- `collect() -> AggregationResult`:
  - Iterates over all tasks in the `group_result`
  - Calls `.get(timeout=self.timeout, propagate=False)` on each `AsyncResult`
  - Classifies each result as succeeded or failed (a result is failed if it is an `Exception` instance)
  - Invokes `on_result` for successes and `on_error` for failures
  - If `max_failures` is set and the failure count exceeds it, raises `MaxFailuresExceeded` with the partial results collected so far
  - Returns an `AggregationResult` instance

- `reduce(func, initial=None) -> Any`:
  - Calls `collect()`, then applies `functools.reduce(func, results.succeeded, initial)` to the successful results
  - Returns the reduced value

- `filter(predicate) -> list`:
  - Calls `collect()`, then returns `[r for r in results.succeeded if predicate(r)]`

### `AggregationResult` Class

```python
@dataclass
class AggregationResult:
    succeeded: list[Any]          # Results from successful tasks, in order
    failed: list[FailedTask]      # List of FailedTask entries
    total: int                    # Total number of tasks
    success_count: int            # Number of succeeded tasks
    failure_count: int            # Number of failed tasks
    elapsed: float                # Wall-clock seconds from start to last result

    @property
    def success_rate(self) -> float:
        return self.success_count / self.total if self.total > 0 else 0.0

    @property
    def is_complete(self) -> bool:
        return self.success_count + self.failure_count == self.total
```

### `FailedTask` Class

```python
@dataclass
class FailedTask:
    index: int                    # Position in the group
    task_id: str                  # Celery task ID
    exception: Exception          # The exception that was raised
```

### `MaxFailuresExceeded` Exception

```python
class MaxFailuresExceeded(Exception):
    def __init__(self, message, partial_result: AggregationResult):
        super().__init__(message)
        self.partial_result = partial_result
```

### Behavioral Requirements

- Results in `succeeded` must preserve the original task order within the group (index 0 first, then index 1, etc.)
- Failed tasks must not appear in `succeeded` — they appear only in `failed`
- If `timeout` is reached before all tasks complete, raise `TimeoutError` with the partial `AggregationResult` attached as an attribute `.partial_result`
- `collect()` must be idempotent — calling it multiple times returns the same result (cache the result internally)
- `reduce()` and `filter()` must call `collect()` internally (not require the user to call it first)
- All callbacks (`on_result`, `on_error`) must be called synchronously during `collect()` execution

## Expected Functionality

- Given a group of 5 tasks where tasks 0, 1, 3, 4 succeed and task 2 raises `ValueError("bad input")`:
  - `collect()` returns `AggregationResult` with `success_count=4`, `failure_count=1`, `failed=[FailedTask(index=2, ...)]`
  - `reduce(operator.add)` returns the sum of the 4 successful results
  - `filter(lambda x: x > 10)` returns only successful results greater than 10
- Given `max_failures=2` and 3 tasks fail: `collect()` raises `MaxFailuresExceeded` after the 3rd failure
- Given `timeout=5.0` and tasks take 10 seconds: `collect()` raises `TimeoutError` with partial results

## Acceptance Criteria

- `ResultAggregator` correctly classifies task results as succeeded or failed
- Results in `succeeded` preserve the original group ordering
- `on_result` and `on_error` callbacks are invoked for each corresponding task
- `max_failures` threshold stops aggregation early and raises `MaxFailuresExceeded` with partial results
- `timeout` raises `TimeoutError` when exceeded
- `reduce()` applies `functools.reduce` over successful results only
- `filter()` returns only successful results matching the predicate
- `collect()` is idempotent across multiple calls
- `AggregationResult.success_rate` returns the correct ratio
- All classes and exceptions are importable from `celery.contrib.result_aggregator`
