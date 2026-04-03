# Task: Add a Medication Resource with TDD to Spring PetClinic

## Background

Spring PetClinic (https://github.com/spring-projects/spring-petclinic) is the canonical Spring Boot sample application. It manages owners, pets, vets, and visits. This task requires adding a new "Medication" resource using Test-Driven Development: write the tests first, then implement the entity, repository, service, and controller to make them pass.

## Files to Create/Modify

- `src/test/java/org/springframework/samples/petclinic/medication/MedicationControllerTests.java` (create) — Controller tests using `@WebMvcTest`: test list medications, add medication, view medication detail, validate form errors.
- `src/test/java/org/springframework/samples/petclinic/medication/MedicationRepositoryTests.java` (create) — Repository integration tests using `@DataJpaTest`: test findByPetId, save, findActive medications.
- `src/main/java/org/springframework/samples/petclinic/medication/Medication.java` (create) — JPA entity with fields: `id`, `name`, `dosage`, `frequency`, `startDate`, `endDate` (nullable = ongoing), `pet` (ManyToOne relationship), `prescribedBy` (ManyToOne to Vet).
- `src/main/java/org/springframework/samples/petclinic/medication/MedicationRepository.java` (create) — Spring Data JPA repository with custom queries: `findByPetId(Integer petId)`, `findActiveMedications(Integer petId, LocalDate date)` (where endDate is null or > date).
- `src/main/java/org/springframework/samples/petclinic/medication/MedicationController.java` (create) — Thymeleaf controller: `GET /owners/{ownerId}/pets/{petId}/medications` (list), `GET .../medications/new` (form), `POST .../medications/new` (submit), `GET .../medications/{medId}` (detail).
- `src/main/resources/db/h2/data.sql` (modify) — Add sample medication data for existing pets.
- `src/main/resources/templates/medications/medicationList.html` (create) — Thymeleaf template displaying a pet's medications in a table.
- `src/main/resources/templates/medications/createOrUpdateMedicationForm.html` (create) — Form template for adding/editing medications.

## Requirements

### Entity

- `Medication` extends `BaseEntity` (inheriting `id`).
- Fields: `name` (String, not blank, max 100), `dosage` (String, not blank, e.g., "500mg"), `frequency` (String, not blank, e.g., "twice daily"), `startDate` (LocalDate, not null), `endDate` (LocalDate, nullable), `notes` (String, max 500).
- Relationships: `@ManyToOne Pet pet`, `@ManyToOne Vet prescribedBy`.
- Validation: `startDate` must not be in the future, `endDate` if set must be >= `startDate`.

### Repository

- `List<Medication> findByPetId(Integer petId)` — all medications for a pet, ordered by startDate desc.
- `@Query` for `findActiveMedications`: `SELECT m FROM Medication m WHERE m.pet.id = :petId AND (m.endDate IS NULL OR m.endDate >= :currentDate) ORDER BY m.startDate DESC`.
- Standard `save(Medication)` from `CrudRepository`.

### Controller

- `GET /owners/{ownerId}/pets/{petId}/medications` — populates model with pet object and medication list, returns `medications/medicationList` view.
- `GET .../medications/new` — populates model with empty `Medication` object and list of vets, returns form view.
- `POST .../medications/new` — validates `@Valid Medication`, binds to pet identified by `petId`, saves, redirects to list. On validation error, returns form view.
- Controller validates that the `petId` belongs to the `ownerId` (prevent IDOR).

### Tests (Write First)

- **Controller tests**:
  - `testListMedications` — mock repository returning 2 medications, verify view name and model attribute.
  - `testAddMedicationSuccess` — POST valid medication, verify redirect to list.
  - `testAddMedicationValidationError` — POST with blank name, verify form view returned with error.
  - `testAddMedicationFutureStartDate` — POST with startDate tomorrow, verify validation error.
- **Repository tests**:
  - `testFindByPetId` — insert medications for 2 different pets, query by one petId, verify correct results.
  - `testFindActiveMedications` — insert 3 medications (1 ended, 1 ongoing, 1 ending tomorrow), verify only 2 active returned.
  - `testSave` — save a medication and verify it's retrievable.

### Expected Functionality

- Viewing pet "Leo"'s page → navigate to medications → see a table of current medications with name, dosage, frequency, and prescribing vet.
- Adding a new medication with name="Amoxicillin", dosage="250mg", frequency="3x daily" → medication appears in the list.
- Adding a medication with an end date before start date → validation error displayed on the form.
- `findActiveMedications(petId, today)` excludes medications where `endDate < today`.

## Acceptance Criteria

- Tests are written before implementation and cover controller, repository, and validation logic.
- `Medication` entity has correct JPA annotations and validation constraints.
- Repository custom query returns only active medications correctly.
- Controller handles CRUD operations with proper validation and error handling.
- Controller validates that pet belongs to the specified owner.
- Sample data is added to `data.sql` for at least 3 medications across 2 pets.
- `./mvnw test` passes all new and existing tests.
- `./mvnw compile` succeeds without errors.
