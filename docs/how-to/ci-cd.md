# CI/CD Integration

Run integration tests in GitHub Actions.

## Manual Trigger

The repository includes a `workflow_dispatch` workflow for running integration tests on demand.

### Prerequisites

1. Create a GitHub environment called `integration` in your repo settings
2. Add a secret `COPILOT_GITHUB_TOKEN` with a GitHub token that has Copilot access

### Running

Go to **Actions** → **Integration Tests** → **Run workflow**.

Optionally provide a `-k` filter to run specific tests (e.g., `test_basic`).

## Unit Tests in CI

Unit tests run automatically on every push and PR via the `ci.yml` workflow. These don't require Copilot access — they test pure logic with no SDK calls.

## Token Management

Integration tests use real Copilot API calls:

- **Keep tests focused** — one prompt per test
- **Use `max_turns`** — limit conversation turns to control cost
- **Use `timeout_s`** — set reasonable timeouts to avoid runaway tests
- **Filter with `-k`** — run only the tests you need
