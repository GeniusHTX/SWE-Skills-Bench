# Task: Implement a Pet Vaccination Tracking Feature Using TDD for Spring PetClinic

## Background

Spring PetClinic (https://github.com/spring-projects/spring-petclinic) is a sample Spring Boot application for managing a veterinary clinic. The project needs a new pet vaccination tracking feature that allows recording vaccinations, checking vaccination status, and generating vaccination reports. The feature must be developed using strict test-driven development — write failing tests first, then implement to pass.

## Files to Create/Modify

- `src/main/java/org/springframework/samples/petclinic/vaccination/Vaccination.java` (create) — JPA entity for vaccination records
- `src/main/java/org/springframework/samples/petclinic/vaccination/VaccinationRepository.java` (create) — Spring Data JPA repository
- `src/main/java/org/springframework/samples/petclinic/vaccination/VaccinationService.java` (create) — Business logic service
- `src/main/java/org/springframework/samples/petclinic/vaccination/VaccinationController.java` (create) — REST controller for vaccination endpoints
- `src/test/java/org/springframework/samples/petclinic/vaccination/VaccinationControllerTests.java` (create) — MockMvc controller tests
- `src/test/java/org/springframework/samples/petclinic/vaccination/VaccinationServiceTests.java` (create) — Service layer unit tests with mock repository
- `src/test/java/org/springframework/samples/petclinic/vaccination/VaccinationRepositoryTests.java` (create) — Repository integration tests

## Requirements

### Vaccination Entity

- JPA entity `Vaccination` with fields:
  - `id` (Integer, auto-generated)
  - `pet` (ManyToOne relationship to existing `Pet` entity)
  - `vaccineName` (String, required, max 100 characters)
  - `vaccineType` (String, one of: `"CORE"`, `"NON_CORE"`, `"REQUIRED"`)
  - `dateAdministered` (LocalDate, required, must not be in the future)
  - `expirationDate` (LocalDate, required, must be after `dateAdministered`)
  - `batchNumber` (String, required, matches pattern `[A-Z]{2}[0-9]{6}`)
  - `veterinarian` (String, required)
  - `notes` (String, optional, max 500 characters)
- Bean validation annotations on all fields with appropriate error messages

### REST API Endpoints

- `GET /api/pets/{petId}/vaccinations` — List all vaccinations for a pet; return 404 if pet not found
- `GET /api/pets/{petId}/vaccinations/{id}` — Get a specific vaccination; return 404 if not found
- `POST /api/pets/{petId}/vaccinations` — Create a vaccination record; return 201; return 400 with validation errors for invalid input
- `GET /api/pets/{petId}/vaccinations/status` — Return vaccination status: list of due, upcoming (within 30 days), and expired vaccinations
- `GET /api/pets/{petId}/vaccinations/report` — Generate a vaccination report with: total vaccinations, vaccinations by type, next due date, compliance status (true if no expired vaccinations)

### Service Layer

- `addVaccination(petId, vaccination)` — validate and save; throw `EntityNotFoundException` if pet not found; throw `DuplicateVaccinationException` if the same vaccine was administered to the same pet on the same date
- `getVaccinationStatus(petId)` — categorize vaccinations into `expired` (expirationDate < today), `due_soon` (expirationDate within 30 days), and `current` (expirationDate > 30 days from now)
- `generateReport(petId)` — aggregate vaccination data into a summary report

### Test Requirements

- **Controller tests** using `MockMvc`: test all endpoints with `@WebMvcTest`, mock the service layer, verify HTTP status codes, response JSON structure, and error handling
- **Service tests**: use `@Mock` for the repository, `@InjectMocks` for the service, use `AssertJ` assertions; test validation logic, duplicate detection, and status categorization
- **Repository tests**: use `@DataJpaTest` with the embedded H2 database; test custom queries, relationship loading, and data integrity constraints
- Test coverage must be at least 80% of the vaccination package (verify with JaCoCo if available)

### Expected Functionality

- `POST /api/pets/1/vaccinations` with `{"vaccineName": "Rabies", "vaccineType": "REQUIRED", "dateAdministered": "2024-01-15", "expirationDate": "2025-01-15", "batchNumber": "AB123456", "veterinarian": "Dr. Smith"}` returns 201
- `POST /api/pets/1/vaccinations` with `dateAdministered` in the future returns 400 with validation error
- `POST /api/pets/1/vaccinations` with `batchNumber: "invalid"` returns 400 mentioning batch number format
- `GET /api/pets/1/vaccinations/status` with one expired vaccination returns `{"expired": [...], "due_soon": [], "current": [...]}`
- `GET /api/pets/999/vaccinations` for non-existent pet returns 404
- Posting same vaccine for same pet on same date returns 409 with duplicate error

## Acceptance Criteria

- Vaccination entity has JPA annotations and bean validation on all fields
- All four REST endpoints return correct HTTP status codes and response structures
- Service validates against duplicates and non-existent pets with appropriate exceptions
- Vaccination status correctly categorizes expired, due-soon, and current vaccinations
- Controller tests use MockMvc and verify status codes, JSON paths, and error responses
- Service tests mock the repository and verify business logic with AssertJ assertions
- Repository tests use @DataJpaTest and verify queries and constraints
- `./mvnw compile -DskipTests` completes successfully
- Test coverage of the vaccination package is at least 80%
