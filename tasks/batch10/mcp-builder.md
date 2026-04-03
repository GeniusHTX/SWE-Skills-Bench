# Task: Build a Markdown-to-SQLite MCP Server

## Background

The MCP servers monorepo (https://github.com/modelcontextprotocol/servers) contains various Model Context Protocol server implementations under `src/`. A new server called `markdown-sqlite` is needed that allows LLMs to ingest a collection of Markdown files, store their content and metadata in a SQLite database, and query them through MCP tools. The server must be implemented in TypeScript using the MCP SDK, compile cleanly, and expose well-designed tools for ingestion and querying.

## Files to Create/Modify

- `src/markdown-sqlite/package.json` (new) — Package manifest with build script, MCP SDK dependency (`@modelcontextprotocol/sdk`), `zod`, `better-sqlite3`, and TypeScript tooling
- `src/markdown-sqlite/tsconfig.json` (new) — TypeScript configuration targeting ES2022+ with strict mode, outputting to `dist/`
- `src/markdown-sqlite/src/index.ts` (new) — Server entry point: registers tools, sets up stdio transport, initializes SQLite database
- `src/markdown-sqlite/src/db.ts` (new) — SQLite database initialization and query helpers; creates tables for documents (path, title, content, frontmatter, last_modified)
- `src/markdown-sqlite/src/tools.ts` (new) — Tool definitions and handlers for ingest, search, list, and get operations
- `src/markdown-sqlite/README.md` (new) — Usage instructions, tool descriptions, and example invocations

## Requirements

### Database Schema

- Table `documents` with columns: `id` (INTEGER PRIMARY KEY), `path` (TEXT UNIQUE NOT NULL), `title` (TEXT), `content` (TEXT NOT NULL), `frontmatter` (TEXT, JSON string of parsed YAML frontmatter), `last_modified` (TEXT ISO-8601 timestamp)
- Create the table on server startup if it does not exist
- `path` column must enforce uniqueness so re-ingesting the same file updates the existing row

### Tools

#### `ingest_markdown`
- Input: `directory` (string, required) — absolute path to a directory of `.md` files
- Behavior: recursively scans the directory for `*.md` files, parses YAML frontmatter (if present) and body content, upserts each file into the `documents` table
- Returns: a JSON object with `ingested_count` (number of files processed) and `errors` (array of `{ path, message }` for files that failed to parse)
- Must not crash if a single file is unreadable; collect errors and continue

#### `search_documents`
- Input: `query` (string, required), `limit` (number, optional, default 20, max 100)
- Behavior: performs a case-insensitive substring search across `title` and `content` columns
- Returns: array of `{ id, path, title, snippet }` where `snippet` is up to 200 characters of context around the first match

#### `list_documents`
- Input: `page` (number, optional, default 1), `page_size` (number, optional, default 50, max 200)
- Behavior: returns paginated document listing ordered by `path`
- Returns: `{ documents: [{ id, path, title, last_modified }], total_count, page, page_size }`

#### `get_document`
- Input: `id` (number) OR `path` (string) — at least one must be provided
- Behavior: retrieves a single document's full content and metadata
- Returns: `{ id, path, title, content, frontmatter, last_modified }` or an error if not found

### Input Validation

- All tool inputs must be validated with Zod schemas
- `limit` and `page_size` must be clamped to their maximums, not rejected
- `get_document` must return a clear error when neither `id` nor `path` is provided
- `ingest_markdown` must return an error if the directory does not exist or is not readable

### Error Handling

- Tool handlers must never throw unhandled exceptions to the transport layer
- Database errors must be caught and returned as structured error content with `isError: true`
- File system errors during ingestion (permission denied, binary file, etc.) must be collected per-file and reported in the `errors` array, not halt the entire operation

### Tool Annotations

- `ingest_markdown`: mark as not read-only, not idempotent, not destructive
- `search_documents`, `list_documents`, `get_document`: mark as read-only

### Build

- `npm run build` must invoke `tsc` and produce JavaScript output in `dist/`
- The compiled entry point must be executable via `node dist/index.js`

## Acceptance Criteria

- `cd src/markdown-sqlite && npm install && npm run build` completes with exit code 0 and no TypeScript compilation errors
- All four tools (`ingest_markdown`, `search_documents`, `list_documents`, `get_document`) are registered and appear in the server's tool listing
- Each tool has a Zod-validated input schema with descriptive field documentation
- `ingest_markdown` on a directory containing valid and invalid `.md` files returns a count of successes and a per-file error array without crashing
- `search_documents` returns matching results with contextual snippets and respects the `limit` parameter
- `list_documents` returns paginated results with correct `total_count`
- `get_document` returns full document content when found and a structured error when not found
- No unhandled promise rejections or uncaught exceptions propagate to the transport on any tool call
- Tool annotations correctly reflect read-only vs. mutating behavior
