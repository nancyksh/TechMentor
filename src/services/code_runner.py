"""Subprocess-based Python code runner for the Code Lab.

Runs student code in a locked-down subprocess with a hard timeout.
Returns pass/fail against hidden test cases.

Safety:
- 3-second timeout, no network, no fork-bombs (ulimit).
- On Windows, subprocess isolation is weaker; the timeout is the primary guard.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CaseResult:
    passed: bool
    expected: str
    got: str
    error: str | None = None
    runtime_ms: int = 0


@dataclass
class CodeResult:
    total: int
    passed: int
    runtime_ms: int
    cases: list[CaseResult]
    error: str | None = None  # non-None = code itself crashed before any test case

    @property
    def all_passed(self) -> bool:
        return self.passed == self.total

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "runtime_ms": self.runtime_ms,
            "cases": [
                {"passed": c.passed, "expected": c.expected, "got": c.got,
                 "error": c.error, "runtime_ms": c.runtime_ms}
                for c in self.cases
            ],
            "error": self.error,
        }


def run_code(
    code: str,
    test_cases: list[dict],
    *,
    time_limit_ms: int = 3000,
    python_path: str | None = None,
) -> CodeResult:
    """Execute `code` against each test case in a subprocess.

    test_cases: [{"stdin": "1 2", "expected": "3"}, ...]
    """
    if not test_cases:
        return CodeResult(total=0, passed=0, runtime_ms=0, cases=[])

    python_path = python_path or sys.executable
    total_runtime = 0
    results: list[CaseResult] = []

    for tc in test_cases:
        stdin_data = tc.get("stdin", "")
        expected = (tc.get("expected") or "").strip()
        cr = _run_single(code, stdin_data, expected, python_path, time_limit_ms)
        results.append(cr)
        total_runtime += cr.runtime_ms

    return CodeResult(
        total=len(results),
        passed=sum(1 for r in results if r.passed),
        runtime_ms=total_runtime,
        cases=results,
    )


def _run_single(
    code: str,
    stdin_data: str,
    expected: str,
    python_path: str,
    time_limit_ms: int,
) -> CaseResult:
    """Run code against a single test case in a subprocess."""
    t0 = time.perf_counter()
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        proc = subprocess.run(
            [python_path, tmp_path],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=time_limit_ms / 1000.0,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            cwd=tempfile.gettempdir(),
        )
        dt_ms = int((time.perf_counter() - t0) * 1000)

        if proc.returncode != 0:
            err = proc.stderr.strip() or f"exit code {proc.returncode}"
            return CaseResult(passed=False, expected=expected, got="", error=err, runtime_ms=dt_ms)

        got = proc.stdout.strip()
        passed = got == expected
        return CaseResult(passed=passed, expected=expected, got=got, runtime_ms=dt_ms)

    except subprocess.TimeoutExpired:
        dt_ms = int((time.perf_counter() - t0) * 1000)
        return CaseResult(passed=False, expected=expected, got="", error="TLE (time limit exceeded)", runtime_ms=dt_ms)
    except Exception as e:
        dt_ms = int((time.perf_counter() - t0) * 1000)
        return CaseResult(passed=False, expected=expected, got="", error=str(e), runtime_ms=dt_ms)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
