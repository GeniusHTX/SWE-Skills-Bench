# Task: Add Veterinary Specialty Management REST API to Spring PetClinic

## Background

The Spring PetClinic application (https://github.com/spring-projects/spring-petclinic) is a reference Spring Boot project that manages pets, owners, visits, and veterinarians. Currently, vet specialties are stored as a simple `Specialty` entity referenced by `Vet`, but there is no dedicated REST API for managing specialties independently. The task is to add a full CRUD REST endpoint for veterinary specialties with proper validation, error handling, and test coverage.

## Files to Create/Modify

- `src/main/java/org/springframework/samples/petclinic/specialty/SpecialtyController.java` (create) — REST controller exposing CRUD endpoints for Specialty resources
- `src/main/java/org/springframework/samples/petclinic/specialty/SpecialtyService.java` (create) — Service layer with business logic for specialty management
- `src/main/java/org/springframework/samples/petclinic/specialty/SpecialtyRepository.java` (create) — Spring Data JPA repository interface for Specialty
- `src/main/java/org/springframework/samples/petclinic/specialty/SpecialtyDto.java` (create) — Data transfer object for Specialty API input/output
- `src/test/java/org/springframework/samples/petclinic/specialty/SpecialtyControllerTests.java` (create) — MockMvc-based tests for all REST endpoints
- `src/test/java/org/springframework/samples/petclinic/specialty/SpecialtyServiceTests.java` (create) — Unit tests for service layer logic with mocked repository
- `src/main/resources/db/h2/data.sql` (modify) — Add seed data for specialties if not already present

## Requirements

### REST API Endpoints

- `GET /api/specialties` — Return all specialties as a JSON array, sorted alphabetically by name
- `GET /api/specialties/{id}` — Return a single specialty by ID; return HTTP 404 if not found
- `POST /api/specialties` — Create a new specialty; return HTTP 201 with the created resource and a `Location` header
- `PUT /api/specialties/{id}` — Update an existing specialty; return HTTP 404 if the ID does not exist
- `DELETE /api/specialties/{id}` — Delete a specialty; return HTTP 204 on success, HTTP 404 if not found

### Validation Rules

- The `name` field is required, must be between 2 and 80 characters, and must be unique (case-insensitive)
- Creating or updating a specialty with a duplicate name must return HTTP 409 Conflict with an error message identifying the conflict
- Creating a specialty with a missing or blank name must return HTTP 400 with a validation error
- Request bodies with unknown JSON fields must be rejected with HTTP 400

### Data Model

- The `Specialty` entity must have at minimum: `id` (auto-generated), `name` (unique, not blank)
- The entity must integrate with the existing JPA/Hibernate configuration and the H2/MySQL/PostgreSQL database profiles
- The repository must extend a Spring Data interface that supports pagination

### Service Layer

- The service must encapsulate all business rules (uniqueness check, not-found handling)
- The service must throw meaningful exceptions that the controller translates to appropriate HTTP status codes
- The service must not expose JPA entities directly to the controller — use a DTO for input and output

### Test Requirements

- Controller tests must use MockMvc to test all five endpoints, including success and error paths
- Controller tests must verify response status codes, response body JSON structure, and response headers (`Location`, `Content-Type`)
- Service tests must mock the repository and verify business logic (uniqueness validation, not-found errors)
- At least one test must verify the duplicate-name conflict scenario
- At least one test must verify the validation error scenario for blank/missing name

## Expected Functionality

- `GET /api/specialties` → `[{"id":1,"name":"dentistry"},{"id":2,"name":"radiology"},{"id":3,"name":"surgery"}]` with HTTP 200
- `POST /api/specialties` with `{"name":"oncology"}` → HTTP 201 with body `{"id":4,"name":"oncology"}` and `Location: /api/specialties/4`
- `POST /api/specialties` with `{"name":"surgery"}` (existing) → HTTP 409 with conflict error
- `POST /api/specialties` with `{"name":""}` → HTTP 400 with validation error
- `GET /api/specialties/999` → HTTP 404
- `DELETE /api/specialties/1` → HTTP 204
- `DELETE /api/specialties/999` → HTTP 404

## Acceptance Criteria

- All five REST endpoints are functional and return correct status codes for both success and error cases
- The specialty name uniqueness constraint is enforced at the service level and returns HTTP 409 for duplicates
- Input validation rejects blank names and names outside the 2–80 character range with HTTP 400
- Controller tests cover all endpoints including conflict, validation error, and not-found scenarios
- Service tests verify business logic independently of the web layer
- The application compiles successfully with `./mvnw compile -DskipTests`
- All new and existing tests pass with `./mvnw test`
