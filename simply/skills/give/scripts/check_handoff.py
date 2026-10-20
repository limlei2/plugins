#!/usr/bin/env python3
"""Check a /simply:give handoff against references/handoff-format.md.
Exit 1 with one line per error. Used by give (writer) and take (reader)."""
import re
import sys
from pathlib import Path

HEADINGS = ["Goal", "Done so far", "In progress", "Exact next step", "Decisions and why",
            "Dead ends", "Files involved", "Code state", "How to verify", "Open questions",
            "Note from giver"]
STATUS = r"^Status: (open|taken by .+ at \d{4}-\d{2}-\d{2} \d{2}:\d{2})$"
SHA = r"[0-9a-f]{40}"


def check(text):
    errors = []
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# Handoff: "):
        errors.append("line 1 must be '# Handoff: <title>'")
    if len(lines) < 3 or not re.match(STATUS, lines[2]):
        errors.append("line 3 must be 'Status: open' or 'Status: taken by <name> at <YYYY-MM-DD HH:MM>'")
    if not re.search(r"^Created: \d{4}-\d{2}-\d{2} \d{2}:\d{2} by \S", text, re.M):
        errors.append("missing 'Created: <YYYY-MM-DD HH:MM> by <name>'")

    found = re.findall(r"^## (.+?)\s*$", text, re.M)
    if found != HEADINGS:
        errors.append(f"headings must be exactly {HEADINGS} in order; found {found}")

    parts = re.split(r"^## (.+?)\s*$", text, flags=re.M)
    sections = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}
    for name in HEADINGS:
        if not sections.get(name):
            errors.append(f"'## {name}' is empty; write 'None.'")

    code = sections.get("Code state", "")
    branch = re.search(r"^Branch: (.+)$", code, re.M)
    if not branch:
        errors.append("Code state missing 'Branch:'")
    git = branch and not branch.group(1).startswith("none")
    if git and not re.search(rf"^Commit: {SHA}$", code, re.M):
        errors.append("Code state 'Commit:' must be a full 40-char SHA")
    if git and not re.search(rf"^Stash: ({SHA}|none)$", code, re.M):
        errors.append("Code state 'Stash:' must be a full 40-char SHA or 'none'")
    if not re.search(r"^Dirty files:", code, re.M):
        errors.append("Code state missing 'Dirty files:'")
    for line in sections.get("Files involved", "").splitlines():
        if line.startswith("- ") and not re.match(r"^- `[^`]+`", line):
            errors.append(f"Files involved item must start with a backticked path: {line[:70]}")
    for line in sections.get("Done so far", "").splitlines():
        if line.startswith("- ") and "Verified:" not in line:
            errors.append(f"Done so far item has no 'Verified:': {line[:70]}")
    return errors


def _example():
    fmt = (Path(__file__).parent.parent / "references" / "handoff-format.md").read_text()
    return re.search(r"```markdown\n(.*?)```", fmt, re.S).group(1)


def _selftest():
    good = _example()
    assert check(good) == [], check(good)
    assert check(good.replace("Status: open", "Status: done")), "bad status must fail"
    assert check(good.replace("## Dead ends", "## Dead-ends")), "renamed heading must fail"
    assert any("40-char" in e for e in check(re.sub(r"Commit: \w+", "Commit: 3f9c2a1", good)))
    assert check(good.replace("- `src/webhooks/retry.ts`", "- src/webhooks/retry.ts")), "unbackticked path must fail"
    picked = good.replace("Status: open", "Status: taken by limlei2 at 2026-10-21 09:15")
    assert check(picked) == [], check(picked)


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        _selftest()
        print("selftest ok")
        sys.exit(0)
    if len(sys.argv) != 2:
        sys.exit("usage: check_handoff.py <handoff.md> | --selftest")
    errs = check(Path(sys.argv[1]).read_text())
    print("\n".join(errs) or "ok")
    sys.exit(1 if errs else 0)
