# Task: Add Malli Validation Schemas for Metabase Dashboard API Endpoints

## Background

Metabase (https://github.com/metabase/metabase) is an open-source business intelligence tool built with Clojure. The API endpoints for dashboard operations need proper request/response validation using Malli schemas. This task adds schemas for dashboard CRUD operations, parameter validation, and card layout specifications, integrated into the existing `metabase.api` namespace structure.

## Files to Create/Modify

- `src/metabase/api/dashboard/schema.clj` (create) — Malli schemas for dashboard API request/response validation
- `src/metabase/api/dashboard/validators.clj` (create) — Validation functions that apply schemas to API requests
- `test/metabase/api/dashboard/schema_test.clj` (create) — Tests for schema validation

## Requirements

### Dashboard Schema

- Define a Malli schema `:ms/Dashboard` with the following fields:
  - `:id` — `pos-int?`, required on response, absent on create request
  - `:name` — `[:string {:min 1, :max 255}]`, required
  - `:description` — `[:maybe :string]`, optional (nullable)
  - `:collection_id` — `[:maybe pos-int?]`, optional
  - `:parameters` — `[:sequential :ms/DashboardParameter]`, default `[]`
  - `:cards` — `[:sequential :ms/DashboardCard]`, default `[]`
  - `:created_at` — `inst?`, required on response
  - `:updated_at` — `inst?`, required on response
- Define separate schemas for create and update requests:
  - `:ms/DashboardCreateRequest` — requires `:name`, optional everything else, no `:id`/`:created_at`/`:updated_at`
  - `:ms/DashboardUpdateRequest` — all fields optional (partial update), no `:id`/`:created_at`/`:updated_at`

### Dashboard Parameter Schema

- Define `:ms/DashboardParameter` with:
  - `:id` — `:string`, required (UUID format)
  - `:name` — `[:string {:min 1}]`, required
  - `:slug` — `[:string {:min 1}]`, required
  - `:type` — `[:enum "date/single" "date/range" "string/=" "string/!=" "number/=" "number/between" "category"]`, required
  - `:default` — `[:maybe :any]`, optional
  - `:values_source_type` — `[:maybe [:enum "card" "static-list" "list"]]`, optional
  - `:values_source_config` — `[:maybe :map]`, optional (only valid when `values_source_type` is present)

### Dashboard Card Schema

- Define `:ms/DashboardCard` with:
  - `:id` — `pos-int?`, required on response
  - `:card_id` — `[:maybe pos-int?]` (nullable — text cards have no backing card)
  - `:row` — `nat-int?`, required (grid row position, 0-indexed)
  - `:col` — `[:and nat-int? [:< 18]]`, required (grid column, 0–17 for 18-column grid)
  - `:size_x` — `[:and pos-int? [:<= 18]]`, required (width in grid units)
  - `:size_y` — `pos-int?`, required (height in grid units)
  - `:parameter_mappings` — `[:sequential :ms/ParameterMapping]`, default `[]`
  - `:visualization_settings` — `:map`, default `{}`
- Validate: `(:col + :size_x)` must be ≤ 18 (card must not extend beyond the grid); encode this as a custom Malli validator with error message `"Card extends beyond grid boundary"`

### Parameter Mapping Schema

- Define `:ms/ParameterMapping` with:
  - `:parameter_id` — `:string`, required
  - `:card_id` — `pos-int?`, required
  - `:target` — `[:sequential :any]`, required (Metabase-specific target format like `["dimension" ["field" 123 nil]]`)

### Validation Functions

- `(validate-create-request data)` — validate against `:ms/DashboardCreateRequest`; return `{:valid true :data coerced-data}` or `{:valid false :errors [...]}` with human-readable error messages
- `(validate-update-request data)` — validate against `:ms/DashboardUpdateRequest`
- `(validate-card-layout cards)` — validate all cards in a dashboard: no overlapping positions, all within grid bounds
- Coerce types where Malli supports it: string numbers to integers, string dates to instants

### Expected Functionality

- `(validate-create-request {:name "Q1 Revenue"})` returns `{:valid true, :data {:name "Q1 Revenue", :parameters [], :cards []}}`
- `(validate-create-request {})` returns `{:valid false, :errors [{:field :name, :message "required"}]}`
- `(validate-create-request {:name ""})` returns `{:valid false, :errors [{:field :name, :message "must be at least 1 character"}]}`
- A card with `:col 16` and `:size_x 4` (16 + 4 = 20 > 18) fails validation with grid boundary error
- A parameter with `:type "invalid"` fails validation listing allowed enum values
- `(validate-card-layout [{:col 0, :row 0, :size_x 6, :size_y 4} {:col 3, :row 0, :size_x 6, :size_y 4}])` detects overlapping cards

## Acceptance Criteria

- All Malli schemas (`:ms/Dashboard`, `:ms/DashboardParameter`, `:ms/DashboardCard`, `:ms/ParameterMapping`) are defined with correct types and constraints
- Separate create and update request schemas exclude server-managed fields (`:id`, `:created_at`, `:updated_at`)
- Dashboard card grid constraint (col + size_x ≤ 18) is enforced with custom validator
- Card layout validation detects overlapping positions
- Validation functions return structured results with field-level error messages
- Type coercion converts string numbers and dates where applicable
- Tests cover valid inputs, missing required fields, type mismatches, enum violations, grid boundary violations, and overlapping card detection
