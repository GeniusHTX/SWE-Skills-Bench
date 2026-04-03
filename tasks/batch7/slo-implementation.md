# Task: Add a Multi-Window SLO Evaluator to slo-generator

## Background

The slo-generator (https://github.com/google/slo-generator) is a Python framework for computing SLO reports from various backends. The task is to implement a `MultiWindowSloEvaluator` class that computes SLO compliance and error budget consumption across multiple rolling time windows simultaneously (1h, 6h, 24h, 72h), and generates burnrate alerts following the Google SRE multi-window alerting model.

## Files to Create/Modify

- `slo_generator/evaluators/multi_window.py` (create) — `MultiWindowSloEvaluator` that evaluates an SLO across multiple time windows in one pass
- `slo_generator/evaluators/burnrate.py` (create) — `BurnRateCalculator` that computes burnrate and generates alert conditions
- `tests/unit/test_multi_window_evaluator.py` (create) — Unit tests for the evaluator and burnrate calculator

## Requirements

### `BurnRateCalculator` (`burnrate.py`)

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class WindowResult:
    window_hours: float
    good_events: float
    total_events: float
    slo_target: float        # e.g., 0.999
    
    @property
    def error_rate(self) -> float:
        """Fraction of bad events: (total - good) / total. Returns 0 if total is 0."""
    
    @property
    def sli(self) -> float:
        """SLI = good / total. Returns 1.0 if total is 0."""
    
    @property
    def error_budget_consumed(self) -> float:
        """Fraction of error budget consumed: error_rate / (1 - slo_target)."""
    
    @property
    def compliant(self) -> bool:
        """True if sli >= slo_target."""
    
    @property
    def burnrate(self) -> float:
        """Error budget burn rate: error_budget_consumed / (window_hours / (30*24)).
        e.g., for 1h window and 30-day budget: factor = 1/(30*24) = 1/720.
        burnrate = error_budget_consumed / (1/720) = error_budget_consumed * 720."""

@dataclass
class BurnRateAlert:
    severity: str        # "page" or "ticket"
    short_window_hours: float
    long_window_hours: float
    burnrate_threshold: float
    triggered: bool
    message: str

class BurnRateCalculator:
    """Implements Google's multi-window multi-burnrate alerting model."""
    
    ALERT_CONFIGS = [
        # (short_window_h, long_window_h, burnrate_threshold, severity)
        (1,   6,  14.4, "page"),
        (6,  24,   6.0, "page"),
        (24, 72,   3.0, "ticket"),
    ]
    
    def compute_alerts(
        self,
        results: dict[float, WindowResult],  # key = window_hours
        budget_period_hours: float = 720,    # 30 days
    ) -> list[BurnRateAlert]:
        """
        For each alert config (short_w, long_w, threshold, severity):
        - Look up short_window result and long_window result from `results`
        - Triggered if both short_window.burnrate > threshold AND long_window.burnrate > threshold
        - Message must include the window sizes and actual burnrate values
        """
```

### `MultiWindowSloEvaluator` (`multi_window.py`)

```python
from typing import Protocol

class SliBackend(Protocol):
    def get_good_events(self, slo_config: dict, window_hours: float) -> float: ...
    def get_total_events(self, slo_config: dict, window_hours: float) -> float: ...

class MultiWindowSloEvaluator:
    DEFAULT_WINDOWS = [1.0, 6.0, 24.0, 72.0]
    
    def __init__(
        self,
        backend: SliBackend,
        windows_hours: list[float] = None,
        budget_period_hours: float = 720,
    ):
        self.backend = backend
        self.windows_hours = windows_hours or self.DEFAULT_WINDOWS
        self.budget_period_hours = budget_period_hours
    
    def evaluate(self, slo_config: dict) -> "SloEvaluationReport":
        """
        For each window in self.windows_hours:
        1. Call backend.get_good_events(slo_config, window_hours)
        2. Call backend.get_total_events(slo_config, window_hours)
        3. Build a WindowResult
        Compute burnrate alerts using BurnRateCalculator.
        Return SloEvaluationReport.
        """
```

#### `SloEvaluationReport`

```python
@dataclass
class SloEvaluationReport:
    slo_name: str                         # from slo_config["name"]
    slo_target: float                     # from slo_config["slo_target"]
    budget_period_hours: float
    windows: dict[float, WindowResult]    # key = window_hours
    alerts: list[BurnRateAlert]
    
    @property
    def overall_compliant(self) -> bool:
        """True only if ALL windows are compliant."""
    
    @property
    def worst_window(self) -> WindowResult:
        """The WindowResult with the lowest SLI value."""
    
    def to_dict(self) -> dict:
        """Serializable dictionary for downstream consumption / export."""
```

#### `slo_config` Schema

Expected keys:
```python
{
    "name": "api-availability",
    "slo_target": 0.999,
    "backend": "prometheus",   # (not used by the evaluator itself)
    # additional backend-specific keys passed through to the backend
}
```

### Burnrate Alert Triggering Logic

Given `burnrate_threshold = 14.4` and windows `(1h, 6h)`:
- Look up `results[1.0].burnrate` and `results[6.0].burnrate`
- Set `triggered = True` if BOTH are > 14.4
- `message = "HIGH BURNRATE: 1h burnrate=16.2x, 6h burnrate=15.1x exceeds 14.4x threshold (page)"`

All three alert configs must be evaluated independently. Multiple alerts can trigger simultaneously.

## Expected Functionality

- Given `slo_target=0.999` and `good_events=990`, `total_events=1000` (99.0% SLI):
  - `error_rate = 0.01`
  - `error_budget_consumed = 0.01 / (1 - 0.999) = 10.0` (10x over budget)
  - For a 1h window: `burnrate = 10.0 / (1/720) = 7200` (720x)
- With `slo_target=0.999` over 1h and 6h windows both showing burnrate > 14.4: the `"page"` alert with `(1, 6, 14.4)` config is triggered
- With burnrate of 5.0 in the 24h window and 4.0 in the 72h window: no alert triggers (neither exceeds 6.0 for the (6h, 24h) pair since the 6h window isn't 5.0)
- `overall_compliant` is `False` if any window's SLI falls below `slo_target`

## Acceptance Criteria

- `WindowResult` properties correctly calculate `error_rate`, `sli`, `error_budget_consumed`, `compliant`, and `burnrate`
- `MultiWindowSloEvaluator.evaluate` calls backend for each window and builds correct `WindowResult` objects
- `BurnRateCalculator.compute_alerts` returns the correct `BurnRateAlert` objects: triggered when both windows exceed threshold
- `SloEvaluationReport.overall_compliant` requires ALL windows to be compliant
- `SloEvaluationReport.worst_window` returns the window with the minimum SLI value
- `to_dict()` returns a serializable dictionary without non-JSON-serializable objects
- Division by zero is handled gracefully when `total_events = 0`
- All unit tests pass with mock backends returning synthetic event counts
