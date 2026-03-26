# Task: Optimize Catalog Service Concurrency and Data Access in eShop

## Background

The eShop application (https://github.com/dotnet/eshop) is a reference .NET microservices solution. The Catalog API service handles product browsing and needs performance improvements for concurrent request handling and optimized data retrieval patterns to reduce response latency under load.

## Files to Create/Modify

- `src/Catalog.API/Services/CatalogService.cs` (create or modify) — Service layer with async data access patterns and caching
- `src/Catalog.API/Apis/CatalogApi.cs` (modify) — Refactored API endpoints with projection DTOs
- `src/Catalog.API/Infrastructure/CatalogContext.cs` (modify) — Optimized EF Core queries (eager loading, projections)

## Requirements

### Concurrency Improvements

- Identify and refactor synchronous data access patterns to use async/await throughout the request pipeline
- Ensure database context and HTTP client usages are properly scoped for concurrent access
- Use appropriate concurrency primitives where shared state access is involved

### Data Access Optimization

- Optimize database queries to reduce round trips (e.g., eager loading related data, projection queries selecting only needed fields)
- Implement or improve caching for frequently accessed read-only data such as catalog categories and brand lists
- Ensure pagination queries are efficient and do not load entire result sets

### API Performance

- Response DTOs should carry only the fields needed by the caller, not entire entity graphs
- Long-running operations should not block the main request thread

## Expected Functionality

- The Catalog API builds and starts without errors
- Product listing and detail endpoints return correct data with reduced query counts
- Concurrent requests are handled without thread-safety issues or context disposal errors

## Acceptance Criteria

- Catalog endpoints use asynchronous data-access flow end to end rather than blocking synchronous calls in the request path.
- Product list and detail responses return the correct data while limiting fields to the required DTO shape.
- Frequently reused read-only data such as category and brand information is cached or otherwise optimized for repeated access.
- Pagination and related queries avoid loading unnecessary rows or entity graphs into memory.
- Concurrent requests complete without context-lifetime issues, shared-state corruption, or thread-safety regressions.
