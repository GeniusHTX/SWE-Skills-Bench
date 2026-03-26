# Task: Design Video Transcoding Task System with Celery

## Background
   Design a video transcoding task system based on Celery's Task base class,
   implementing proper task chaining, state updates, and retry logic.

## Files to Create/Modify
   - examples/transcoding/tasks.py
   - examples/transcoding/workflow.py
   - t/unit/tasks/test_transcoding.py

## Requirements
   
   Tasks to Implement (in tasks.py):
   
   1) extract_audio:
      - bind=True (access to self)
      - Call self.update_state to report EXTRACTING status
   
   2) transcode_video:
      - Support meta={'progress': pct} for percentage progress
      - Implement self.retry on failure
      - Max 3 retries, countdown=60
   
   3) generate_thumbnail:
      - Generate thumbnail from video frame
   
   Workflow (in workflow.py):
   - Use chain() to compose: extract_audio.s() | transcode_video.s() | generate_thumbnail.s()
   - Proper signature passing between tasks

4. Test Cases (CELERY_TASK_ALWAYS_EAGER=True):
   - Retry logic (mock transcode failure, verify retry called)
   - Progress reporting assertions
   - Chain execution returns correct final result
   - State updates are recorded

## Acceptance Criteria

   - All three tasks implemented
   - Chain workflow correctly orchestrates tasks
