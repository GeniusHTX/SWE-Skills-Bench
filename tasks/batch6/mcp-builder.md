# Task: Build an MCP Server for the GitHub Issues API

## Background

A TypeScript MCP (Model Context Protocol) server is needed that enables LLMs to interact with the GitHub Issues API. The server must expose tools for listing, creating, updating, commenting on, and searching issues within a repository. It uses streamable HTTP transport for remote access and follows the MCP SDK conventions for tool schemas, annotations, and structured output.

## Files to Create/Modify

- `package.json` (create) — Project configuration with dependencies: `@modelcontextprotocol/sdk`, `zod`, `typescript`
- `tsconfig.json` (create) — TypeScript compiler configuration targeting ES2022 with strict mode
- `src/index.ts` (create) — Server entry point: creates the MCP server, registers all tools, starts streamable HTTP transport
- `src/github-client.ts` (create) — Authenticated GitHub API client with rate-limit handling and pagination support
- `src/tools/list-issues.ts` (create) — Tool: `github_list_issues` — list issues with filters (state, labels, assignee, milestone, sort, direction, per_page, page)
- `src/tools/get-issue.ts` (create) — Tool: `github_get_issue` — get a single issue by number with full details
- `src/tools/create-issue.ts` (create) — Tool: `github_create_issue` — create a new issue with title, body, labels, assignees, milestone
- `src/tools/update-issue.ts` (create) — Tool: `github_update_issue` — update issue fields (title, body, state, labels, assignees)
- `src/tools/add-comment.ts` (create) — Tool: `github_add_comment` — add a comment to an issue
- `src/tools/list-comments.ts` (create) — Tool: `github_list_comments` — list comments on an issue with pagination
- `src/tools/search-issues.ts` (create) — Tool: `github_search_issues` — full-text search across issues using GitHub search syntax

## Requirements

### GitHub API Client (`src/github-client.ts`)

- Accept a personal access token via environment variable `GITHUB_TOKEN`.
- Base URL: `https://api.github.com`.
- Include `Accept: application/vnd.github.v3+json` and `Authorization: Bearer <token>` headers on every request.
- Implement `getRateLimit()` that returns remaining requests and reset time.
- When a response has status 403 with `x-ratelimit-remaining: 0`, throw an error with message: `"Rate limit exceeded. Resets at {reset_time}"`.
- Implement pagination helper that follows `Link` header `rel="next"` to collect all pages up to a configurable max.

### Tool Definitions

Each tool must have:
- Zod input schema with constraints and field descriptions.
- `outputSchema` defined for structured responses.
- Annotations: `readOnlyHint`, `destructiveHint`, `idempotentHint` set appropriately.

#### `github_list_issues`

- Parameters: `owner` (string, required), `repo` (string, required), `state` (enum: `"open"`, `"closed"`, `"all"`, default `"open"`), `labels` (optional, comma-separated string), `assignee` (optional, string), `sort` (enum: `"created"`, `"updated"`, `"comments"`, default `"created"`), `direction` (enum: `"asc"`, `"desc"`, default `"desc"`), `per_page` (number 1-100, default 30), `page` (number, default 1).
- Returns: `{ issues: Array<{ number, title, state, user, labels, assignees, created_at, updated_at, comments_count }>, total_count: number }`.
- Annotations: `readOnlyHint: true`, `destructiveHint: false`.

#### `github_create_issue`

- Parameters: `owner`, `repo`, `title` (required, non-empty string), `body` (optional), `labels` (optional, array of strings), `assignees` (optional, array of strings), `milestone` (optional, number).
- Returns: `{ number, title, html_url, state }`.
- Annotations: `readOnlyHint: false`, `destructiveHint: false`, `idempotentHint: false`.

#### `github_update_issue`

- Parameters: `owner`, `repo`, `issue_number` (required, positive integer), `title` (optional), `body` (optional), `state` (optional, enum: `"open"`, `"closed"`), `labels` (optional, array of strings), `assignees` (optional, array of strings).
- Returns: `{ number, title, state, html_url, updated_at }`.
- Annotations: `readOnlyHint: false`, `destructiveHint: false`, `idempotentHint: true`.

#### `github_search_issues`

- Parameters: `query` (required, GitHub search syntax string), `sort` (optional, enum: `"created"`, `"updated"`, `"comments"`, `"reactions"`), `order` (optional, enum: `"asc"`, `"desc"`), `per_page` (1-100, default 30).
- Returns: `{ total_count: number, items: Array<{ number, title, state, repository, score, html_url }> }`.
- Annotations: `readOnlyHint: true`.

#### `github_add_comment`

- Parameters: `owner`, `repo`, `issue_number` (positive integer), `body` (required, non-empty string).
- Returns: `{ id, html_url, created_at }`.
- Annotations: `readOnlyHint: false`, `destructiveHint: false`, `idempotentHint: false`.

#### `github_list_comments`

- Parameters: `owner`, `repo`, `issue_number` (positive integer), `per_page` (1-100, default 30), `page` (default 1).
- Returns: `{ comments: Array<{ id, user, body, created_at, updated_at }> }`.
- Annotations: `readOnlyHint: true`.

#### `github_get_issue`

- Parameters: `owner`, `repo`, `issue_number` (positive integer).
- Returns: `{ number, title, body, state, user, labels, assignees, milestone, created_at, updated_at, closed_at, comments_count, html_url }`.
- Annotations: `readOnlyHint: true`.

### Error Handling

- API 404 responses → tool result with `isError: true` and message `"Issue #N not found in owner/repo"`.
- API 422 (validation error) → tool result with `isError: true` and the GitHub validation message forwarded.
- Network errors → tool result with `isError: true` and message `"Failed to connect to GitHub API: {error_message}"`.
- Missing `GITHUB_TOKEN` → server fails to start with message `"GITHUB_TOKEN environment variable is required"`.

### Server Setup (`src/index.ts`)

- Create MCP server with name `"github-issues-mcp"` and version `"1.0.0"`.
- Register all 7 tools.
- Start streamable HTTP transport on port from `PORT` env var (default 3000).
- Log registered tool count on startup.

### Expected Functionality

- `github_list_issues({ owner: "facebook", repo: "react", state: "open", labels: "bug", per_page: 5 })` → returns 5 open bug issues from facebook/react.
- `github_create_issue({ owner: "myorg", repo: "myrepo", title: "Fix login bug", body: "Steps to reproduce...", labels: ["bug", "priority-high"] })` → creates issue, returns number and URL.
- `github_search_issues({ query: "repo:facebook/react is:open label:bug sort:reactions" })` → returns matching issues with scores.
- `github_update_issue({ owner: "myorg", repo: "myrepo", issue_number: 42, state: "closed" })` → closes issue #42.
- `github_get_issue({ owner: "myorg", repo: "myrepo", issue_number: 999999 })` → returns error: `"Issue #999999 not found in myorg/myrepo"`.

## Acceptance Criteria

- The MCP server starts successfully and registers all 7 tools with correct input schemas, output schemas, and annotations.
- `npm run build` compiles without errors.
- Each tool validates input with Zod and returns structured output matching the declared `outputSchema`.
- Read-only tools (`list_issues`, `get_issue`, `list_comments`, `search_issues`) are annotated with `readOnlyHint: true`.
- Mutating tools (`create_issue`, `update_issue`, `add_comment`) are annotated with `readOnlyHint: false`.
- Rate limiting is detected and surfaced as an actionable error message with reset time.
- Missing or invalid authentication is caught at startup, not at first tool call.
