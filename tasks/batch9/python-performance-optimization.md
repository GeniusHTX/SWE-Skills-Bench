# Task: Add a Configurable Flame Graph Renderer to py-spy

## Background

py-spy (https://github.com/benfred/py-spy) is a sampling profiler for Python written in Rust. A new Rust module is needed that implements a configurable flame graph renderer: reading py-spy's collapsed stack format, computing frame statistics (self time, total time, sample count), supporting multiple color schemes, generating interactive SVG flame graphs with search and zoom, and exporting profile data in multiple formats (JSON, speedscope, pprof).

## Files to Create/Modify

- `src/flamegraph/mod.rs` (create) — Module declaration and public API: `FlamegraphRenderer` struct and `render()` function
- `src/flamegraph/parser.rs` (create) — Parser for collapsed stack format: `parse_collapsed(input: &str) -> Vec<StackSample>` where each line is `frame1;frame2;frameN count`
- `src/flamegraph/tree.rs` (create) — `FlameTree` data structure that aggregates collapsed stacks into a tree with cumulative and self sample counts per node
- `src/flamegraph/svg.rs` (create) — SVG renderer that generates interactive flame graph SVGs with configurable width, frame height, color palette, and embedded JavaScript for search/zoom
- `src/flamegraph/colors.rs` (create) — Color scheme implementations: `Hot` (red-yellow gradient by self time), `Cold` (blue-green by total time), `Differential` (red for regression, blue for improvement), `Language` (color by runtime: Python=green, C=orange, kernel=red)
- `src/flamegraph/export.rs` (create) — Export functions: `to_json()`, `to_speedscope()`, `to_pprof()` format converters
- `src/flamegraph/config.rs` (create) — `FlamegraphConfig` struct with all rendering options
- `tests/flamegraph_test.rs` (create) — Unit tests for parser, tree building, color assignment, and SVG output

## Requirements

### Config (`config.rs`)

- `FlamegraphConfig` struct:
  - `width: u32` (default 1200, SVG width in pixels)
  - `frame_height: u32` (default 16, height per stack frame)
  - `min_width: f64` (default 0.1, minimum frame width as percentage; frames below this are hidden)
  - `color_scheme: ColorScheme` (enum: Hot, Cold, Differential, Language)
  - `title: String` (default "Flame Graph")
  - `count_name: String` (default "samples", unit label for counts)
  - `reverse: bool` (default false, if true render icicle graph top-down)
  - `font_size: u32` (default 12)
  - `search_enabled: bool` (default true)
- Implement `Default` for `FlamegraphConfig`

### Parser (`parser.rs`)

- Struct `StackSample`: `frames: Vec<String>`, `count: u64`
- Function `parse_collapsed(input: &str) -> Result<Vec<StackSample>, ParseError>`:
  - Each line format: `frame1;frame2;...;frameN count`
  - Split on last space to separate stack from count
  - Split stack on `;` to get individual frames
  - Skip empty lines and lines starting with `#` (comments)
  - Return error if count is not a valid u64
  - Trim whitespace from frame names
- Function `parse_differential(input: &str) -> Result<Vec<DiffSample>, ParseError>`:
  - Format: `frame1;frame2;frameN base_count,comp_count`
  - `DiffSample`: `frames`, `base_count`, `comp_count`, `delta` (comp - base)

### Flame Tree (`tree.rs`)

- Struct `FlameNode`: `name: String`, `total_count: u64`, `self_count: u64`, `children: Vec<FlameNode>`, `depth: usize`
- Struct `FlameTree`: `root: FlameNode`, `total_samples: u64`, `max_depth: usize`
- Method `FlameTree::from_samples(samples: &[StackSample]) -> FlameTree`:
  - Build tree by matching common prefixes
  - `total_count` for each node = sum of all samples passing through it
  - `self_count` = total_count - sum(children.total_count)
  - Root node name = "all", total_count = sum of all sample counts
- Method `FlameNode::width_ratio(&self, total: u64) -> f64` — Returns `total_count as f64 / total as f64`
- Method `FlameTree::prune(min_ratio: f64) -> &mut Self` — Remove nodes below `min_ratio` width

### SVG Renderer (`svg.rs`)

- Function `render_svg(tree: &FlameTree, config: &FlamegraphConfig) -> String`:
  - SVG header with viewBox based on `config.width` and `max_depth * frame_height + header_height`
  - Each frame rendered as `<rect>` with `<title>` tooltip showing: `{name} ({count} {count_name}, {percentage}%)`
  - Frame text clipped to frame width; hidden if too small
  - Color assigned from `config.color_scheme`
  - If `reverse` is true, root is at top (icicle graph)
  - Embedded `<script>` for search functionality: highlights matching frames by name, dims non-matching
  - Search input: `<foreignObject>` with HTML input field at the top
  - Zoom: clicking a frame re-renders with that frame as root (JavaScript zoom)
- Frame positioning: x based on cumulative offset among siblings, y based on depth
- Total SVG height: `(max_depth + 2) * frame_height`

### Color Schemes (`colors.rs`)

- Trait `ColorMapper`: `fn color(&self, node: &FlameNode, tree: &FlameTree) -> (u8, u8, u8)`
- `HotColorMapper` — Maps self_count ratio to red-yellow gradient: high self time = red, low = yellow
  - RGB: `(205 + 50 * ratio, 230 * (1 - ratio), 55 * (1 - ratio))` clamped to 0-255
- `ColdColorMapper` — Maps total_count ratio to blue-cyan gradient
- `DifferentialColorMapper` — For diff flamegraphs: delta > 0 = red intensity proportional to increase, delta < 0 = blue intensity proportional to decrease, delta = 0 = gray
- `LanguageColorMapper` — Detects language from frame name patterns:
  - Python frames (containing `.py:` or `<module>`): green
  - C/C++ frames (no `.py` extension): orange
  - Kernel frames (starting with `[kernel]` or containing `vmlinux`): red
  - Unknown: gray

### Export (`export.rs`)

- Function `to_json(tree: &FlameTree) -> String` — Recursive JSON: `{"name": "...", "value": N, "children": [...]}`
- Function `to_speedscope(samples: &[StackSample], config: &FlamegraphConfig) -> String` — Speedscope JSON format:
  - `{"$schema": "https://www.speedscope.app/file-format-schema.json", "shared": {"frames": [...]}, "profiles": [{"type": "sampled", "samples": [...], "weights": [...]}]}`
  - Frames are deduplicated with indices
- Function `to_pprof(tree: &FlameTree) -> Vec<u8>` — Protocol buffer bytes in pprof format (string table, samples, locations)

### Expected Functionality

- Parsing `"main;foo;bar 10\nmain;foo;baz 5\nmain;qux 3"` produces a tree where `main` has total=18, `foo` has total=15, `bar` has self=10
- SVG output for a 3-level tree with config width=1200 produces valid SVG with `<rect>` elements and embedded search JavaScript
- Hot color scheme assigns redder colors to frames with higher self-time ratios
- Differential color scheme shows regressions in red and improvements in blue
- Speedscope export produces valid JSON matching the speedscope schema

## Acceptance Criteria

- Parser correctly handles collapsed stack format including edge cases (empty lines, comments, whitespace)
- FlameTree correctly computes total_count and self_count for all nodes
- SVG output is valid XML with correct viewBox dimensions
- Search functionality in SVG highlights frames by name match
- All four color schemes produce valid RGB values (0-255 range)
- JSON export produces valid recursive structure
- Speedscope export matches the expected schema with deduplicated frames
- `cargo build --release` compiles successfully
- `python -m pytest /workspace/tests/test_python_performance_optimization.py -v --tb=short` passes
