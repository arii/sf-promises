"""Conservative CI gate: only exact funding-only diffs can skip app tests."""
import os
import re
import subprocess


SHA = re.compile(r"^[0-9a-f]{40}$")


def needs_tests(paths):
    return not paths or any(path != ".github/FUNDING.yml" for path in paths)


def inspect_diff(base, head, run=subprocess.run):
    if not all(SHA.fullmatch(value or "") and set(value) != {"0"} for value in (base, head)):
        return True
    try:
        # Fetch only the two comparison commits, not the repository's full history.
        run(["git", "fetch", "--no-tags", "--depth=1", "origin", base, head],
            check=True, capture_output=True, timeout=60)
        result = run(["git", "diff", "--name-only", "--no-renames", "-z", base, head],
                     check=True, capture_output=True, timeout=30)
        paths = result.stdout.decode("utf-8", errors="strict").rstrip("\0").split("\0")
        return needs_tests(paths)
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return True


if __name__ == "__main__":
    required = inspect_diff(os.environ.get("CI_BASE_SHA"), os.environ.get("CI_HEAD_SHA"))
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"run_tests={str(required).lower()}\n")
    print("Run application gates" if required else "Funding metadata only: application gates not needed")
