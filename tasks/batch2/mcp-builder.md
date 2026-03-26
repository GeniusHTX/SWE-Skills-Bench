# Task: Build an MCP Server for Markdown Knowledge Base Search

## Background

The MCP Servers repository (https://github.com/modelcontextprotocol/servers) hosts reference implementations of Model Context Protocol servers. A new server is needed under `src/markdown-sqlite/` that indexes Markdown documents into a SQLite database and exposes search, retrieval, and indexing capabilities as MCP tools for LLM clients.

## Files to Create

- Files under `src/markdown-sqlite/` — TypeScript source files for the MCP server including entry point, tool definitions, and SQLite integration
- `src/markdown-sqlite/package.json` — Project manifest with build and dependency configuration

## Requirements

### MCP Tools

- Register at least three tools:
  1. Index Markdown files from a given directory into the SQLite database
  2. Full-text search across indexed documents, returning matching results
  3. Retrieve the full content of a specific document by identifier

### SQLite Storage

- Store indexed documents in a local SQLite database
- Enable full-text search on stored content
- Track document metadata (file path, title from first heading, indexing timestamp)

### Build

- The project must build successfully with `npm run build` from `src/markdown-sqlite/`
- TypeScript compilation must produce valid JavaScript output

## Expected Functionality

- After indexing a directory of `.md` files, all documents are searchable
- Search queries return ranked results with document identifiers and excerpts
- The retrieval tool returns complete document content
- Re-indexing updates existing entries rather than duplicating them

## Acceptance Criteria

- The server exposes distinct MCP tools for indexing markdown files, searching indexed content, and retrieving a document by identifier.
- Indexed documents are stored in SQLite with enough metadata to identify source path, title, and indexing time.
- Search results return ranked matches with useful excerpts rather than only raw identifiers.
- Re-indexing the same source content updates existing records instead of producing duplicates.
- Retrieval returns the full stored document content for the requested identifier.
