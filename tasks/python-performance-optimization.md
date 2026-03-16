# Task: Create Python Profiling Demo Scripts for py-spy

## Background
   Add practical profiling demo
   scripts to the py-spy repository that demonstrate various profiling
   scenarios and analysis workflows.

## Files to Create/Modify
   - examples/profiling_targets/cpu_bound.py (CPU-intensive workload)
   - examples/profiling_targets/io_bound.py (I/O-intensive workload)
   - examples/profiling_targets/README.md (documentation)
   - scripts/analyze_profile.py (profile analysis helper)

## Requirements
   
   CPU-Bound Example (cpu_bound.py):
   - Recursive Fibonacci calculation
   - Matrix multiplication
   - String processing loops
   - Clear hotspot functions for easy identification
   
   I/O-Bound Example (io_bound.py):
   - File operations
   - Sleep-based simulation
   - Network call simulation (localhost)
   - Threading/async patterns
   
   Analysis Script (scripts/analyze_profile.py):
   - Load py-spy output (flamegraph SVG or speedscope JSON)
   - Extract top functions by time
   - Generate summary report
   - JSON export for further analysis

4. Expected py-spy Commands:
   - `py-spy record -o profile.svg -- python examples/profiling_targets/cpu_bound.py`
   - `py-spy top -- python examples/profiling_targets/io_bound.py`

## Acceptance Criteria
   - Demo scripts run independently without py-spy
   - `python examples/profiling_targets/cpu_bound.py` exits with code 0
   - README explains how to use py-spy with examples
