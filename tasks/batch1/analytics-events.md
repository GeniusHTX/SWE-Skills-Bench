# Task: Add Frontend Analytics Event Definitions for Metabase

## Background

We need to define and implement key user behavior analytics events for Metabase's frontend, enabling better understanding of user interactions.

## Files to Create/Modify

- `frontend/src/metabase/lib/analytics.ts` - Event definitions and types
- `frontend/test/metabase/lib/analytics.test.ts` - Unit tests

## Requirements

### Event Definitions (2-3 key events)

**1. dashboard_viewed**
- Payload: `dashboard_id`, `view_duration_ms`, `card_count`

**2. question_saved**
- Payload: `question_id`, `question_type`, `database_id`, `save_duration_ms`

**3. filter_applied**
- Payload: `dashboard_id`, `filter_type`, `filter_value_count`

### Event Interface

```typescript
interface AnalyticsEvent {
  event_name: string;
  payload: Record<string, unknown>;
  timestamp: number;
}
```

### Naming Convention

- Use `snake_case` for event names and payload field names
- Include TypeScript type definitions for each event payload

### Expected Functionality

- Event triggers produce correct payload structure
- All required fields are present in each payload
- Field names follow `snake_case` convention consistently
- Timestamps are valid Unix timestamps
- Payloads conform to their TypeScript type definitions

## Acceptance Criteria

- Event definitions have proper TypeScript types
- Payload fields are complete and correctly named
- Implementation follows naming conventions
- Code compiles without type errors
