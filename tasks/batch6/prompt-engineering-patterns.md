# Task: Design a Multi-Stage Prompt Pipeline for SQL Generation from Natural Language

## Background

A production application needs a prompt engineering pipeline that converts natural language questions into correct, safe SQL queries against a specific database schema. The pipeline must handle ambiguous queries, validate generated SQL, and provide explanations. It uses few-shot examples selected by semantic similarity, chain-of-thought reasoning, and a self-verification step.

## Files to Create/Modify

- `src/prompt_pipeline/__init__.py` (create) — Package init exporting `SQLPromptPipeline`, `FewShotSelector`, `PromptTemplate`
- `src/prompt_pipeline/templates.py` (create) — Prompt templates for each stage: schema understanding, query decomposition, SQL generation, verification
- `src/prompt_pipeline/few_shot.py` (create) — `FewShotSelector` class for retrieving relevant examples by semantic similarity with diversity sampling
- `src/prompt_pipeline/pipeline.py` (create) — `SQLPromptPipeline` orchestrating the multi-stage prompt flow
- `src/prompt_pipeline/validators.py` (create) — SQL validation: syntax check, table/column existence, injection detection
- `data/few_shot_examples.jsonl` (create) — 15 few-shot examples covering various query patterns (joins, aggregations, subqueries, date filters, CASE expressions)
- `data/schema.json` (create) — Target database schema: `users`, `orders`, `products`, `order_items`, `categories` tables with columns and types
- `tests/test_pipeline.py` (create) — Tests for template rendering, few-shot selection, validation, and end-to-end pipeline

## Requirements

### Database Schema (`data/schema.json`)

Define 5 tables with relationships:
- `users` — `id` (int PK), `name` (varchar), `email` (varchar unique), `created_at` (timestamp), `tier` (varchar: 'free', 'pro', 'enterprise')
- `orders` — `id` (int PK), `user_id` (int FK→users), `status` (varchar: 'pending', 'completed', 'cancelled', 'refunded'), `total_amount` (decimal), `created_at` (timestamp)
- `products` — `id` (int PK), `name` (varchar), `category_id` (int FK→categories), `price` (decimal), `stock_quantity` (int), `is_active` (boolean)
- `order_items` — `id` (int PK), `order_id` (int FK→orders), `product_id` (int FK→products), `quantity` (int), `unit_price` (decimal)
- `categories` — `id` (int PK), `name` (varchar), `parent_category_id` (int FK→categories, nullable)

### Prompt Templates (`src/prompt_pipeline/templates.py`)

Implement 4 templates using the instruction hierarchy `[System Context] → [Task Instruction] → [Examples] → [Input Data] → [Output Format]`:

1. **Schema Understanding Template** — System prompt establishing the SQL expert role, embedding the full schema with table descriptions, column types, and foreign key relationships. Must include constraint: "Only reference tables and columns that exist in the schema."

2. **Query Decomposition Template** — Chain-of-thought template that breaks a natural language question into sub-tasks:
   - Identify required tables
   - Identify join conditions
   - Identify filter conditions
   - Identify aggregation/grouping needs
   - Identify sorting requirements
   - Output structured JSON: `{ "tables": [...], "joins": [...], "filters": [...], "aggregations": [...], "sort": [...] }`

3. **SQL Generation Template** — Takes the decomposition output and few-shot examples, generates the SQL query. Must include:
   - 3 dynamically selected few-shot examples
   - Explicit instruction to use parameterized queries for user-provided values
   - Output format: SQL in a code block followed by a one-sentence explanation

4. **Verification Template** — Self-check prompt that receives the generated SQL and schema, verifies:
   - All referenced tables exist in the schema
   - All referenced columns exist in the correct tables
   - JOIN conditions use correct foreign keys
   - WHERE clauses use correct column types
   - Output format: `{ "valid": true/false, "issues": [...], "corrected_sql": "..." }`

Each template must be a class with a `render(**kwargs) -> str` method that performs variable interpolation and validates that all required variables are provided (raising `ValueError` for missing ones).

### Few-Shot Selector (`src/prompt_pipeline/few_shot.py`)

- `FewShotSelector.__init__(examples_path: str, embedding_model: str = "text-embedding-3-small")` — loads examples from JSONL and computes embeddings.
- `FewShotSelector.select(query: str, k: int = 3, diversity_weight: float = 0.3) -> list[dict]` — returns top-k examples balancing relevance (cosine similarity) and diversity (MMR algorithm). Each example has `{"input": str, "decomposition": str, "sql": str, "explanation": str}`.
- When `k` exceeds available examples, return all examples without error.
- Diversity weight of 0.0 = pure similarity ranking; 1.0 = maximum diversity.

### SQL Validator (`src/prompt_pipeline/validators.py`)

- `validate_syntax(sql: str) -> tuple[bool, str | None]` — parse SQL using `sqlparse`, return `(True, None)` if valid or `(False, "error description")`.
- `validate_schema(sql: str, schema: dict) -> list[str]` — extract table and column references from the SQL, check against the schema, return list of issues (empty list if valid). Issues like: `"Table 'user' does not exist. Did you mean 'users'?"`.
- `detect_injection(sql: str) -> list[str]` — detect common SQL injection patterns: multiple statements (`;`), `UNION SELECT`, `DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `--` comments, `/* */` comments when not in string literals. Return list of flagged patterns.

### Pipeline (`src/prompt_pipeline/pipeline.py`)

- `SQLPromptPipeline.__init__(schema_path: str, examples_path: str, llm_client)` — initialize with schema and few-shot examples.
- `SQLPromptPipeline.generate(question: str) -> PipelineResult` — execute the full pipeline:
  1. Render schema understanding + query decomposition prompt → call LLM → get decomposition JSON
  2. Select few-shot examples based on the question
  3. Render SQL generation prompt with decomposition + examples → call LLM → get SQL
  4. Validate SQL syntax and schema compliance
  5. If validation fails, render verification prompt → call LLM → get corrected SQL
  6. Return `PipelineResult(sql=str, explanation=str, decomposition=dict, validation_issues=list, attempts=int)`
- Maximum 2 correction attempts before returning with `validation_issues` populated.

### Few-Shot Examples (`data/few_shot_examples.jsonl`)

15 examples covering:
- Simple SELECT with WHERE (2 examples)
- JOIN queries (3 examples, including multi-table joins)
- Aggregation with GROUP BY and HAVING (3 examples)
- Subqueries (2 examples)
- Date range filters using `created_at` (2 examples)
- CASE expressions (1 example)
- Combined patterns — JOIN + aggregation + date filter (2 examples)

### Expected Functionality

- `pipeline.generate("How many orders were placed last month?")` → SQL with `COUNT(*)`, date filter on `orders.created_at`, correct date arithmetic.
- `pipeline.generate("What are the top 5 products by revenue?")` → SQL joining `products`, `order_items`, `orders` (completed only), with `SUM(quantity * unit_price)`, `GROUP BY`, `ORDER BY`, `LIMIT 5`.
- `pipeline.generate("Show me users who have never placed an order")` → SQL with `LEFT JOIN` and `IS NULL` or `NOT EXISTS` subquery.
- `pipeline.generate("Drop the users table")` → injection detector flags `DROP`, pipeline refuses to generate.

## Acceptance Criteria

- The pipeline produces correct SQL for single-table queries, multi-table joins, aggregations, subqueries, and date range filters against the defined schema.
- Few-shot examples are selected by semantic similarity with configurable diversity weighting via MMR.
- The chain-of-thought decomposition step produces structured JSON identifying tables, joins, filters, aggregations, and sort.
- The verification step catches and corrects invalid table/column references in generated SQL.
- The injection detector flags destructive SQL keywords and multi-statement queries.
- All prompt templates validate required variables and raise `ValueError` when variables are missing.
- Template rendering follows the instruction hierarchy: system context → task → examples → input → output format.
