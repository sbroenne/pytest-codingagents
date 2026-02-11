"""Run each integration test file individually, generating a separate report per file.

Usage:
    uv run python scripts/run_all.py          # run all test files
    uv run python scripts/run_all.py basic     # run only test_basic.py
    uv run python scripts/run_all.py -k "not test_token"  # pass extra pytest args

Each test file gets its own HTML + JSON report in aitest-reports/<name>.html.
Unit tests run once without aitest reporting (no LLM calls).
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPORTS_DIR = Path("aitest-reports")
TESTS_DIR = Path("tests")
UNIT_DIR = TESTS_DIR / "unit"

# Integration test files (order: fast → slow)
TEST_FILES = [
    "test_basic",
    "test_cli_tools",
    "test_custom_agents",
    "test_events",
    "test_instructions",
    "test_models",
    "test_matrix",
    "test_skills",
]

SUMMARY_MODEL = "azure/gpt-5.2-chat"


def run_unit_tests() -> bool:
    """Run unit tests first (fast, no LLM cost)."""
    print("\n" + "=" * 60)
    print("  UNIT TESTS")
    print("=" * 60)
    result = subprocess.run(
        ["uv", "run", "pytest", str(UNIT_DIR), "-v", "--no-header", "-p", "no:aitest"],
        cwd=Path.cwd(),
    )
    return result.returncode == 0


def run_test_file(name: str, extra_args: list[str] | None = None) -> tuple[bool, float]:
    """Run a single test file with its own report.

    Returns (passed, duration_seconds).
    """
    test_path = TESTS_DIR / f"{name}.py"
    html_path = REPORTS_DIR / f"{name}.html"
    json_path = REPORTS_DIR / f"{name}.json"

    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print(f"  Report: {html_path}")
    print(f"{'=' * 60}")

    cmd = [
        "uv",
        "run",
        "pytest",
        str(test_path),
        "-v",
        "--no-header",
        f"--aitest-html={html_path}",
        f"--aitest-json={json_path}",
        f"--aitest-summary-model={SUMMARY_MODEL}",
    ]
    if extra_args:
        cmd.extend(extra_args)

    start = time.monotonic()
    result = subprocess.run(cmd, cwd=Path.cwd())
    elapsed = time.monotonic() - start

    return result.returncode == 0, elapsed


def main() -> None:
    REPORTS_DIR.mkdir(exist_ok=True)

    # Parse arguments: filter names and extra pytest args
    args = sys.argv[1:]
    extra_pytest_args: list[str] = []
    filter_names: list[str] = []

    for arg in args:
        if arg.startswith("-"):
            extra_pytest_args.append(arg)
        else:
            filter_names.append(arg)

    # Pick which test files to run
    if filter_names:
        files = []
        for name in filter_names:
            # Allow "basic" or "test_basic"
            canonical = name if name.startswith("test_") else f"test_{name}"
            if canonical in TEST_FILES:
                files.append(canonical)
            else:
                print(f"Unknown test file: {name}")
                print(f"Available: {', '.join(TEST_FILES)}")
                sys.exit(1)
    else:
        files = list(TEST_FILES)

    # Run unit tests first (unless filtering to specific integration tests)
    if not filter_names:
        unit_ok = run_unit_tests()
        if not unit_ok:
            print("\n❌ Unit tests failed — fix them before running integration tests.")
            sys.exit(1)

    # Run each integration test file
    results: list[tuple[str, bool, float]] = []
    total_start = time.monotonic()

    for name in files:
        passed, elapsed = run_test_file(name, extra_pytest_args or None)
        results.append((name, passed, elapsed))

    total_elapsed = time.monotonic() - total_start

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"{'Test File':<30} {'Result':<10} {'Time':>8}")
    print("-" * 50)

    passed_count = 0
    for name, passed, elapsed in results:
        status = "PASSED" if passed else "FAILED"
        passed_count += int(passed)
        mins = int(elapsed // 60)
        secs = elapsed % 60
        time_str = f"{mins}:{secs:04.1f}" if mins else f"{secs:.1f}s"
        print(f"  {name:<28} {status:<10} {time_str:>8}")

    print("-" * 50)
    total_mins = int(total_elapsed // 60)
    total_secs = total_elapsed % 60
    total_time = f"{total_mins}:{total_secs:04.1f}" if total_mins else f"{total_secs:.1f}s"
    print(f"  {'Total':<28} {passed_count}/{len(results):<10} {total_time:>8}")

    print(f"\nReports in: {REPORTS_DIR.resolve()}")
    for name, _, _ in results:
        print(f"  - {REPORTS_DIR / f'{name}.html'}")

    # Exit with failure if any test file failed
    if passed_count < len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
