# Task: Build an MCP Server for Markdown-to-SQLite Operations

## Background

The Model Context Protocol (MCP) servers repository (https://github.com/modelcontextprotocol/servers) hosts reference server implementations under `src/`. Each server is a self-contained npm workspace package exposing tools that LLMs can invoke. A new `markdown-sqlite` server is needed that allows an LLM to ingest Markdown files, parse their structure into a normalized SQLite database, and query the resulting tables.

## Files to Create/Modify

- `src/markdown-sqlite/package.json` (create) — Package manifest with dependencies (`@modelcontextprotocol/sdk`, `better-sqlite3`, `marked` or similar).
- `src/markdown-sqlite/tsconfig.json` (create) — TypeScript configuration extending the repo conventions.
- `src/markdown-sqlite/src/index.ts` (create) — Server entry point: initializes the MCP server, registers tools, and starts the stdio transport.
- `src/markdown-sqlite/src/tools/ingest.ts` (create) — Implements the `ingest_markdown` tool: reads a Markdown file, parses headings/paragraphs/code blocks/lists into rows, and stores them in a SQLite database.
- `src/markdown-sqlite/src/tools/query.ts` (create) — Implements the `query_db` tool: executes a read-only SQL query against the ingested database and returns results.
- `src/markdown-sqlite/src/tools/list-tables.ts` (create) — Implements the `list_tables` tool: returns the schema of all tables in the current database.
- `src/markdown-sqlite/src/db.ts` (create) — SQLite database initialization and helper functions (create tables, insert rows, execute queries).

## Requirements

### Tool: `ingest_markdown`

- Accepts parameters: `file_path` (string, required — path to a Markdown file) and `db_path` (string, optional — SQLite file path, defaults to `:memory:`).
- Parses the Markdown file into structural elements: headings (level 1–6), paragraphs, code blocks (with language annotation), and list items.
- Stores each element as a row in a `documents` table with columns: `id` (auto-increment), `file_path`, `element_type` (heading/paragraph/code_block/list_item), `heading_level` (nullable), `content` (text), `position` (ordinal position within the file), `parent_heading_id` (nullable FK referencing the nearest ancestor heading).
- Multiple files can be ingested into the same database; re-ingesting the same file replaces its previous rows.
- Invalid or non-existent file paths return a structured error message (not a server crash).

### Tool: `query_db`

- Accepts parameters: `db_path` (string, required) and `sql` (string, required).
- Executes the SQL query in read-only mode and returns up to 100 rows as a JSON array.
- Queries that attempt `INSERT`, `UPDATE`, `DELETE`, or `DROP` must be rejected before execution.
- SQL syntax errors return a descriptive error message.

### Tool: `list_tables`

- Accepts parameter: `db_path` (string, required).
- Returns the names and column definitions of all tables in the database as structured JSON.

### Tool Schemas

- Every tool must have a Zod (or JSON Schema) input schema with required/optional annotations and descriptions for each parameter.
- Tool names must follow the `snake_case` convention used in the existing servers.

### Expected Functionality

- Ingesting a 50-line Markdown file with 3 H1 sections, nested H2 subsections, code blocks, and lists → `documents` table contains one row per structural element with correct `element_type`, `heading_level`, and `parent_heading_id` relationships.
- `query_db` with `SELECT element_type, COUNT(*) FROM documents GROUP BY element_type` → returns counts per element type.
- `query_db` with `DROP TABLE documents` → rejected with an error indicating write operations are not allowed.
- `list_tables` on a freshly ingested DB → returns `documents` table with its column names and types.
- `ingest_markdown` with a non-existent file → returns an error message containing the file path.

## Acceptance Criteria

- `npm run build` in `src/markdown-sqlite` completes without TypeScript or bundling errors.
- The server starts via stdio transport and responds to MCP `initialize` and `tools/list` requests, advertising exactly three tools.
- `ingest_markdown` correctly parses headings, paragraphs, code blocks, and list items from a Markdown file into the SQLite `documents` table.
- `query_db` executes valid read-only SQL and returns results; write SQL is rejected with a descriptive error.
- `list_tables` returns accurate schema information for all tables in the database.
- Each tool has a complete input schema with typed, described parameters.
