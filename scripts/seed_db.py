"""Seed the DB with a default user + a small set of DSA problems for the Code Lab.

Usage:
    python scripts/seed_db.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.db.connection import transaction  # noqa: E402
from src.db.dao import UserDAO, ProblemDAO  # noqa: E402

# A small starter set of DSA problems. Each test_case is {"stdin": "...", "expected": "..."}.
# Stdin is fed to the student's program via stdin; expected is the exact stdout.
PROBLEMS = [
    {
        "slug": "two-sum",
        "title": "Two Sum",
        "subject": "DSA",
        "topic": "arrays",
        "difficulty": "easy",
        "prompt": (
            "Given a list of integers and a target, print the indices (0-based) of the two numbers "
            "that add up to the target, separated by a single space. The first index must be smaller "
            "than the second. There is exactly one valid answer.\n\n"
            "Input: two lines — first n and target, second n space-separated ints.\n"
            "Output: two indices separated by a space."
        ),
        "starter_code": (
            "import sys\n"
            "def solve():\n"
            "    data = sys.stdin.read().strip().split()\n"
            "    if not data: return\n"
            "    # TODO: parse and solve\n"
            "    pass\n"
            "solve()\n"
        ),
        "test_cases": [
            {"stdin": "4 9\n2 7 11 15", "expected": "0 1"},
            {"stdin": "3 6\n3 2 4", "expected": "1 2"},
            {"stdin": "2 6\n3 3", "expected": "0 1"},
        ],
        "reference": (
            "import sys\n"
            "def solve():\n"
            "    it = iter(sys.stdin.read().strip().split())\n"
            "    n = int(next(it)); target = int(next(it))\n"
            "    a = [int(next(it)) for _ in range(n)]\n"
            "    seen = {}\n"
            "    for i, x in enumerate(a):\n"
            "        if target - x in seen:\n"
            "            print(seen[target - x], i); return\n"
            "        seen[x] = i\n"
            "solve()\n"
        ),
    },
    {
        "slug": "reverse-string",
        "title": "Reverse a String",
        "subject": "DSA",
        "topic": "strings",
        "difficulty": "easy",
        "prompt": (
            "Read a single line and print it reversed.\n\n"
            "Input: one line of text (no newline at end needed).\n"
            "Output: the reversed string."
        ),
        "starter_code": (
            "import sys\n"
            "def solve():\n"
            "    s = sys.stdin.read().rstrip('\\n')\n"
            "    # TODO\n"
            "    pass\n"
            "solve()\n"
        ),
        "test_cases": [
            {"stdin": "hello", "expected": "olleh"},
            {"stdin": "TechMentor", "expected": "rotneMhceT"},
            {"stdin": "a", "expected": "a"},
        ],
        "reference": "import sys\nprint(sys.stdin.read().rstrip('\\n')[::-1])\n",
    },
    {
        "slug": "fizzbuzz",
        "title": "FizzBuzz",
        "subject": "DSA",
        "topic": "loops",
        "difficulty": "easy",
        "prompt": (
            "Print numbers 1..N, one per line, but:\n"
            "  - multiples of 3 -> Fizz\n"
            "  - multiples of 5 -> Buzz\n"
            "  - multiples of both -> FizzBuzz\n\n"
            "Input: a single integer N.\n"
            "Output: N lines."
        ),
        "starter_code": (
            "import sys\n"
            "n = int(sys.stdin.read().strip())\n"
            "# TODO\n"
        ),
        "test_cases": [
            {"stdin": "5", "expected": "1\n2\nFizz\n4\nBuzz"},
            {"stdin": "15", "expected": "\n".join(
                ["1","2","Fizz","4","Buzz","Fizz","7","8","Fizz","Buzz","11","Fizz","13","14","FizzBuzz"]
            )},
        ],
        "reference": (
            "import sys\n"
            "n = int(sys.stdin.read().strip())\n"
            "out = []\n"
            "for i in range(1, n+1):\n"
            "    if i % 15 == 0: out.append('FizzBuzz')\n"
            "    elif i % 3 == 0: out.append('Fizz')\n"
            "    elif i % 5 == 0: out.append('Buzz')\n"
            "    else: out.append(str(i))\n"
            "print('\\n'.join(out))\n"
        ),
    },
    {
        "slug": "binary-search",
        "title": "Binary Search",
        "subject": "DSA",
        "topic": "searching",
        "difficulty": "medium",
        "prompt": (
            "Given a sorted list of distinct integers and a target, print the index of the target "
            "or -1 if not found.\n\n"
            "Input: line 1 = n and target, line 2 = n sorted integers.\n"
            "Output: a single integer."
        ),
        "starter_code": (
            "import sys\n"
            "def solve():\n"
            "    data = sys.stdin.read().strip().split()\n"
            "    # TODO\n"
            "    pass\n"
            "solve()\n"
        ),
        "test_cases": [
            {"stdin": "5 4\n1 2 4 6 8", "expected": "2"},
            {"stdin": "5 5\n1 2 4 6 8", "expected": "-1"},
            {"stdin": "1 1\n1", "expected": "0"},
        ],
        "reference": (
            "import sys\n"
            "it = iter(sys.stdin.read().split())\n"
            "n = int(next(it)); t = int(next(it))\n"
            "a = [int(next(it)) for _ in range(n)]\n"
            "lo, hi = 0, n - 1\n"
            "ans = -1\n"
            "while lo <= hi:\n"
            "    mid = (lo + hi) // 2\n"
            "    if a[mid] == t: ans = mid; break\n"
            "    if a[mid] < t: lo = mid + 1\n"
            "    else: hi = mid - 1\n"
            "print(ans)\n"
        ),
    },
    {
        "slug": "count-vowels",
        "title": "Count Vowels",
        "subject": "DSA",
        "topic": "strings",
        "difficulty": "easy",
        "prompt": (
            "Read a line and print the count of vowels (a, e, i, o, u — case-insensitive) in it.\n\n"
            "Input: one line.\n"
            "Output: a single integer."
        ),
        "starter_code": (
            "import sys\n"
            "s = sys.stdin.read().strip()\n"
            "# TODO\n"
        ),
        "test_cases": [
            {"stdin": "Hello World", "expected": "3"},
            {"stdin": "AEIOU", "expected": "5"},
            {"stdin": "xyz", "expected": "0"},
        ],
        "reference": (
            "import sys\n"
            "print(sum(1 for c in sys.stdin.read().strip().lower() if c in 'aeiou'))\n"
        ),
    },
]


def main() -> None:
    with transaction() as conn:
        uid = UserDAO.get_or_create_default(conn)
        n = 0
        for p in PROBLEMS:
            ProblemDAO.upsert(
                conn,
                slug=p["slug"], title=p["title"], subject=p["subject"], topic=p["topic"],
                difficulty=p["difficulty"], prompt=p["prompt"],
                starter_code=p["starter_code"], test_cases=p["test_cases"],
                reference=p.get("reference"), time_limit_ms=3000,
            )
            n += 1
    print(f"OK: seeded user_id={uid}, problems={n}")


if __name__ == "__main__":
    main()
