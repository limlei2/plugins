#!/usr/bin/env python3
"""Check a /simply:goodnight daily log against references/daily-log-format.md.
Exit 1 with one line per error. Used by goodnight (writer) and goodmorning (reader)."""
import re
import sys
from pathlib import Path

HEADINGS = ["Summary", "Done", "In progress", "Blocked", "Decisions", "Open questions",
            "Tomorrow", "Skill notes", "Handoffs", "Durable facts saved"]
HEADER_KEYS = ["project", "updated", "head", "branches"]
# section -> keys every item line must carry
ITEM_KEYS = {
    "Done": ["verified"],
    "In progress": ["branch", "next"],
    "Blocked": ["blocker", "unblocks"],
    "Decisions": ["why"],
    "Tomorrow": ["why"],
    "Skill notes": ["issue", "suggest"],
}


def check(text):
    errors = []
    lines = text.splitlines()
    if not lines or not re.match(r"^# Daily log \d{4}-\d{2}-\d{2}$", lines[0]):
        errors.append("line 1 must be '# Daily log YYYY-MM-DD'")
    for key in HEADER_KEYS:
        if not re.search(rf"^- {key}: \S", text, re.M):
            errors.append(f"header missing '- {key}: ...'")

    found = re.findall(r"^## (.+?)\s*$", text, re.M)
    if found != HEADINGS:
        errors.append(f"headings must be exactly {HEADINGS} in order; found {found}")

    parts = re.split(r"^## (.+?)\s*$", text, flags=re.M)
    sections = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}
    for name in HEADINGS:
        body = sections.get(name, "")
        if not body:
            errors.append(f"'## {name}' is empty; write '- none'")
            continue
        if body == "- none":
            continue
        items = [l for l in body.splitlines() if l.strip()]
        if name == "Tomorrow" and not all(re.match(r"^\d+\. ", l) for l in items):
            errors.append("Tomorrow items must be a numbered list ('1. ...')")
        for line in items:
            for key in ITEM_KEYS.get(name, []):
                if not re.search(rf"\| {key}: \S", line):
                    errors.append(f"{name}: missing '| {key}: ...' in: {line[:70]}")
    return errors


def _example():
    fmt = (Path(__file__).parent.parent / "references" / "daily-log-format.md").read_text()
    return re.search(r"```markdown\n(.*?)```", fmt, re.S).group(1)


def _selftest():
    good = _example()
    assert check(good) == [], check(good)
    assert check(good.replace("## Blocked", "## Blockers")), "renamed heading must fail"
    bad = good.replace("| next: add dead-letter", "| nxt: add dead-letter")
    assert any("next" in e for e in check(bad)), check(bad)
    assert any("'- none'" in e for e in check(good.replace(
        "## Open questions\n- Should", "## Open questions\n\n## X\n- Should")))


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        _selftest()
        print("selftest ok")
        sys.exit(0)
    if len(sys.argv) != 2:
        sys.exit("usage: check_log.py <log.md> | --selftest")
    errs = check(Path(sys.argv[1]).read_text())
    print("\n".join(errs) or "ok")
    sys.exit(1 if errs else 0)
