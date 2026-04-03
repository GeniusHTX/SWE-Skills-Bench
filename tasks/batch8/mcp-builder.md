# Task: Build an MCP Server for Markdown-to-SQLite Conversion and Querying

## Background

The MCP servers repository (`modelcontextprotocol/servers`) hosts reference implementations of Model Context Protocol servers. A new TypeScript MCP server is needed in the `src/markdown-sqlite` directory that provides tools for LLMs to ingest Markdown documents into a SQLite database and query their structured content. The server should parse Markdown into structured sections, store them in SQLite, and expose query tools via the MCP protocol over stdio transport.

## Files to Create/Modify

- `src/markdown-sqlite/src/index.ts` (new) — MCP server entry point, tool registration, and stdio transport setup
- `src/markdown-sqlite/src/parser.ts` (new) — Markdown parser that converts documents into structured section records (heading hierarchy, content blocks, metadata)
- `src/markdown-sqlite/src/database.ts` (new) — SQLite database layer for storing and querying parsed document sections
- `src/markdown-sqlite/src/tools.ts` (new) — MCP tool implementations: `ingest_document`, `query_sections`, `search_content`, `list_documents`
- `src/markdown-sqlite/package.json` (new) — Package configuration with dependencies (MCP SDK, better-sqlite3, marked/remark) and `build` script
- `src/markdown-sqlite/tsconfig.json` (new) — TypeScript configuration targeting ES2022 with strict mode

## Requirements

### Markdown Parser

- Parse Markdown content into a flat list of section records
- Each section record contains: `heading` (the heading text), `level` (1–6), `path` (slash-delimited heading hierarchy, e.g., "Introduction/Getting Started/Prerequisites"), `content` (text content under the heading, excluding sub-headings), `word_count` (number of words in content)
- Content before the first heading is assigned to a virtual root section with heading `"_root"`, level 0, and path `"_root"`
- Code blocks within a section are preserved verbatim in the content field with their language tag (e.g., `\`\`\`python\n...\`\`\``)
- Empty sections (headings with no content before the next heading) must still produce a record with empty content and `word_count: 0`

### SQLite Database

- Create a `documents` table: `id` (auto-increment), `name` (unique text), `ingested_at` (ISO 8601), `total_sections` (integer), `total_words` (integer)
- Create a `sections` table: `id` (auto-increment), `document_id` (foreign key), `heading` (text), `level` (integer), `path` (text), `content` (text), `word_count` (integer)
- Create an index on `sections.path` and a full-text search virtual table `sections_fts` using FTS5 on `heading` and `content` columns
- Re-ingesting a document with the same name replaces the previous version (delete old sections, update document record)

### MCP Tools

- `ingest_document` — accepts `name` (string) and `content` (string, raw Markdown); parses and stores the document; returns `{ document_id, total_sections, total_words }`
- `query_sections` — accepts `document_name` (string), optional `min_level` (integer, default 1), optional `max_level` (integer, default 6), optional `path_prefix` (string); returns matching section records
- `search_content` — accepts `query` (string) for FTS5 search, optional `document_name` (string) to scope search; returns matching sections with FTS5 rank scores
- `list_documents` — no parameters; returns all ingested documents with their name, ingested_at, total_sections, and total_words
- All tools must include Zod input schemas with field descriptions
- All tools must return structured JSON content

### Server Configuration

- The server uses stdio transport for communication
- Server name: `"markdown-sqlite"`, version read from package.json
- The `package.json` must include a `"build"` script that compiles TypeScript (e.g., `tsc`)
- The compiled output must be in a `dist/` directory

### Expected Functionality

- Ingesting a Markdown document with 3 headings and 500 words returns `{ document_id: 1, total_sections: 3, total_words: 500 }`
- Ingesting the same document name again replaces the old version; `list_documents` still shows only one entry with updated `ingested_at`
- `query_sections` with `document_name: "readme"` and `max_level: 2` returns only level-1 and level-2 sections
- `query_sections` with `path_prefix: "API/Authentication"` returns only sections under that heading hierarchy
- `search_content` with `query: "configuration"` returns sections containing that word, ranked by relevance
- `search_content` with a non-matching query returns an empty array
- `list_documents` on an empty database returns an empty array
- Ingesting a document with no headings produces a single `_root` section
- `ingest_document` with empty `content` produces a document with one `_root` section and `total_words: 0`

## Acceptance Criteria

- `cd src/markdown-sqlite && npm run build` compiles successfully with exit code 0
- The Markdown parser correctly extracts heading hierarchy, content blocks, code blocks, and word counts
- The SQLite schema includes `documents`, `sections`, and `sections_fts` tables with proper foreign keys and indexes
- Re-ingesting a document by name replaces the previous version without duplicating records
- All four MCP tools (`ingest_document`, `query_sections`, `search_content`, `list_documents`) are registered and return correctly structured JSON
- FTS5 search returns relevant sections ranked by match score
- Input validation via Zod schemas rejects missing required fields with descriptive error messages
- Unit tests verify parsing, database operations, tool behavior, and edge cases (empty documents, no headings, re-ingestion)
