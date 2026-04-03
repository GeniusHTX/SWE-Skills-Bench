# Task: Add Visit Scheduling Feature to Spring PetClinic with Full Test Coverage

## Background

The Spring PetClinic application is a reference Spring Boot project that manages pet owners, their pets, and veterinary visits. Currently, visits can only be recorded after they happen. A new visit-scheduling capability must be added that allows owners to schedule future visits with date validation, status tracking, and conflict detection. All new code must be accompanied by tests at the unit, web-layer, and integration levels, and the overall coverage of the new code must reach at least 80%.

## Files to Create/Modify

- `src/main/java/org/springframework/samples/petclinic/visit/VisitSchedulingService.java` (create) — Service class encapsulating scheduling business logic
- `src/main/java/org/springframework/samples/petclinic/visit/VisitStatus.java` (create) — Enum with values `SCHEDULED`, `COMPLETED`, `CANCELLED`
- `src/main/java/org/springframework/samples/petclinic/visit/VisitScheduleRequest.java` (create) — DTO for incoming scheduling requests with Jakarta Bean Validation annotations
- `src/main/java/org/springframework/samples/petclinic/visit/VisitSchedulingController.java` (create) — REST controller exposing scheduling endpoints
- `src/main/java/org/springframework/samples/petclinic/visit/Visit.java` (modify) — Add `status` field (`VARCHAR(20)`, default `SCHEDULED`) and `scheduledDate` (`DATE`) to the existing entity
- `src/main/java/org/springframework/samples/petclinic/visit/VisitRepository.java` (modify) — Add query methods for finding visits by pet, date range, and status
- `src/main/resources/db/h2/schema.sql` (modify) — Add `status` and `scheduled_date` columns to the `visits` table
- `src/main/resources/db/h2/data.sql` (modify) — Populate `status` for existing seed visits
- `src/test/java/org/springframework/samples/petclinic/visit/VisitSchedulingServiceTest.java` (create) — Unit tests for scheduling logic using JUnit 5 and Mockito
- `src/test/java/org/springframework/samples/petclinic/visit/VisitSchedulingControllerTest.java` (create) — Web-layer tests using `@WebMvcTest` and MockMvc
- `src/test/java/org/springframework/samples/petclinic/visit/VisitSchedulingIntegrationTest.java` (create) — Full-stack integration tests using `@SpringBootTest` and `@AutoConfigureMockMvc`

## Requirements

### Visit Entity Changes

- Add a `status` field of type `String` mapped to column `status VARCHAR(20)` with default value `"SCHEDULED"`
- Add a `scheduledDate` field of type `LocalDate` mapped to column `scheduled_date DATE`
- The `status` field must only accept values defined in the `VisitStatus` enum: `SCHEDULED`, `COMPLETED`, `CANCELLED`

### VisitScheduleRequest DTO

- Fields: `petId` (`Integer`, required, positive), `vetId` (`Integer`, required, positive), `scheduledDate` (`LocalDate`, required), `description` (`String`, optional, max 255 characters)
- Jakarta validation annotations must be present: `@NotNull`, `@Positive`, `@Future`, `@Size`

### VisitSchedulingService

- `scheduleVisit(VisitScheduleRequest request) -> Visit` — creates a new visit with status `SCHEDULED`
- `cancelVisit(Integer visitId) -> Visit` — transitions status from `SCHEDULED` to `CANCELLED`; throws `IllegalStateException` if the visit is already `COMPLETED` or `CANCELLED`
- `completeVisit(Integer visitId) -> Visit` — transitions status from `SCHEDULED` to `COMPLETED`; throws `IllegalStateException` if the visit is not `SCHEDULED`
- Before scheduling, the service must check `VisitRepository` for existing `SCHEDULED` visits for the same pet on the same date; if one exists, throw `IllegalArgumentException` with the message `"A visit is already scheduled for this pet on the given date"`
- `scheduledDate` must be in the future (strictly after `LocalDate.now()`); if not, throw `IllegalArgumentException` with the message `"Scheduled date must be in the future"`
- The pet referenced by `petId` must exist in the database; if not, throw `EntityNotFoundException`

### VisitSchedulingController

- `POST /api/visits/schedule` — accepts `VisitScheduleRequest` as JSON, returns HTTP 201 with the created visit
- `PUT /api/visits/{visitId}/cancel` — returns HTTP 200 with the updated visit, or HTTP 409 for invalid state transitions
- `PUT /api/visits/{visitId}/complete` — returns HTTP 200 with the updated visit, or HTTP 409 for invalid state transitions
- `GET /api/visits/scheduled?petId={petId}` — returns all `SCHEDULED` visits for the given pet, ordered by `scheduledDate` ascending
- Validation errors return HTTP 400 with a JSON body containing field-level error messages

### VisitRepository Queries

- `findByPetIdAndScheduledDateAndStatus(Integer petId, LocalDate date, VisitStatus status) -> Optional<Visit>`
- `findByPetIdAndStatusOrderByScheduledDateAsc(Integer petId, VisitStatus status) -> List<Visit>`

### Expected Functionality

- `POST /api/visits/schedule` with `{"petId": 1, "vetId": 3, "scheduledDate": "2030-06-15"}` → HTTP 201, visit with status `SCHEDULED`
- `POST /api/visits/schedule` with a past date → HTTP 400, `"Scheduled date must be in the future"`
- `POST /api/visits/schedule` with the same petId and date as an existing scheduled visit → HTTP 409, `"A visit is already scheduled for this pet on the given date"`
- `PUT /api/visits/{id}/cancel` on a `SCHEDULED` visit → HTTP 200, status becomes `CANCELLED`
- `PUT /api/visits/{id}/cancel` on an already `COMPLETED` visit → HTTP 409
- `PUT /api/visits/{id}/complete` on a `CANCELLED` visit → HTTP 409
- `POST /api/visits/schedule` with `petId` referencing a non-existent pet → HTTP 404
- `POST /api/visits/schedule` with missing `petId` → HTTP 400 with validation error

## Acceptance Criteria

- `./mvnw compile -DskipTests` completes with exit code 0
- `./mvnw test` completes with all new and existing tests passing
- Unit tests in `VisitSchedulingServiceTest` verify scheduling, cancellation, completion, duplicate-date rejection, past-date rejection, and non-existent-pet handling using mocked dependencies
- Web-layer tests in `VisitSchedulingControllerTest` verify HTTP status codes, JSON response shapes, and validation error responses using `@WebMvcTest` and MockMvc
- Integration tests in `VisitSchedulingIntegrationTest` perform full HTTP round-trips against the running application context with the H2 database
- State transitions `SCHEDULED → CANCELLED` and `SCHEDULED → COMPLETED` work correctly; all other transitions are rejected with `IllegalStateException`
- No duplicate scheduled visits are allowed for the same pet on the same date
- Line coverage of the new scheduling classes is ≥ 80%
