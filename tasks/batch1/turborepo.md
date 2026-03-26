# Task: Create Turborepo Monorepo Example with Cache Demonstration

## Background

We need a complete monorepo example in the `examples/` directory that demonstrates Turborepo's task caching and incremental build mechanisms.

## Project Structure

Create the following structure:

```
examples/cache-demo/
├── package.json
├── turbo.json
├── benchmark.sh
└── packages/
    ├── core/
    │   ├── package.json
    │   └── src/index.ts
    ├── utils/
    │   ├── package.json
    │   └── src/index.ts
    └── app/
        ├── package.json
        └── src/index.ts
```

## Requirements

### Root Configuration

- `examples/cache-demo/package.json` - Root package with workspace configuration
- `examples/cache-demo/turbo.json` - Pipeline configuration

### turbo.json Pipeline Configuration

Define tasks with proper caching:

- **build**: Configure outputs, inputs, dependsOn
- **lint**: Configure caching
- **test**: Configure caching

Key fields to configure:
- `"outputs"`: Specify build output directories
- `"inputs"`: Specify input file patterns
- `"dependsOn"`: Define task dependencies (use `^build` for workspace dependencies)

### Benchmark Script

Create `benchmark.sh` that:
- Runs build twice consecutively
- Measures and compares build times
- Displays cache hit information

### Expected Behavior

- **First build**: Full compilation
- **Second build**: Cache hit (should show "FULL TURBO")
- Significant time reduction on second run

## Acceptance Criteria

- `cd examples/cache-demo && bash benchmark.sh` runs successfully
- Second build shows "FULL TURBO" or "cache hit" in output
- Build time significantly reduced on cache hit
