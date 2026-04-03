# Task: Add Appointment Scheduling Feature to Spring PetClinic with Full Test Coverage

## Background

The Spring PetClinic application (https://github.com/spring-projects/spring-petclinic) is a reference Spring Boot project demonstrating MVC, JPA, and testing patterns. Currently, visits are simple one-off records without scheduling constraints. The task is to add an appointment scheduling feature that allows owners to book future visits with specific veterinarians, enforces no double-booking for the same vet in the same time slot, and validates scheduling rules — all built with tests written before production code.

## Files to Create/Modify

- `src/main/java/org/springframework/samples/petclinic/owner/Appointment.java` (create) — JPA entity for appointments with fields: `id`, `pet` (ManyToOne), `vet` (ManyToOne), `appointmentDate` (LocalDate), `timeSlot` (enum: MORNING, AFTERNOON), `reason` (String), `status` (enum: SCHEDULED, COMPLETED, CANCELLED)
- `src/main/java/org/springframework/samples/petclinic/owner/AppointmentRepository.java` (create) — Spring Data JPA repository with query methods for finding appointments by vet+date, by pet, and for checking scheduling conflicts
- `src/main/java/org/springframework/samples/petclinic/owner/AppointmentController.java` (create) — MVC controller handling GET `/owners/{ownerId}/pets/{petId}/appointments/new`, POST to create, and GET `/owners/{ownerId}/appointments` to list
- `src/test/java/org/springframework/samples/petclinic/owner/AppointmentControllerTests.java` (create) — `@WebMvcTest` tests for all controller endpoints using MockMvc and `@MockitoBean` for the repository
- `src/test/java/org/springframework/samples/petclinic/owner/AppointmentTests.java` (create) — Unit tests for entity validation (Bean Validation constraints) and status transitions
- `src/test/java/org/springframework/samples/petclinic/owner/AppointmentRepositoryTests.java` (create) — `@DataJpaTest` tests verifying custom query methods and conflict detection
- `src/main/resources/db/h2/data.sql` (modify) — Add sample appointment seed data for the H2 test database
- `src/main/resources/db/h2/schema.sql` (modify) — Add the `appointments` table DDL with foreign keys to `pets` and `vets`

## Requirements

### Appointment Entity

- `appointmentDate` must be a future date; dates in the past or today must fail Bean Validation
- `reason` must be between 1 and 255 characters
- `timeSlot` must be one of `MORNING` (9:00–12:00) or `AFTERNOON` (13:00–17:00)
- `status` defaults to `SCHEDULED` on creation; only `SCHEDULED` appointments can be transitioned to `CANCELLED` or `COMPLETED`; `CANCELLED` and `COMPLETED` are terminal states

### Scheduling Conflict Detection

- A vet must not have two `SCHEDULED` appointments on the same date in the same time slot
- `AppointmentRepository` must expose a method `findConflict(Vet vet, LocalDate date, TimeSlot slot)` that returns any existing `SCHEDULED` appointment for that combination
- The controller must check for conflicts before persisting and return an appropriate validation error if a conflict exists

### Controller Endpoints

- `GET /owners/{ownerId}/pets/{petId}/appointments/new` — Returns appointment creation form pre-populated with the pet and a dropdown of all vets
- `POST /owners/{ownerId}/pets/{petId}/appointments/new` — Validates input, checks for scheduling conflicts, persists the appointment, and redirects to the owner detail page
- `GET /owners/{ownerId}/appointments` — Lists all appointments for the given owner's pets, sorted by date descending

### Validation Rules

- Submitting a past date returns a form with a validation error message "Appointment date must be in the future"
- Submitting a conflicting vet+date+slot returns a form with error message "This veterinarian is not available at the selected time"
- Submitting an empty reason returns a validation error "Reason must not be blank"

### Expected Functionality

- Creating an appointment for Dr. James Carter on 2026-04-15 MORNING succeeds when no conflict exists
- Creating a second MORNING appointment for Dr. Carter on 2026-04-15 fails with a conflict error
- Creating an AFTERNOON appointment for Dr. Carter on the same date succeeds
- Cancelling a SCHEDULED appointment transitions status to CANCELLED
- Attempting to cancel an already-COMPLETED appointment returns an error

## Acceptance Criteria

- The project compiles without errors via `./mvnw compile -DskipTests`
- All new and existing tests pass via `./mvnw test`
- `AppointmentControllerTests` contains at least 8 test methods covering: successful creation, past-date rejection, blank-reason rejection, conflict detection, appointment listing, form rendering with vet dropdown, cancellation of SCHEDULED appointment, and rejection of cancellation for COMPLETED appointment
- `AppointmentRepositoryTests` verifies that `findConflict` returns a result when a conflict exists and returns empty when no conflict exists
- `AppointmentTests` validates Bean Validation constraints on `appointmentDate`, `reason`, and `timeSlot`
- No existing PetClinic tests are broken by the new feature
