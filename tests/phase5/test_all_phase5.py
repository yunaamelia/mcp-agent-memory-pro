#!/usr/bin/env python3
"""
Master Phase 5 Test Suite
Runs all Phase 5 tests and generates report
"""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def run_test_module(module_name: str) -> dict:
    """Run a test module and capture results"""

    test_file = Path(__file__).parent / f"{module_name}.py"

    result = {"module": module_name, "status": "unknown", "duration": 0, "output": ""}

    if not test_file.exists():
        result["status"] = "skipped"
        result["output"] = f"Test file not found: {test_file}"
        return result

    start_time = datetime.now(UTC)

    try:
        proc = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path(__file__).parent.parent.parent,
        )

        result["duration"] = (datetime.now(UTC) - start_time).total_seconds()
        result["output"] = proc.stdout + proc.stderr
        result["status"] = "passed" if proc.returncode == 0 else "failed"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["output"] = "Test timed out after 60 seconds"
    except Exception as e:
        result["status"] = "error"
        result["output"] = str(e)

    return result


def main():
    """Run all Phase 5 tests"""

    print("\n" + "=" * 70)
    print("        PHASE 5 - COMPLETE VALIDATION SUITE")
    print("=" * 70)
    print(f"\nStarted: {datetime.now(UTC).isoformat()}\n")

    # Test modules to run
    test_modules = [
        "test_ml_engine",
        "test_automation",
        "test_predictive",
        "test_caching",
        "test_plugins",
        "test_plugins_caching",  # pytest-style tests
    ]

    results = []
    passed = 0
    failed = 0

    for module in test_modules:
        print(f"Running {module}...")
        result = run_test_module(module)
        results.append(result)

        if result["status"] == "passed":
            passed += 1
            print(f"  ✅ PASSED ({result['duration']:.2f}s)")
        elif result["status"] == "skipped":
            print("  ⏭️ SKIPPED")
        else:
            failed += 1
            print(f"  ❌ FAILED ({result['status']})")

    # Generate report
    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "summary": {
            "total": len(test_modules),
            "passed": passed,
            "failed": failed,
            "skipped": len([r for r in results if r["status"] == "skipped"]),
        },
        "results": results,
    }

    # Save report
    report_path = Path(__file__).parent.parent / "phase5-validation-report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'=' * 70}")
    print("VALIDATION SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total Tests:  {report['summary']['total']}")
    print(f"  Passed:       {report['summary']['passed']}")
    print(f"  Failed:       {report['summary']['failed']}")
    print(f"  Skipped:      {report['summary']['skipped']}")
    print(f"\nReport saved to: {report_path}")

    if failed > 0:
        print(f"\n❌ VALIDATION FAILED ({failed} test(s) failed)")
        return 1
    else:
        print("\n✅ PHASE 5 VALIDATION COMPLETE - ALL TESTS PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
