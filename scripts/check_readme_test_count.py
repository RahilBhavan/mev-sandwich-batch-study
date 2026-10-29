"""Fail if the test counts written in README.md differ from what pytest collects.

usage: python scripts/check_readme_test_count.py [README]

CI runs this so the prose ("The suite has N tests", "`N passed in ...`") cannot drift from the suite.
"""
import re
import subprocess
import sys


def collected():
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        capture_output=True, text=True, check=True,
    ).stdout
    return int(re.search(r"(\d+) tests? collected", out).group(1))


def main():
    readme = open(sys.argv[1] if len(sys.argv) > 1 else "README.md", encoding="utf-8").read()
    claimed = {int(n) for n in re.findall(r"suite has (\d+) tests", readme)}
    claimed |= {int(n) for n in re.findall(r"`(\d+) passed", readme)}
    if not claimed:
        sys.exit("README.md states no test count; add one or drop this check.")
    actual = collected()
    if claimed != {actual}:
        sys.exit(f"README.md states {sorted(claimed)} tests but pytest collects {actual}.")
    print(f"README test count matches pytest: {actual}")


if __name__ == "__main__":
    main()
