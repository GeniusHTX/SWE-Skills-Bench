# Task: Design a Video Transcoding Task System with Celery

## Background

Celery (https://github.com/celery/celery) is a distributed task queue for Python. A new example application is needed that demonstrates a video transcoding workflow using Celery tasks, including task chaining, error handling, progress tracking, and retry logic.

## Files to Create

- `examples/transcoding/tasks.py` — Celery task definitions for the transcoding pipeline
- `examples/transcoding/workflow.py` — Workflow orchestration composing tasks into a pipeline

## Requirements

### Task Definitions (`tasks.py`)

- Define Celery tasks for distinct stages of a video transcoding pipeline (e.g., input validation, transcoding, thumbnail generation, notification)
- Each task should accept clearly typed parameters and return a structured result
- Include retry configuration for tasks that may fail transiently (e.g., network-based operations)
- Include error callbacks or handlers for task failure scenarios

### Workflow Orchestration (`workflow.py`)

- Compose the individual tasks into a workflow using Celery's primitives (chains, groups, or chords)
- Define at least one sequential pipeline (task A → task B → task C)
- Define at least one parallel fan-out step (multiple tasks running concurrently)
- Include progress tracking or status reporting capability

### Configuration

- Tasks should declare appropriate `bind`, `max_retries`, `default_retry_delay`, and `acks_late` settings where relevant
- The workflow module should be importable and define a main entry point function that kicks off the pipeline

## Expected Functionality

- Invoking the workflow processes a video through all pipeline stages in the correct order
- Failed tasks retry according to their configuration
- Parallel steps execute concurrently and their results are aggregated
- The overall workflow reports success or failure with appropriate detail

## Acceptance Criteria

- The example expresses a complete video-processing workflow with clearly separated Celery tasks for multiple stages.
- The workflow includes both sequential composition and at least one parallel fan-out step.
- Tasks that can fail transiently declare retry behavior and surface failures through explicit error handling.
- The orchestration entry point can launch the workflow and report its progress or status.
- Task inputs and outputs are structured consistently enough to connect stages without ambiguity.
