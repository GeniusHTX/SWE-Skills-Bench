# Task: Build a Markdown-to-SQLite MCP Server

## Background

The MCP servers repository (https://github.com/modelcontextprotocol/servers) hosts official Model Context Protocol server implementations. A new `markdown-sqlite` server is needed that ingests Markdown files, parses their structure (headings, paragraphs, code blocks, lists, front-matter), stores the parsed content in a SQLite database, and exposes MCP tools for querying and searching the indexed content. This enables LLMs to semantically explore and retrieve information from large Markdown documentation sets.

## Files to Create/Modify

- `src/markdown-sqlite/index.ts` (create) — Server entry point: initializes STDIO transport, registers all MCP tools, connects to SQLite database
- `src/markdown-sqlite/lib.ts` (create) — Core logic: Markdown parsing (headings, paragraphs, code blocks, lists, YAML front-matter), SQLite schema creation, document indexing, and query execution
- `src/markdown-sqlite/package.json` (create) — Package manifest with dependencies: `@modelcontextprotocol/sdk`, `zod`, `better-sqlite3`, `gray-matter`, `marked`; build and start scripts
- `src/markdown-sqlite/tsconfig.json` (create) — TypeScript configuration extending the root `tsconfig.json`
- `src/markdown-sqlite/README.md` (create) — Server documentation describing tools, installation, and usage
- `src/markdown-sqlite/__tests__/lib.test.ts` (create) — Unit tests for Markdown parsing, SQLite indexing, and query logic using vitest

## Requirements

### SQLite Schema

- Table `documents`: columns `id` (INTEGER PRIMARY KEY), `path` (TEXT UNIQUE NOT NULL), `title` (TEXT), `front_matter` (TEXT, JSON-encoded), `indexed_at` (TEXT, ISO 8601 timestamp)
- Table `sections`: columns `id` (INTEGER PRIMARY KEY), `document_id` (INTEGER FK → documents.id), `heading` (TEXT), `level` (INTEGER 1–6), `content` (TEXT), `section_order` (INTEGER)
- Table `code_blocks`: columns `id` (INTEGER PRIMARY KEY), `section_id` (INTEGER FK → sections.id), `language` (TEXT), `code` (TEXT), `block_order` (INTEGER)
- Create a full-text search virtual table `sections_fts` using FTS5 on `heading` and `content` columns

### MCP Tools

- `index_directory` — Accepts parameters `{ path: string, glob?: string }`. Recursively scans the directory for `.md` files (filtered by glob if provided), parses each file, and upserts into the SQLite tables. Returns `{ indexed: number, errors: string[] }` as structured output
- `search` — Accepts `{ query: string, limit?: number }`. Performs FTS5 search on `sections_fts`, returns matching sections with their document path, heading, content snippet (first 200 characters), and relevance rank. Default limit is 10
- `get_document` — Accepts `{ path: string }`. Returns the full parsed document including all sections and code blocks. Returns an error if the path is not indexed
- `list_documents` — Accepts `{ front_matter_filter?: Record<string, string> }`. Lists all indexed documents. If `front_matter_filter` is provided, returns only documents whose parsed front-matter contains matching key-value pairs
- `get_code_blocks` — Accepts `{ language?: string, document_path?: string }`. Returns code blocks optionally filtered by language and/or document path

### Markdown Parsing

- YAML front-matter delimited by `---` must be parsed into a JSON object and stored in `documents.front_matter`
- Headings (`#` through `######`) must create new sections; content between headings belongs to the preceding section
- Fenced code blocks (triple backtick) must be extracted with their language identifier and stored in `code_blocks`
- A Markdown file with no headings must produce a single section with `heading = NULL` and `level = 0`

### Error Handling

- `index_directory` on a non-existent path must return an error message "Directory not found: <path>" (not throw)
- `get_document` for a non-indexed path must return an error message "Document not indexed: <path>"
- `search` with an empty query must return an error message "Query must not be empty"
- All tool errors must use `isError: true` in the MCP response content

### Expected Functionality

- Indexing a directory with 3 Markdown files (one with YAML front-matter, one with nested headings, one with code blocks) produces correct `documents`, `sections`, and `code_blocks` rows
- Searching for "installation" returns sections whose heading or content contains that term
- `list_documents` with `front_matter_filter: { "category": "guide" }` returns only documents whose front-matter has `category: guide`
- `get_code_blocks` with `language: "python"` returns only Python code blocks

## Acceptance Criteria

- `cd src/markdown-sqlite && npm run build` compiles without errors
- All 5 MCP tools are registered and respond to `tools/list` with correct names, descriptions, and input schemas
- `index_directory` correctly parses Markdown with front-matter, headings, and code blocks into the SQLite database
- FTS5 search returns relevant results ranked by relevance
- `get_document` and `list_documents` return complete structured data matching the indexed content
- Error cases return `isError: true` with descriptive messages instead of throwing exceptions
- Unit tests in `__tests__/lib.test.ts` pass via `npx vitest run`
