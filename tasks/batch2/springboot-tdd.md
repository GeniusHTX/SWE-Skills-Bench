# Task: Add a Pet Weight Tracking Feature to Spring PetClinic Using TDD

## Background

Spring PetClinic (https://github.com/spring-projects/spring-petclinic) is a sample Spring Boot application for managing veterinary clinic records. A new feature is needed to track pet weights over time so veterinarians can record measurements and view history. The feature should be developed using a test-driven approach.

## Files to Create/Modify

- `src/main/java/org/springframework/samples/petclinic/weight/WeightRecord.java` (create) — JPA entity for weight records
- `src/main/java/org/springframework/samples/petclinic/weight/WeightRepository.java` (create) — Spring Data repository interface
- `src/main/java/org/springframework/samples/petclinic/weight/WeightController.java` (create) — REST controller for weight endpoints
- `src/main/resources/db/hsqldb/schema.sql` (modify) — Add weight records table schema
- `src/test/java/org/springframework/samples/petclinic/weight/WeightControllerTests.java` (create) — TDD test class

## Requirements

### Data Model

- A weight record captures the pet reference, weight value, unit of measurement, and measurement date
- The relationship between pets and weight records must be properly mapped with JPA

### API / Controller

- Record a new weight entry for a given pet
- Retrieve weight history for a given pet, ordered chronologically
- Reject invalid weights (zero or negative values) with appropriate validation

### Tests

- Follow the Red-Green-Refactor cycle
- Cover: successful weight recording, retrieval in correct chronological order, validation failures, and non-existent pet references

## Expected Functionality

- Adding a weight record for a valid pet persists the data and is retrievable
- Weight history returns entries in chronological order
- Invalid inputs are rejected with appropriate error responses

## Acceptance Criteria

- A valid pet can receive a new weight record containing value, unit, and measurement date.
- Weight history for a pet is returned in chronological order.
- Invalid weights such as zero or negative values are rejected through the application layer.
- Requests referencing a non-existent pet fail with the expected not-found behavior.
- The new feature includes tests that drive the design of the entity, persistence, and API behavior.
