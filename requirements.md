# Requirements

## User Story

As a maintainer, I want the GitHub Actions workflows to run reliably and report results so that validation failures are visible and actionable.

## Acceptance Criteria (EARS)

- WHEN the Phase 0 Validation workflow runs on push, pull_request, or manual dispatch, THE SYSTEM SHALL execute the validation script on Ubuntu and upload the validation report artifact.
- WHEN the Phase 0 Validation workflow runs on macOS, THE SYSTEM SHALL execute the validation script and upload the validation report artifact.
- WHEN the Phase 0 Validation workflow runs on Windows, THE SYSTEM SHALL execute the Windows-specific tests with required Python dependencies installed.
- WHEN the Phase 0 Validation workflow finishes on a pull request, THE SYSTEM SHALL post or update a PR comment with the latest validation summary.
- WHEN the nightly validation workflow completes, THE SYSTEM SHALL upload the validation report artifact.
- IF the nightly validation workflow fails, THEN THE SYSTEM SHALL create an issue that includes the failure summary and a link to the workflow run.
- IF a validation report is missing when commenting on a PR, THEN THE SYSTEM SHALL still post a comment indicating the report is unavailable.
