# Task: Implement Secure Export API Endpoints for BabyBuddy

## Background

We need to add export endpoints to BabyBuddy's REST API that allow users to export feeding and sleep records. The implementation must enforce proper authentication and authorization to ensure users can only access their own children's data.

## Files to Modify

- `api/serializers.py` - Add FeedingExportSerializer and SleepExportSerializer
- `api/views.py` - Add ExportViewSet
- `api/urls.py` - Register export routes
- `tests/test_api.py` - Add security test cases

## Requirements

### API Endpoint

- `GET /api/child/{child_id}/export/?type=feeding|sleep`
- Returns last 30 days of records in JSON format

### Security Requirements

- Use Django Permission to validate authenticated users
- Users can ONLY access their own children's data
- Proper HTTP status codes for different scenarios:
  - Authenticated user accessing own child's data → 200 OK
  - Unauthenticated request → 401 Unauthorized
  - User accessing another user's child data → 403 Forbidden

### Serializers

- **FeedingExportSerializer**: id, start, end, duration, type, method, amount
- **SleepExportSerializer**: id, start, end, duration, quality

## Acceptance Criteria

- `python manage.py test babybuddy.tests.test_api -v 2` passes with all tests successful
- Export endpoint returns correct JSON structure
- Security checks properly implemented and tested
