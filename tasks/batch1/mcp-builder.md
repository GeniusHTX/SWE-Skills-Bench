# Task: Build MCP Server for Markdown Knowledge Base with SQLite

## Background

We need to create a hybrid MCP (Model Context Protocol) server using TypeScript and `@modelcontextprotocol/sdk` that connects a local Markdown knowledge base with a SQLite metadata database.

## Files to Create/Modify

- `src/markdown-sqlite/index.ts` - Main server implementation
- `src/markdown-sqlite/package.json` - Package configuration
- `src/markdown-sqlite/tests/index.test.ts` - Unit tests

## Requirements

### Tools to Implement

**1. index_markdown(dir_path: string)**
- Scan all `.md` files in specified directory
- Extract: file path, first-level heading, tags (from YAML front-matter)
- Write to SQLite table `documents`

**2. search_documents(query: string)**
- Use SQLite FTS5 full-text search
- Return matching document summaries: id, title, snippet

**3. read_document(doc_id: number)**
- Return complete Markdown content of specified document

### Package Configuration

- TypeScript compilation with `@modelcontextprotocol/sdk`
- `"build"` script for compilation
- `"test"` script for running tests

### SQLite Schema

```sql
CREATE VIRTUAL TABLE documents USING fts5(
  path, title, tags, content
);
```

### Expected Functionality

- `index_markdown` successfully indexes all markdown files in directory
- `search_documents` returns relevant results matching the query
- `read_document` returns complete and correct markdown content
- Graceful error handling for non-existent file paths

## Acceptance Criteria

- `cd src/markdown-sqlite && npm run build` compiles without errors
- All three MCP tools work as specified
- Error cases are handled appropriately
