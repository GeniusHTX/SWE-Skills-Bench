# Task: Build an MCP Server for SQLite-Backed Markdown Note Management

## Background

The Model Context Protocol (MCP) servers repository (https://github.com/modelcontextprotocol/servers) hosts reference implementations of MCP servers that enable LLMs to interact with external services. The task is to create a new MCP server called `markdown-sqlite` under `src/markdown-sqlite/` that provides tools for storing, retrieving, searching, and organizing Markdown notes in a local SQLite database. The server must be a fully functional TypeScript MCP server that builds and exposes tools following the MCP specification.

## Files to Create/Modify

- `src/markdown-sqlite/package.json` (create) — Node.js package manifest with build script, MCP SDK dependency, and better-sqlite3 dependency
- `src/markdown-sqlite/tsconfig.json` (create) — TypeScript configuration targeting ES2022 with strict mode
- `src/markdown-sqlite/src/index.ts` (create) — MCP server entry point: tool definitions, request handlers, SQLite database initialization
- `src/markdown-sqlite/src/database.ts` (create) — SQLite database layer: schema creation, CRUD operations, full-text search queries
- `src/markdown-sqlite/src/types.ts` (create) — TypeScript type definitions for notes, tags, and search results
- `src/markdown-sqlite/README.md` (create) — Usage documentation describing available tools and their parameters

## Requirements

### MCP Server Setup

- The server must use the `@modelcontextprotocol/sdk` package for MCP protocol handling
- The server must communicate over stdio transport
- The server must declare its capabilities in the `initialize` response: `tools` capability must be present
- The `package.json` `build` script must compile TypeScript to JavaScript so that `npm run build` succeeds

### Database Schema

- The SQLite database must be created automatically on first run at a configurable path (default: `./notes.db`)
- The schema must include a `notes` table with columns: `id` (TEXT PRIMARY KEY, UUID), `title` (TEXT NOT NULL), `content` (TEXT NOT NULL, Markdown body), `tags` (TEXT, comma-separated), `created_at` (TEXT, ISO 8601), `updated_at` (TEXT, ISO 8601)
- A full-text search (FTS5) virtual table must index the `title` and `content` columns for search

### Tool Definitions

The server must expose the following five tools:

#### `create_note`
- Parameters: `title` (string, required), `content` (string, required), `tags` (string[], optional)
- Behavior: Insert a new note with a generated UUID, current timestamp, and the provided title/content/tags
- Return: The created note object with all fields including `id` and timestamps

#### `get_note`
- Parameters: `id` (string, required)
- Behavior: Retrieve a single note by its UUID
- Return: The note object, or an error if not found

#### `search_notes`
- Parameters: `query` (string, required), `limit` (number, optional, default 10)
- Behavior: Perform full-text search across titles and content using SQLite FTS5
- Return: Array of matching notes sorted by relevance, each including a `snippet` field showing the match context

#### `update_note`
- Parameters: `id` (string, required), `title` (string, optional), `content` (string, optional), `tags` (string[], optional)
- Behavior: Update the specified fields of an existing note; `updated_at` is set to current time
- Return: The updated note object, or an error if the ID does not exist

#### `delete_note`
- Parameters: `id` (string, required)
- Behavior: Delete a note by UUID
- Return: Confirmation message, or an error if the ID does not exist

### Input Validation

- `create_note` must reject empty `title` or empty `content` with a descriptive error
- `search_notes` must reject empty `query` strings
- `search_notes` `limit` must be a positive integer no greater than 100
- `update_note` must require at least one field (`title`, `content`, or `tags`) to be provided
- All tool parameters must be validated against their declared JSON Schema before execution

### Error Handling

- Tools must return MCP error responses (not crash the server) when given invalid input
- Database errors (e.g., disk full, corrupt DB) must be caught and returned as tool errors
- Requesting a non-existent note ID must return a clear "note not found" error, not a generic failure

## Expected Functionality

- Calling `create_note` with `{"title": "Meeting Notes", "content": "# Q4 Planning\n- Budget review\n- Headcount", "tags": ["work","planning"]}` → returns a note object with a UUID `id`, both timestamps, and the provided fields
- Calling `search_notes` with `{"query": "budget"}` → returns an array containing the previously created note with a snippet highlighting "Budget"
- Calling `update_note` with `{"id": "<uuid>", "content": "# Q4 Planning\n- Budget review\n- Headcount\n- OKRs"}` → returns the note with updated content and a new `updated_at` timestamp
- Calling `get_note` with a non-existent UUID → returns an error indicating "note not found"
- Calling `delete_note` with a valid UUID → returns success; subsequent `get_note` with that UUID returns "not found"
- `npm run build` in the `src/markdown-sqlite/` directory completes without errors

## Acceptance Criteria

- The server builds successfully with `npm run build` from the `src/markdown-sqlite/` directory
- All five tools (`create_note`, `get_note`, `search_notes`, `update_note`, `delete_note`) are declared in the server's tool list and execute correctly
- Full-text search returns relevant results ranked by relevance with contextual snippets
- Input validation rejects empty titles, empty content, empty search queries, and invalid limit values with descriptive errors
- The SQLite database and FTS5 index are created automatically on first tool invocation
- Non-existent note IDs produce clear error messages without server crashes
