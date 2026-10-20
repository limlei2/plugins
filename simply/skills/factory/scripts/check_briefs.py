#!/usr/bin/env python3
"""Check /simply:factory briefs: required sections present, Criteria non-empty,
no two briefs sharing a "Work in" path. Exit 1 with one line per error."""
import re
import sys
from pathlib import Path

SECTIONS = ["Goal", "Criteria", "Files", "Checks", "Constraints", "Context"]


def sections(text):
    parts = re.split(r"^## +(.+?)\s*$", text, flags=re.M)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts), 2)}


def work_in(files_body):
    m = re.search(r"Work in:\s*(.+)", files_body)
    if not m or m.group(1).strip().lower().startswith("read-only"):
        return []
    return [p.strip(" `") for p in m.group(1).split(",") if p.strip(" `")]


def base(path):
    # shortcut: globs compared by their literal prefix, so `src/**` overlaps `src/a.ts`; precise glob intersection if this gives false alarms
    return re.split(r"[*?\[]", path)[0].rstrip("/")


def overlaps(a, b):
    a, b = base(a), base(b)
    return a == b or a.startswith(b + "/") or b.startswith(a + "/") or not a or not b


def check(paths, max_briefs=5, max_criteria=7):
    errors, claims = [], []
    if not 2 <= len(paths) <= max_briefs:
        errors.append(f"{len(paths)} briefs; a run needs 2 to {max_briefs}")
    for p in paths:
        s = sections(Path(p).read_text())
        for name in SECTIONS:
            if not s.get(name):
                errors.append(f"{p}: missing or empty '## {name}'")
        n = len(re.findall(r"^- \[ \] \S", s.get("Criteria", ""), re.M))
        if s.get("Criteria") and n == 0:
            errors.append(f"{p}: Criteria has no '- [ ] ...' items")
        if n > max_criteria:
            errors.append(f"{p}: {n} criteria; max is {max_criteria}, split the task")
        if s.get("Files") and "Work in:" not in s["Files"]:
            errors.append(f"{p}: Files has no 'Work in:' line")
        claims += [(p, w) for w in work_in(s.get("Files", ""))]
    for i, (p1, w1) in enumerate(claims):
        for p2, w2 in claims[i + 1:]:
            if p1 != p2 and overlaps(w1, w2):
                errors.append(f"{p1} and {p2} both work in '{w1}' / '{w2}'")
    return errors


def _selftest():
    import tempfile
    good = "## Goal\ng\n## Criteria\n- [ ] c\n## Files\n- Work in: `src/a.ts`\n## Checks\n- `x`\n## Constraints\n- k\n## Context\nq\n"
    with tempfile.TemporaryDirectory() as d:
        a, b, c = (Path(d) / n for n in ("a.md", "b.md", "c.md"))
        a.write_text(good)
        b.write_text(good.replace("src/a.ts", "src/b.ts"))
        c.write_text(good.replace("src/a.ts", "src/**").replace("## Goal\ng\n", ""))
        assert check([a, b]) == [], check([a, b])
        errs = check([a, c])
        assert any("Goal" in e for e in errs) and any("both work in" in e for e in errs), errs
        assert any("a run needs" in e for e in check([a])), "single brief must fail"
        b.write_text(good.replace("- [ ] c\n", "- [ ] c\n" * 8).replace("src/a.ts", "src/b.ts"))
        assert any("8 criteria" in e for e in check([a, b])), check([a, b])


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--selftest"]:
        _selftest()
        print("selftest ok")
        sys.exit(0)
    max_briefs = 5
    if args[:1] == ["--research"]:
        max_briefs, args = 6, args[1:]
    if not args:
        sys.exit("usage: check_briefs.py [--research] <brief.md>... | --selftest")
    errs = check(args, max_briefs)
    print("\n".join(errs) or f"ok: {len(args)} briefs")
    sys.exit(1 if errs else 0)
