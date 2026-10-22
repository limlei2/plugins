#!/usr/bin/env python3
"""Check /simply:plan task briefs: required sections present, 1-7 criteria, 1-10 tasks,
an Estimate line unless read-only, Uses/Provides lines, and every `Uses: task <n>: X`
naming an earlier brief whose Provides has X verbatim (looked up beside the brief when
not passed, so a loop's fix briefs can be checked alone).
With --parallel (subagents mode): 2-5 tasks, no two sharing a "Work in" path, and none
using another's Provides. Exit 1 with one line per error."""
import re
import sys
from pathlib import Path

SECTIONS = ["Goal", "Criteria", "Files", "Interfaces", "Checks", "Constraints", "Context"]


def sections(text):
    parts = re.split(r"^## +(.+?)\s*$", text, flags=re.M)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts), 2)}


def work_in(files_body):
    m = re.search(r"Work in:\s*(.+)", files_body)
    if not m or m.group(1).strip().lower().startswith("read-only"):
        return []
    return [p.strip(" `") for p in m.group(1).split(",") if p.strip(" `")]


def items(body, key):
    return [m.group(1).strip() for m in re.finditer(rf"^- {key}:\s*(.+?)\s*$", body, re.M)]


def number(path):
    m = re.match(r"(\d+)-", Path(path).name)
    return int(m.group(1)) if m else None


def find_task(n, path, paths):
    for q in paths:
        if number(q) == n:
            return Path(q)
    return next(iter(sorted(Path(path).parent.glob(f"{n}-*.md"))), None)


def check_uses(p, uses, paths, parallel):
    errors = []
    for u in uses:
        m = re.match(r"task (\d+):\s*(.+)", u)
        if not m:
            continue
        n, text = int(m.group(1)), m.group(2).strip()
        dep = find_task(n, p, paths)
        if dep is None:
            errors.append(f"{p}: uses task {n}, but there is no brief {n}-*.md")
            continue
        own = number(p)
        if own is not None and n >= own:
            errors.append(f"{p}: uses task {n}, which does not run before it")
        if parallel and any(Path(q).resolve() == dep.resolve() for q in paths):
            errors.append(f"{p}: runs in parallel with task {n}, so it can't use its Provides")
        if text not in items(sections(dep.read_text()).get("Interfaces", ""), "Provides"):
            errors.append(f"{p}: '{text}' is not in task {n}'s Provides")
    return errors


def base(path):
    # shortcut: globs compared by their literal prefix, so `src/**` overlaps `src/a.ts`; precise glob intersection if this gives false alarms
    return re.split(r"[*?\[]", path)[0].rstrip("/")


def overlaps(a, b):
    a, b = base(a), base(b)
    return a == b or a.startswith(b + "/") or b.startswith(a + "/") or not a or not b


def check(paths, parallel=False, max_criteria=7):
    errors, claims = [], []
    min_briefs, max_briefs = (2, 5) if parallel else (1, 10)
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
        if work_in(s.get("Files", "")) and not re.search(r"^- Estimate:\s*~?\d", s["Files"], re.M):
            errors.append(f"{p}: Files has no '- Estimate: ~<n> changed lines across <m> files' line")
        iface = s.get("Interfaces", "")
        if iface and not (items(iface, "Uses") and items(iface, "Provides")):
            errors.append(f"{p}: Interfaces needs '- Uses:' and '- Provides:' lines (write none when there are none)")
        errors += check_uses(p, items(iface, "Uses"), paths, parallel)
        claims += [(p, w) for w in work_in(s.get("Files", ""))]
    for i, (p1, w1) in enumerate(claims if parallel else []):
        for p2, w2 in claims[i + 1:]:
            if p1 != p2 and overlaps(w1, w2):
                errors.append(f"{p1} and {p2} both work in '{w1}' / '{w2}'")
    return errors


def _selftest():
    import tempfile
    good = ("## Goal\ng\n## Criteria\n- [ ] c\n## Files\n- Work in: `src/a.ts`\n- Estimate: ~40 changed lines across 1 file\n"
            "## Interfaces\n- Uses: none\n- Provides: none\n## Checks\n- `x`\n## Constraints\n- k\n## Context\nq\n")
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
        assert check([a] * 10) == [], "tdd takes up to 10 tasks"
        assert any("a run needs" in e for e in check([a] * 11)), "tdd stops at 10"
        assert any("a run needs 2 to 5" in e for e in check([a] * 6, parallel=True)), "parallel stops at 5"
        b.write_text(good.replace("- [ ] c\n", "- [ ] c\n" * 8).replace("src/a.ts", "src/b.ts"))
        assert any("8 criteria" in e for e in check([a, b])), check([a, b])
        r1, r2 = Path(d) / "r1.md", Path(d) / "r2.md"
        r1.write_text(good.replace("- Work in: `src/a.ts`\n- Estimate: ~40 changed lines across 1 file", "- Work in: read-only").replace("- `x`", "- none"))
        r2.write_text(r1.read_text())
        assert check([r1]) == [], check([r1])
        b.write_text(good.replace("- Estimate: ~40 changed lines across 1 file\n", ""))
        assert any("Estimate" in e for e in check([b])), check([b])
        b.write_text(good.replace("- Uses: none\n", ""))
        assert any("'- Uses:'" in e for e in check([b])), check([b])
        run = Path(d) / "run"
        run.mkdir()
        f = "`f(x: int): int` in `src/a.ts`"
        t1, t2 = run / "1-make.md", run / "2-use.md"
        t1.write_text(good.replace("- Provides: none", f"- Provides: {f}"))
        t2.write_text(good.replace("src/a.ts", "src/b.ts").replace("- Uses: none", f"- Uses: task 1: {f}"))
        assert check([t1, t2]) == [], check([t1, t2])
        assert check([t2]) == [], "a fix brief finds its dependency beside it"
        assert any("can't use" in e for e in check([t1, t2], parallel=True)), "parallel tasks are independent"
        t2.write_text(good.replace("src/a.ts", "src/b.ts").replace("- Uses: none", "- Uses: task 1: `f(x: str)`"))
        assert any("not in task 1's Provides" in e for e in check([t1, t2])), check([t1, t2])
        t1.write_text(good.replace("- Uses: none", "- Uses: task 2: `g()`"))
        assert any("does not run before" in e for e in check([t1])), check([t1])
        t1.write_text(good.replace("- Uses: none", "- Uses: task 9: `g()`"))
        assert any("no brief 9-" in e for e in check([t1])), check([t1])


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
