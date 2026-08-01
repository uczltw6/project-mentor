# Project Mentor learning receipt

_Generated: 2026-08-01T09:05:00Z_

## What we completed

- Goal: Add and verify a health endpoint
- Current mode: `guided`
- Milestone: Health endpoint verified — The endpoint contract passed its focused test.

## Knowledge actually used in this project

### Request routing

- What it is: A route connects an HTTP method and path to the function that handles it.
- Why it mattered here: The new health endpoint needs a stable entry point.
- Project evidence:
  - `tests/test_app.py::test_health` — The focused health-route test passed. (observed)
- Decision made: Keep the health response minimal and deterministic.
- Agent demonstrated: project use supported by the evidence above; this does not imply user capability
- You demonstrated: Exposure: encountered; understanding not yet verified
- If this changes: Changing the method or path would break callers and focused tests.
- Small next practice: Add one failing test for an unknown route and explain the expected status.

## Key design decisions

- Keep the health response minimal and deterministic. — A stable status-only body is easier to consume and reveals less operational detail.

## Understanding not yet demonstrated

- Request routing

## Deferred / learn later

- None
