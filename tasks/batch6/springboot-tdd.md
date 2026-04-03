# Task: Add Vet Appointment Booking Feature to Spring Petclinic with TDD

## Background

The Spring Petclinic application (https://github.com/spring-projects/spring-petclinic) is a reference Spring Boot application demonstrating MVC patterns. A new appointment booking feature is needed that allows pet owners to schedule visits with specific veterinarians. The feature needs a new `Appointment` entity, repository, service, and REST controller — all developed following a test-driven approach where tests are written before implementation.

## Files to Create/Modify

- `src/main/java/org/springframework/samples/petclinic/appointment/Appointment.java` (create) — JPA entity for appointments
- `src/main/java/org/springframework/samples/petclinic/appointment/AppointmentRepository.java` (create) — Spring Data JPA repository interface
- `src/main/java/org/springframework/samples/petclinic/appointment/AppointmentService.java` (create) — Service layer with booking logic, conflict detection, and cancellation
- `src/main/java/org/springframework/samples/petclinic/appointment/AppointmentController.java` (create) — REST controller for CRUD operations
- `src/main/java/org/springframework/samples/petclinic/appointment/CreateAppointmentRequest.java` (create) — Request DTO with validation annotations
- `src/main/resources/db/h2/schema.sql` (modify) — Add the `appointments` table DDL
- `src/main/resources/db/h2/data.sql` (modify) — Add sample appointment data
- `src/test/java/org/springframework/samples/petclinic/appointment/AppointmentServiceTest.java` (create) — Unit tests for service logic with Mockito
- `src/test/java/org/springframework/samples/petclinic/appointment/AppointmentControllerTest.java` (create) — MockMvc web layer tests
- `src/test/java/org/springframework/samples/petclinic/appointment/AppointmentRepositoryTest.java` (create) — DataJpaTest persistence tests

## Requirements

### Appointment Entity

- Fields:
  - `id` — Integer, auto-generated primary key
  - `pet` — ManyToOne relationship to `Pet` entity, not null
  - `vet` — ManyToOne relationship to `Vet` entity, not null
  - `appointmentDate` — LocalDate, not null, must be today or in the future
  - `startTime` — LocalTime, not null
  - `endTime` — LocalTime, not null, must be after `startTime`
  - `reason` — String, max length 500, not blank
  - `status` — Enum (`SCHEDULED`, `COMPLETED`, `CANCELLED`), default `SCHEDULED`
  - `createdAt` — LocalDateTime, auto-set on creation
- Table name: `appointments`.

### Repository

- `findByVetAndAppointmentDate(Vet vet, LocalDate date)` — returns all appointments for a vet on a given date.
- `findByPetOwnerId(Integer ownerId)` — returns all appointments for pets belonging to a specific owner.
- `findByVetIdAndStatusAndAppointmentDateBetween(Integer vetId, AppointmentStatus status, LocalDate start, LocalDate end)` — returns vet's appointments in a date range filtered by status.

### Service Logic

- `createAppointment(CreateAppointmentRequest request)`:
  - Validates that the vet and pet exist; throws `EntityNotFoundException` if not.
  - Validates that the appointment date is not in the past.
  - Checks for scheduling conflicts: a vet cannot have two appointments with overlapping time ranges on the same date. If a conflict exists, throw `ConflictException` with message `"Vet already has an appointment from {startTime} to {endTime} on {date}"`.
  - Validates business hours: appointments must start at or after 08:00 and end at or before 18:00. Violations throw `IllegalArgumentException` with message `"Appointments must be within business hours (08:00-18:00)"`.
  - Creates and returns the new `Appointment`.

- `cancelAppointment(Integer appointmentId)`:
  - Only `SCHEDULED` appointments can be cancelled. Attempting to cancel a `COMPLETED` or already `CANCELLED` appointment throws `IllegalStateException` with message `"Only scheduled appointments can be cancelled"`.
  - Sets status to `CANCELLED` and returns the updated appointment.

- `getAppointmentsForOwner(Integer ownerId)`:
  - Returns all appointments for the given owner's pets, sorted by date descending.

### REST Controller

- `POST /api/appointments` — create a new appointment. Request body:
  ```json
  {
    "petId": 1,
    "vetId": 2,
    "appointmentDate": "2026-04-15",
    "startTime": "10:00",
    "endTime": "10:30",
    "reason": "Annual checkup"
  }
  ```
  - Returns 201 Created with the appointment JSON.
  - Returns 400 for validation errors, 404 for non-existent vet/pet, 409 for scheduling conflicts.

- `GET /api/appointments?ownerId={id}` — list appointments for owner. Returns 200 with JSON array.

- `PATCH /api/appointments/{id}/cancel` — cancel an appointment. Returns 200 with updated appointment. Returns 404 if appointment not found, 400 if cannot be cancelled.

- `GET /api/appointments/{id}` — get a single appointment by ID. Returns 200 or 404.

### Expected Functionality

- Creating an appointment for Vet 1 on 2026-04-15 from 10:00 to 10:30 → returns 201 with `status: "SCHEDULED"`.
- Creating another appointment for Vet 1 on 2026-04-15 from 10:15 to 10:45 → returns 409 Conflict with descriptive message.
- Creating an appointment with `startTime: "07:00"` → returns 400 with message about business hours.
- Creating an appointment with past date → returns 400.
- Cancelling a scheduled appointment → returns 200 with `status: "CANCELLED"`.
- Cancelling an already cancelled appointment → returns 400.
- `GET /api/appointments?ownerId=1` → returns appointments sorted by date descending.

## Acceptance Criteria

- The `Appointment` JPA entity is correctly mapped with all required fields, relationships, and constraints.
- The repository provides custom query methods for vet schedule lookup, owner appointment listing, and date-range filtering.
- The service layer enforces scheduling conflict detection, business hours validation, and state transition rules.
- The REST controller handles all four endpoints with correct HTTP status codes and error responses.
- Unit tests for the service layer mock the repository and verify conflict detection, validation, and cancellation logic.
- MockMvc tests verify request/response serialization, validation error handling, and HTTP status codes.
- DataJpaTest tests verify custom repository query methods return correct results.
- The application compiles with `./mvnw compile -DskipTests`.
