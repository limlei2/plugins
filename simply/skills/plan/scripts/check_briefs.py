#!/usr/bin/env python3
"""Check /simply:plan task briefs: required sections present, 1-7 criteria, 1-5 tasks.
With --parallel (subagents mode): 2-5 tasks and no two sharing a "Work in" path.
Exit 1 with one line per error."""
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


def check(paths, parallel=False, max_briefs=5, max_criteria=7):
    errors, claims = [], []
    min_briefs = 2 if parallel else 1
    if not min_briefs <= len(paths) <= max_briefs:
        errors.append(f"{len(paths)} briefs; a run needs {min_briefs} to {max_briefs}")
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
    for i, (p1, w1) in enumerate(claims if parallel else []):
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
        assert check([a, b], parallel=True) == [], check([a, b], parallel=True)
        errs = check([a, c], parallel=True)
        assert any("Goal" in e for e in errs) and any("both work in" in e for e in errs), errs
        assert not any("both work in" in e for e in check([a, c])), "sequential tasks may share files"
        assert check([a]) == [], "one task is fine for tdd"
        assert any("a run needs" in e for e in check([a], parallel=True)), "parallel needs 2+"
        b.write_text(good.replace("- [ ] c\n", "- [ ] c\n" * 8).replace("src/a.ts", "src/b.ts"))
        assert any("8 criteria" in e for e in check([a, b])), check([a, b])
        r1, r2 = Path(d) / "r1.md", Path(d) / "r2.md"
        r1.write_text(good.replace("- Work in: `src/a.ts`", "- Work in: read-only").replace("- `x`", "- none"))
        r2.write_text(r1.read_text())
        assert check([r1]) == [], check([r1])


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--selftest"]:
        _selftest()
        print("selftest ok")
        sys.exit(0)
    parallel = args[:1] == ["--parallel"]
    args = args[1:] if parallel else args
    if not args:
        sys.exit("usage: check_briefs.py [--parallel] <brief.md>... | --selftest")
    errs = check(args, parallel)
    print("\n".join(errs) or f"ok: {len(args)} briefs")
    sys.exit(1 if errs else 0)
