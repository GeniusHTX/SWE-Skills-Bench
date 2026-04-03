# Task: Add Appointment Resource to Spring PetClinic Using Test-Driven Development

## Background

Spring PetClinic (https://github.com/spring-projects/spring-petclinic) is a reference Spring Boot application demonstrating MVC, JPA, and Thymeleaf patterns. It currently manages owners, pets, vets, and visits. A new "Appointment" resource is needed to allow scheduling a pet's visit with a specific vet at a given date and time, with conflict detection and validation. The feature must be developed test-first: write failing tests, implement minimal code to pass, then refactor.

## Files to Create/Modify

- `src/main/java/org/springframework/samples/petclinic/appointment/Appointment.java` (create) — JPA entity linking a Pet to a Vet with date/time, description, and status
- `src/main/java/org/springframework/samples/petclinic/appointment/AppointmentRepository.java` (create) — Spring Data JPA repository with custom query methods for conflict detection and filtered lookups
- `src/main/java/org/springframework/samples/petclinic/appointment/AppointmentController.java` (create) — REST controller with endpoints for creating, listing, retrieving, updating, and cancelling appointments
- `src/main/java/org/springframework/samples/petclinic/appointment/AppointmentValidator.java` (create) — Validator implementing scheduling rules and input constraints
- `src/main/resources/db/h2/schema.sql` (modify) — Add `appointments` table DDL
- `src/main/resources/db/h2/data.sql` (modify) — Add sample appointment seed data
- `src/main/resources/db/mysql/schema.sql` (modify) — Add `appointments` table DDL for MySQL
- `src/main/resources/db/mysql/data.sql` (modify) — Add sample appointment seed data for MySQL
- `src/test/java/org/springframework/samples/petclinic/appointment/AppointmentControllerTests.java` (create) — MockMvc web-layer tests for all controller endpoints
- `src/test/java/org/springframework/samples/petclinic/appointment/AppointmentRepositoryTests.java` (create) — DataJpaTest persistence tests for repository queries
- `src/test/java/org/springframework/samples/petclinic/appointment/AppointmentValidatorTests.java` (create) — Unit tests for validation logic

## Requirements

### Appointment Entity

- `Appointment` JPA entity with fields: `id` (Integer, auto-generated), `pet` (ManyToOne to `Pet`), `vet` (ManyToOne to `Vet`), `appointmentDateTime` (LocalDateTime), `description` (String, max 500 characters), `status` (enum: `SCHEDULED`, `COMPLETED`, `CANCELLED`)
- The `appointments` table must have foreign keys to the `pets` and `vets` tables
- `appointmentDateTime` must not be null; `description` may be empty; default status is `SCHEDULED`
- The entity must use Bean Validation annotations: `@NotNull` on `pet`, `vet`, and `appointmentDateTime`; `@Size(max=500)` on `description`

### Repository and Query Methods

- `findByVetIdAndAppointmentDateTimeBetween(Integer vetId, LocalDateTime start, LocalDateTime end)` — returns appointments for a vet within a date range, used for conflict detection
- `findByPetId(Integer petId)` — returns all appointments for a given pet
- `findByStatus(AppointmentStatus status)` — returns appointments filtered by status
- `findByVetId(Integer vetId)` — returns all appointments for a given vet

### REST Endpoints

- `POST /api/appointments` — create a new appointment; request body contains `petId`, `vetId`, `appointmentDateTime`, and `description`; returns HTTP 201 with the created appointment or HTTP 409 if a scheduling conflict exists
- `GET /api/appointments?vetId={id}` — list appointments, optionally filtered by vet; returns HTTP 200 with a JSON array
- `GET /api/appointments?petId={id}` — list appointments, optionally filtered by pet; returns HTTP 200 with a JSON array
- `GET /api/appointments/{id}` — retrieve a single appointment; returns HTTP 200 or HTTP 404
- `PUT /api/appointments/{id}` — update appointment details (date/time, description); returns HTTP 200 or HTTP 404; must re-validate conflict rules
- `PATCH /api/appointments/{id}/cancel` — set appointment status to `CANCELLED`; returns HTTP 200 or HTTP 404; already-cancelled appointments return HTTP 400

### Scheduling Conflict Detection

- A vet cannot have two `SCHEDULED` appointments within 30 minutes of each other; attempting to create or update an appointment that overlaps with an existing `SCHEDULED` appointment for the same vet must return HTTP 409 with an error message identifying the conflicting time slot
- `CANCELLED` appointments do not count as conflicts
- The 30-minute window is calculated from `appointmentDateTime`: the new appointment's time must not fall within ±30 minutes of any existing `SCHEDULED` appointment for the same vet

### Input Validation

- `appointmentDateTime` must be in the future; past dates must be rejected with HTTP 400
- `petId` and `vetId` must reference existing records; non-existent IDs must result in HTTP 400 or HTTP 404
- `description` exceeding 500 characters must be rejected with HTTP 400

### Test Requirements

- Controller tests (`@WebMvcTest`) must cover: successful creation (201), conflict detection (409), retrieval (200), not-found (404), cancellation (200), double-cancellation (400), validation errors (400), and list filtering by vet/pet
- Repository tests (`@DataJpaTest`) must verify: save and retrieve roundtrip, `findByVetIdAndAppointmentDateTimeBetween` returns correct subset, `findByPetId` returns only that pet's appointments, `findByStatus` filtering
- Validator tests must verify: past-date rejection, null field rejection, description length enforcement, and valid input acceptance
- Tests must be written before the implementation code — tests are expected to fail initially until the corresponding production code is added

## Expected Functionality

- Creating an appointment with valid data for Pet "Leo" (id=1) and Vet "James Carter" (id=1) at a future date returns HTTP 201 with the appointment JSON including a generated `id` and status `SCHEDULED`
- Creating a second appointment for Vet id=1 at the same time returns HTTP 409
- Creating a second appointment for Vet id=1 at a time 45 minutes later succeeds with HTTP 201
- `GET /api/appointments?vetId=1` returns only appointments belonging to vet 1
- `PATCH /api/appointments/1/cancel` sets status to `CANCELLED` and the cancelled slot becomes available for new bookings
- `POST /api/appointments` with a past `appointmentDateTime` returns HTTP 400

## Acceptance Criteria

- The project compiles with `./mvnw compile -DskipTests` without errors
- All new test classes pass when run with `./mvnw test`
- `Appointment` entity is persisted correctly to both H2 and MySQL schemas with proper foreign-key relationships
- `POST /api/appointments` creates appointments and enforces the 30-minute conflict window per vet
- `PATCH /api/appointments/{id}/cancel` transitions status to `CANCELLED` and idempotent cancel attempts return HTTP 400
- All REST endpoints validate input and return appropriate HTTP status codes (201, 200, 400, 404, 409)
- Controller test class contains at least 8 test methods covering success, conflict, not-found, validation, and cancellation scenarios
- Repository test class contains at least 4 test methods covering CRUD and custom query methods
- Validator test class contains at least 4 test methods covering all validation rules
