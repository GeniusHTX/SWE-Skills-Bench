# Task: Add Pet Weight Tracking Feature to PetClinic

## Background

We need to add a weight tracking feature to the Spring PetClinic application. Pet owners should be able to record and view their pets' weight history over time.

## Files to Create/Modify

- `src/main/java/org/springframework/samples/petclinic/owner/WeightRecord.java` - Entity class
- `src/main/java/org/springframework/samples/petclinic/owner/WeightRecordRepository.java` - Data access
- `src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java` - REST endpoints
- `src/main/resources/db/h2/` - DDL for weight_record table

## Requirements

### Entity (WeightRecord.java)

- `id`: Long (Primary Key)
- `petId`: Long (Foreign Key to Pet)
- `weightKg`: Double (Required, positive value)
- `recordDate`: LocalDate

### Repository

- Extend `JpaRepository<WeightRecord, Long>`
- Method: `findByPetIdOrderByRecordDateDesc(Long petId)`

### Controller Endpoints

- `POST /owners/{ownerId}/pets/{petId}/weight` - Record new weight
- `GET /owners/{ownerId}/pets/{petId}/weight/history` - Get weight history

### Database

- Create DDL in `src/main/resources/db/h2/`

## Expected Functionality

1. Successfully record pet weight → returns 201 Created
2. Reject invalid petId → returns 404 Not Found
3. Reject missing weightKg field → returns 400 Bad Request
4. Weight history returns list ordered by date (newest first)

## Acceptance Criteria

- Application compiles without errors: `./mvnw compile`
- All CRUD operations work correctly
- Endpoints handle edge cases appropriately (invalid input, missing data)
