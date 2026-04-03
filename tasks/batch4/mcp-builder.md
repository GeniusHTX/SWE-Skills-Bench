# Task: Build an MCP Server for Markdown-to-SQLite Conversion

## Background

The MCP servers repository (https://github.com/modelcontextprotocol/servers) hosts reference implementations of Model Context Protocol servers. A new TypeScript-based MCP server is needed under `src/markdown-sqlite` that enables LLMs to ingest Markdown documents, store their structured content in a SQLite database, and query that content through MCP tools. The server must follow the repository's established project conventions and expose a well-designed set of tools for document management and querying.

## Files to Create/Modify

- `src/markdown-sqlite/package.json` (create) — Package manifest with build scripts, dependencies (MCP SDK, better-sqlite3, Zod), and `bin` entry
- `src/markdown-sqlite/tsconfig.json` (create) — TypeScript configuration extending the repository's base config
- `src/markdown-sqlite/src/index.ts` (create) — Server entry point: transport setup, tool registration, and server lifecycle
- `src/markdown-sqlite/src/db.ts` (create) — SQLite database initialization, schema creation, and query helpers
- `src/markdown-sqlite/src/tools/ingest.ts` (create) — Tool implementation for parsing and storing Markdown documents
- `src/markdown-sqlite/src/tools/query.ts` (create) — Tool implementation for searching and retrieving stored content
- `src/markdown-sqlite/src/tools/list.ts` (create) — Tool implementation for listing ingested documents and their metadata

## Requirements

### Server Configuration

- The server must use stdio transport for local execution
- The package must compile with `npm run build` and produce a runnable entry point
- The `package.json` must specify a `bin` field pointing to the compiled entry point

### Tool Definitions

The server must expose the following tools:

**`ingest_markdown`**
- Input: `filePath` (string, required) — path to a Markdown file; `tags` (string array, optional) — metadata tags
- Behavior: reads the file, parses it into sections (split on `## ` headings), stores each section as a row in SQLite with the document title, section heading, section body, file path, and ingestion timestamp
- Output: number of sections ingested and the assigned document ID
- Must reject files that are not readable or exceed 1 MB with an actionable error message

**`query_content`**
- Input: `query` (string, required) — substring to search for; `tag` (string, optional) — filter by tag; `limit` (integer, optional, default 10, max 100)
- Behavior: searches section bodies and headings using SQL `LIKE` (case-insensitive), returns matching sections with document title, heading, a snippet of the body (first 200 characters), and the file path
- Output: array of matching section objects

**`list_documents`**
- Input: `tag` (string, optional) — filter by tag
- Behavior: returns all ingested documents with title, file path, section count, tags, and ingestion timestamp
- Output: array of document summary objects

### Database Schema

- The SQLite database must be stored at a configurable path (default: `./mcp-markdown.db`)
- Tables: `documents` (id, title, file_path, tags as JSON string, ingested_at) and `sections` (id, document_id FK, heading, body, position)
- Ingesting the same file path a second time must replace the previous version (upsert semantics)

### Input Validation and Error Handling

- All tool inputs must be validated with Zod schemas
- Invalid inputs must return error messages that describe what was wrong and how to fix it
- Database errors must be caught and returned as user-friendly messages without exposing internal stack traces

### Tool Annotations

- `ingest_markdown` must be annotated as non-read-only and non-idempotent
- `query_content` and `list_documents` must be annotated as read-only

### Expected Functionality

- Ingesting a 50-section Markdown file creates 50 rows in `sections` and 1 row in `documents`
- Re-ingesting the same file path replaces the old sections; section count reflects only the latest version
- `query_content` with query `"install"` returns only sections whose heading or body contains "install" (case-insensitive)
- `query_content` with `limit: 2` returns at most 2 results
- `list_documents` with no tag filter returns all documents; with `tag: "api"` returns only documents tagged "api"
- Ingesting a 2 MB file returns an error message stating the file exceeds the 1 MB limit
- Calling `query_content` with an empty `query` string returns a validation error

## Acceptance Criteria

- `npm run build` in `src/markdown-sqlite` completes without errors
- The server starts via stdio and registers three tools (`ingest_markdown`, `query_content`, `list_documents`)
- Ingesting a valid Markdown file stores structured sections in SQLite and returns the correct section count
- Re-ingesting the same file replaces previous data without duplicating sections
- Query results match the search term case-insensitively and respect the limit parameter
- Document listing returns correct metadata including section counts and tags
- Invalid inputs (missing required fields, oversized files, empty queries) produce descriptive error responses
- Tool annotations correctly reflect read-only vs. mutating behavior
