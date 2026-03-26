# Task: Build an MCP Server with Tool Registration and Schema Validation

## Background

The Model Context Protocol servers repository (https://github.com/modelcontextprotocol/servers) hosts reference implementations of MCP servers. The project needs a new MCP server — `markdown-sqlite` — that provides tools for querying a SQLite database containing parsed Markdown documents. The server must implement tool registration with JSON Schema validation, handle pagination for large result sets, and include proper error handling with MCP-compliant error codes.

## Files to Create/Modify

- `src/markdown-sqlite/src/index.ts` (create) — MCP server entry point with tool registration and request handling
- `src/markdown-sqlite/src/tools.ts` (create) — Tool definitions with JSON Schema input validation
- `src/markdown-sqlite/src/database.ts` (create) — SQLite database operations for Markdown document storage and querying
- `src/markdown-sqlite/src/pagination.ts` (create) — Cursor-based pagination for query results
- `src/markdown-sqlite/package.json` (create) — Package definition with MCP SDK dependency
- `src/markdown-sqlite/tsconfig.json` (create) — TypeScript configuration
- `tests/test_mcp_builder.py` (create) — Tests for MCP server tool functionality

## Requirements

### Tool Registration

- Register the following tools using the MCP SDK's tool registration API:
  - `search_documents` — Full-text search across Markdown documents; input schema: `{"query": "string (required)", "limit": "number (optional, default 10, max 100)", "offset": "number (optional, default 0)"}`
  - `get_document` — Retrieve a single document by ID; input schema: `{"id": "string (required)"}`
  - `list_documents` — List all documents with optional filtering; input schema: `{"tag": "string (optional)", "created_after": "string (optional, ISO 8601)", "cursor": "string (optional)", "page_size": "number (optional, default 20, max 50)"}`
  - `get_document_sections` — Retrieve parsed sections (headers, paragraphs, code blocks) from a document; input schema: `{"id": "string (required)", "section_type": "string (optional, one of: 'header', 'paragraph', 'code')"}`
- Each tool must have a `description` and `inputSchema` (JSON Schema) defined in the tool registration
- Tool annotations must include `readOnlyHint: true` for all tools (read-only server)

### JSON Schema Validation

- All tool inputs must be validated against their JSON Schema before execution
- Missing required fields return MCP error with code `-32602` (Invalid params) and a message listing the missing fields
- Type mismatches (e.g., string where number expected) return the same error code with a descriptive message
- Values exceeding defined limits (e.g., `limit > 100`) are clamped to the maximum rather than rejected

### SQLite Database Layer

- Create a SQLite database with tables:
  - `documents` — columns: `id` (TEXT PRIMARY KEY), `title` (TEXT), `content` (TEXT), `tags` (TEXT, comma-separated), `created_at` (TEXT, ISO 8601), `updated_at` (TEXT, ISO 8601)
  - `sections` — columns: `id` (TEXT PRIMARY KEY), `document_id` (TEXT FOREIGN KEY), `section_type` (TEXT), `content` (TEXT), `heading_level` (INTEGER, nullable), `order_index` (INTEGER)
- Enable FTS5 full-text search on the `documents` table for the `title` and `content` columns
- All queries must use parameterized statements (no string interpolation of user input)

### Cursor-Based Pagination

- `list_documents` uses cursor-based pagination: the cursor is an opaque base64-encoded string containing the last seen `id` and sort position
- Response includes: `results` (array of documents), `next_cursor` (string or null if no more results), `has_more` (boolean)
- Invalid cursors return an empty result set (not an error) with `has_more: false`
- The cursor must be deterministic: the same cursor always produces the same subsequent page (assuming no data changes)

### Error Handling

- MCP protocol errors use standard JSON-RPC error codes: `-32600` (Invalid Request), `-32601` (Method not found), `-32602` (Invalid params), `-32603` (Internal error)
- If a document ID is not found, return a tool result with `isError: true` and a message "Document not found: {id}"
- Database connection failures return error code `-32603` with message "Internal database error"
- All errors include a human-readable `message` field

### Expected Functionality

- Calling `search_documents({"query": "kubernetes"})` returns matching documents ranked by FTS5 relevance
- Calling `get_document({"id": "doc-123"})` returns the full document or an error if not found
- Calling `list_documents({"tag": "tutorial", "page_size": 5})` returns the first 5 tutorial-tagged documents with a `next_cursor`
- Calling `list_documents({"cursor": "<next_cursor>"})` returns the next page
- Calling `search_documents({})` returns MCP error `-32602` mentioning `query` is required
- Calling `search_documents({"query": "test", "limit": 500})` clamps limit to 100

## Acceptance Criteria

- All four tools are registered with correct names, descriptions, and JSON Schema input definitions
- Tool annotations include `readOnlyHint: true`
- Input validation returns MCP error `-32602` for missing required fields and type mismatches
- Values exceeding limits are clamped (not rejected)
- SQLite queries use parameterized statements — no string concatenation of user input
- Full-text search uses FTS5 and returns results ranked by relevance
- Cursor-based pagination produces correct pages with `next_cursor` and `has_more`
- Invalid cursors return empty results gracefully
- Error responses use standard JSON-RPC error codes with descriptive messages
- `npm run build` in `src/markdown-sqlite` compiles successfully
- Tests cover all tools, validation errors, pagination, and error scenarios
