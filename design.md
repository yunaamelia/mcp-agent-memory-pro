# Design

## Architecture

- Workflow A: Phase 0 Validation (push, pull_request, workflow_dispatch)
  - Runs validation on Ubuntu, macOS, and Windows.
  - Publishes a validation report artifact on Ubuntu and macOS.
- Workflow B: Phase 0 PR Comment (workflow_run)
  - Listens for completion of Phase 0 Validation on pull requests.
  - Downloads the Ubuntu validation report artifact and posts a summary comment.
- Workflow C: Phase 0 Nightly Validation (schedule, workflow_dispatch)
  - Runs validation on a nightly schedule.
  - Uploads a report artifact and opens an issue when validation fails.

## Data Flow

1. Phase 0 Validation generates poc/validation-report.json and poc/validation.log.
2. The artifact validation-report-ubuntu is uploaded from the Ubuntu job.
3. Phase 0 PR Comment downloads validation-report-ubuntu and reads reports/validation-report.json.
4. Nightly Validation uploads the nightly report artifact and optionally creates an issue with a run URL.

## Interfaces

- Artifact name: validation-report-ubuntu
- Report path (producer): poc/validation-report.json
- Report path (consumer): reports/validation-report.json
- Run URL format: ${serverUrl}/${owner}/${repo}/actions/runs/${runId}

## Error Handling

- Validation steps use continue-on-error and a final explicit fail step based on outcome.
- PR comment workflow handles missing artifacts and reports by posting a warning.
- Nightly workflow issue creation handles JSON parsing failures and still posts a minimal issue body.

## Unit Testing Strategy

- No additional unit tests are required for workflow changes.
- Validation behavior is verified by the existing Phase 0 validation scripts and workflow executions.
