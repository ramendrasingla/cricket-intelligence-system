#!/usr/bin/env python3
"""
Master Test Runner for Cricket Intelligence System

Runs all test suites in the correct order:
1. News Pipeline
2. Stats Pipeline
3. News MCP Tools
4. Stats MCP Tools

Usage:
    python tests/run_all_tests.py                    # Run all tests
    python tests/run_all_tests.py --pipelines        # Run only pipeline tests
    python tests/run_all_tests.py --tools            # Run only MCP tool tests
    python tests/run_all_tests.py --news             # Run only news-related tests
    python tests/run_all_tests.py --stats            # Run only stats-related tests
"""

import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent


def run_test_file(test_file: Path, test_name: str) -> dict:
    """Run a single test file and return results"""
    print("\n" + "=" * 70)
    print(f"Running: {test_name}")
    print("=" * 70)

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return {"name": test_name, "passed": False, "error": "File not found"}

    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        passed = result.returncode == 0

        return {
            "name": test_name,
            "passed": passed,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except subprocess.TimeoutExpired:
        print(f"❌ Test timed out after 120 seconds")
        return {"name": test_name, "passed": False, "error": "Timeout"}

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return {"name": test_name, "passed": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Run Cricket Intelligence System tests")
    parser.add_argument("--pipelines", action="store_true", help="Run only pipeline tests")
    parser.add_argument("--tools", action="store_true", help="Run only MCP tool tests")
    parser.add_argument("--news", action="store_true", help="Run only news-related tests")
    parser.add_argument("--stats", action="store_true", help="Run only stats-related tests")
    args = parser.parse_args()

    # Define test suites
    all_tests = [
        ("News Pipeline", PROJECT_ROOT / "tests" / "test_news_pipeline.py", ["pipelines", "news"]),
        ("Stats Pipeline", PROJECT_ROOT / "tests" / "test_stats_pipeline.py", ["pipelines", "stats"]),
        ("News MCP Tools", PROJECT_ROOT / "tests" / "test_news_tools.py", ["tools", "news"]),
        ("Stats MCP Tools", PROJECT_ROOT / "tests" / "test_stats_tools.py", ["tools", "stats"])
    ]

    # Filter tests based on arguments
    tests_to_run = []

    if args.pipelines or args.tools or args.news or args.stats:
        for test_name, test_file, tags in all_tests:
            should_run = False
            if args.pipelines and "pipelines" in tags:
                should_run = True
            if args.tools and "tools" in tags:
                should_run = True
            if args.news and "news" in tags:
                should_run = True
            if args.stats and "stats" in tags:
                should_run = True

            if should_run:
                tests_to_run.append((test_name, test_file))
    else:
        # Run all tests
        tests_to_run = [(name, file) for name, file, _ in all_tests]

    # Print header
    print("\n" + "=" * 70)
    print("Cricket Intelligence System - Test Suite")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tests to run: {len(tests_to_run)}")
    print("=" * 70)

    # Run tests
    results = []
    for test_name, test_file in tests_to_run:
        result = run_test_file(test_file, test_name)
        results.append(result)

    # Print summary
    print("\n\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for result in results:
        status = "✓ PASS" if result.get("passed") else "❌ FAIL"
        test_name = result["name"]
        print(f"{status}: {test_name}")

        if not result.get("passed") and "error" in result:
            print(f"       Error: {result['error']}")

    # Calculate stats
    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    failed = total - passed

    print("\n" + "-" * 70)
    print(f"Total: {total} test suites")
    print(f"Passed: {passed} ✓")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    print("=" * 70)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Exit with appropriate code
    return 0 if all(r.get("passed") for r in results) else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
