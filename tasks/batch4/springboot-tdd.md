# Task: Add Veterinary Visit Scheduling Feature to Spring PetClinic with TDD

## Background

The Spring PetClinic application (https://github.com/spring-projects/spring-petclinic) is a reference Spring Boot application for managing a veterinary clinic. A new feature is needed to allow scheduling future visits for pets, including validation of appointment constraints, conflict detection, and proper persistence. The feature must be developed using a test-driven workflow where tests are written before implementation code.

## Files to Create/Modify

- `src/main/java/org/springframework/samples/petclinic/visit/VisitSchedulingService.java` (create) — Service layer for scheduling visits with conflict detection and validation
- `src/main/java/org/springframework/samples/petclinic/visit/VisitScheduleController.java` (create) — REST controller exposing scheduling endpoints
- `src/main/java/org/springframework/samples/petclinic/visit/ScheduleVisitRequest.java` (create) — Request DTO with validation annotations
- `src/main/java/org/springframework/samples/petclinic/visit/VisitRepository.java` (modify) — Add query methods for finding visits by date range and detecting scheduling conflicts
- `src/test/java/org/springframework/samples/petclinic/visit/VisitSchedulingServiceTest.java` (create) — Unit tests for the service layer using Mockito
- `src/test/java/org/springframework/samples/petclinic/visit/VisitScheduleControllerTest.java` (create) — MockMvc-based web layer tests
- `src/test/java/org/springframework/samples/petclinic/visit/VisitSchedulingIntegrationTest.java` (create) — Full Spring Boot integration tests

## Requirements

### REST API

- `POST /api/visits/schedule` accepts a JSON body with `petId` (integer), `vetId` (integer), `visitDate` (ISO-8601 date-time), and `description` (string, max 255 chars)
- A successful scheduling returns `201 Created` with the persisted visit in the response body
- `GET /api/visits/schedule?vetId={id}&from={date}&to={date}` returns all scheduled visits for a vet within the date range, ordered by `visitDate` ascending

### Validation Rules

- `petId` and `vetId` must reference existing records; a nonexistent ID returns `404`
- `visitDate` must be in the future (at least 1 hour from now); a past or too-near date returns `400` with a descriptive message
- `description` must not be blank and must not exceed 255 characters
- Scheduling a visit at a date-time that falls within 30 minutes of an existing visit for the same vet returns `409 Conflict`

### Conflict Detection

- Two visits conflict if they are for the same vet and their `visitDate` values are less than 30 minutes apart
- The conflict check must be performed atomically — concurrent scheduling requests for the same vet and overlapping time slot must not both succeed

### Test Coverage

- Unit tests for `VisitSchedulingService` must cover: successful scheduling, pet-not-found, vet-not-found, past-date rejection, conflict detection, and blank/oversized description rejection
- Controller tests must verify HTTP status codes, response body structure, and validation error messages for each failure mode
- Integration tests must exercise the full request path from HTTP to database and back, including the conflict scenario
- Combined test coverage of the new code must reach at least 80% line coverage

### Expected Functionality

- Scheduling a visit for an existing pet and vet with a future date succeeds and returns the visit with a generated `id`
- Scheduling a visit 10 minutes after an existing visit for the same vet returns `409`
- Scheduling a visit for the same vet 31 minutes after an existing visit succeeds
- Scheduling a visit with `vetId` that does not exist returns `404`
- Scheduling a visit with a `visitDate` 5 minutes from now returns `400`
- Scheduling a visit with a 300-character description returns `400`
- Querying visits for a vet within a date range returns only visits inside that range, sorted by date

## Acceptance Criteria

- The application compiles without errors (`./mvnw compile -DskipTests` succeeds)
- All unit, controller, and integration tests pass (`./mvnw test` exits with code 0)
- `POST /api/visits/schedule` returns correct status codes for valid input (201), missing entities (404), validation failures (400), and scheduling conflicts (409)
- `GET /api/visits/schedule` returns filtered and sorted results matching the query parameters
- Concurrent scheduling requests for the same vet and overlapping time slot do not both succeed
- Test coverage of the new service, controller, and DTO classes is at least 80%
