"""Code runner tests — subprocess execution + test case matching."""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.services.code_runner import run_code


def test_simple_pass():
    code = "print(input())"
    cases = [{"stdin": "hello", "expected": "hello"}]
    result = run_code(code, cases)
    assert result.passed == 1
    assert result.total == 1


def test_simple_fail():
    code = "print('wrong')"
    cases = [{"stdin": "", "expected": "correct"}]
    result = run_code(code, cases)
    assert result.passed == 0
    assert result.total == 1


def test_multiple_cases_mixed():
    code = """
n = int(input())
print(n * 2)
"""
    cases = [
        {"stdin": "3", "expected": "6"},
        {"stdin": "5", "expected": "10"},
        {"stdin": "0", "expected": "0"},
    ]
    result = run_code(code, cases)
    assert result.passed == 3
    assert result.total == 3


def test_runtime_error():
    code = "raise ValueError('boom')"
    cases = [{"stdin": "", "expected": ""}]
    result = run_code(code, cases)
    assert result.passed == 0
    assert result.cases[0].error is not None


def test_syntax_error():
    code = "def foo(: pass"
    cases = [{"stdin": "", "expected": ""}]
    result = run_code(code, cases)
    assert result.passed == 0


def test_timeout():
    code = "import time; time.sleep(10)"
    cases = [{"stdin": "", "expected": ""}]
    result = run_code(code, cases, time_limit_ms=500)
    assert result.passed == 0
    assert any(c.error and "TLE" in c.error for c in result.cases)


def test_fizzbuzz():
    code = """
n = int(input())
for i in range(1, n+1):
    if i % 15 == 0: print('FizzBuzz')
    elif i % 3 == 0: print('Fizz')
    elif i % 5 == 0: print('Buzz')
    else: print(i)
"""
    expected = "\n".join(["1","2","Fizz","4","Buzz","Fizz","7","8","Fizz","Buzz","11","Fizz","13","14","FizzBuzz"])
    cases = [{"stdin": "15", "expected": expected}]
    result = run_code(code, cases)
    assert result.passed == 1


def test_empty_cases():
    result = run_code("print(1)", [])
    assert result.total == 0
    assert result.passed == 0
