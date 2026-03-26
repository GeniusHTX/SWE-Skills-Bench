# Task: Add Nx Workspace Demo with Generator

## Background
   Add a minimal Nx workspace demo with a custom generator stub
   and affected task listing.

## Files to Create/Modify
   - examples/nx-demo/workspace.json (or nx.json)
   - examples/nx-demo/packages/my-lib/ (sample library)
   - examples/nx-demo/tools/generators/my-generator/ (custom generator)

## Requirements
   
   Workspace Configuration:
   - Basic Nx configuration
   - Sample library package
   - Generator configuration
   
   Custom Generator:
   - schema.json defining inputs
   - index.ts with generator implementation stub
   - Template files (optional)
   
   Affected Commands:
   - `nx affected:build` working
   - `nx affected:test` working
   - Proper dependency graph

4. Generator Schema:
   - name: string input
   - directory: optional string
   - tags: optional string array

## Acceptance Criteria
   - `npx nx affected:list` exits with code 0
   - Generator schema validates successfully
   - Output shows affected projects or "No affected projects"
