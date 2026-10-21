#!/usr/bin/env python3
"""Create and update /simply pipeline runs (.simply/runs/<ts>-<slug>/run.md). See references/run-format.md.

usage:
  run_state.py new <git-root> <auto|prompt> "<task>"   create a run; prints its folder
  run_state.py latest <git-root>                       prints the newest run folder
  run_state.py get <run-dir> <field>                   prints the bare value
  run_state.py get <run-dir> <field> <field> ...       prints '<field>: <value>' per field, in order
  run_state.py set <run-dir> <field>=<value> ...       validated; refuses bad values
  run_state.py log <run-dir> "<stage>: <one line>"
  run_state.py check <run-dir>
  run_state.py check-report <reports/n-slug.md>
  run_state.py --selftest"""
import re
import sys
import time
from pathlib import Path

FIELDS = ["mode", "stage", "loop", "execute", "branch", "pending", "created", "task"]
REPORT_HEADINGS = ["Branch", "Commits", "Criteria", "Assumptions", "Escalation"]
ALLOWED = {
    "mode": {"auto", "prompt"},
    "stage": {"brainstorm", "plan", "execute", "review", "done", "escalated"},
    "loop": {"0", "1", "2"},
    "execute": {"none", "tdd", "subagents"},
}


def _now():
    return time.strftime("%Y-%m-%d %H:%M")


def _read(run):
    text = (Path(run) / "run.md").read_text()
    fields = dict(re.findall(r"^- (\w+): (.*)$", text.split("## Log")[0], re.M))
    return text, fields


def _write(run, fields, log):
    title = Path(run).name.split("-", 4)[-1]
    body = f"# Run: {title}\n\n" + "".join(f"- {k}: {fields[k]}\n" for k in FIELDS)
    (Path(run) / "run.md").write_text(body + "\n## Log\n" + "".join(f"{l}\n" for l in log))


def _log(text):
    return re.findall(r"^- \d{4}-\d{2}-\d{2} \d{2}:\d{2} .*$", text.split("## Log")[-1], re.M) if "## Log" in text else []


def check(run):
    errors = []
    try:
        text, f = _read(run)
    except FileNotFoundError:
        return [f"{run}/run.md not found"]
    if not text.startswith("# Run: "):
        errors.append("line 1 must be '# Run: <slug>'")
    for k in FIELDS:
        if k not in f:
            errors.append(f"missing field '- {k}: ...'")
        elif k in ALLOWED and f[k] not in ALLOWED[k]:
            errors.append(f"{k}: '{f[k]}' not one of {sorted(ALLOWED[k])}")
    if "## Log" not in text:
        errors.append("missing '## Log'")
    return errors


def check_report(path):
    """A task report (reports/<n>-<slug>.md) from tdd: the evidence review reads."""
    text = Path(path).read_text()
    errors = []
    found = re.findall(r"^## (.+?)\s*$", text, re.M)
    if found != REPORT_HEADINGS:
        errors.append(f"headings must be exactly {REPORT_HEADINGS} in order; found {found}")
    crit = text.split("## Criteria")[-1].split("## Assumptions")[0]
    rows = [l for l in crit.splitlines() if l.startswith("|") and not re.match(r"^\|\s*-", l)][1:]
    if not rows:
        errors.append("Criteria needs a table 'criterion | evidence' with one row per criterion")
    if any(len(c) < 2 or not c[1] for c in ([x.strip() for x in r.strip().strip("|").split("|")] for r in rows)):
        errors.append("every Criteria row needs evidence")
    return errors


def new(root, mode, task):
    if mode not in ALLOWED["mode"]:
        sys.exit(f"mode must be auto or prompt, got {mode}")
    slug = "-".join(re.findall(r"[a-z0-9]+", task.lower())[:4]) or "run"
    run = Path(root) / ".simply" / "runs" / f"{time.strftime('%Y-%m-%d-%H%M')}-{slug}"
    (run / "tasks").mkdir(parents=True, exist_ok=True)
    # run files must not dirty the tree, or tdd's clean-tree check fails; .git/info/exclude is local, never committed
    exclude = Path(root) / ".git" / "info" / "exclude"
    if exclude.parent.is_dir() and ".simply/runs/" not in exclude.read_text(errors="replace") if exclude.exists() else exclude.parent.is_dir():
        with exclude.open("a") as f:
            f.write("\n.simply/runs/\n")
    fields = {"mode": mode, "stage": "brainstorm", "loop": "0", "execute": "none",
              "branch": "none", "pending": "none", "created": _now(), "task": " ".join(task.split())}
    _write(run, fields, [f"- {_now()} start: mode {mode}"])
    return run


def latest(root):
    runs = sorted((Path(root) / ".simply" / "runs").glob("*/run.md"))
    return runs[-1].parent if runs else None


def get(run, names):
    f = _read(run)[1]
    missing = [n for n in names if not f.get(n)]
    if missing:
        sys.exit(f"no field '{missing[0]}'")
    # one field prints the bare value, so existing single-field callers keep working
    return f[names[0]] if len(names) == 1 else "\n".join(f"{n}: {f[n]}" for n in names)


def set_fields(run, pairs):
    text, f = _read(run)
    for pair in pairs:
        k, _, v = pair.partition("=")
        if k not in FIELDS or k in ("created", "task"):
            sys.exit(f"cannot set '{k}'")
        if k in ALLOWED and v not in ALLOWED[k]:
            sys.exit(f"{k}: '{v}' not one of {sorted(ALLOWED[k])}")
        f[k] = v
    _write(run, f, _log(text))


def add_log(run, line):
    text, f = _read(run)
    _write(run, f, _log(text) + [f"- {_now()} {line}"])


def _selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / ".git" / "info").mkdir(parents=True)
        run = new(d, "prompt", "POST /users should return 400!")
        new(d, "auto", "second run")
        assert (Path(d) / ".git/info/exclude").read_text().count(".simply/runs/") == 1, "exclude written once"
        assert run.name.endswith("post-users-should-return"), run.name
        assert check(run) == [], check(run)
        set_fields(run, ["stage=plan", "execute=tdd", "branch=build/x"])
        add_log(run, "plan: 2 tasks")
        text, f = _read(run)
        assert f["stage"] == "plan" and f["execute"] == "tdd" and len(_log(text)) == 2, text
        assert latest(d).name.endswith("second-run")
        assert get(run, ["mode"]) == "prompt", get(run, ["mode"])
        assert get(run, ["mode", "loop", "execute", "branch"]) == "mode: prompt\nloop: 0\nexecute: tdd\nbranch: build/x"
        try:
            get(run, ["mode", "nope"])
            raise AssertionError("unknown field should exit")
        except SystemExit as e:
            assert str(e) == "no field 'nope'", e
        for bad in (["loop=3"], ["mode=fast"], ["task=x"]):
            try:
                set_fields(run, bad)
                raise AssertionError(f"{bad} should be refused")
            except SystemExit:
                pass
        (run / "run.md").write_text(text.replace("- loop: 0", "- loop: 9"))
        assert any("loop" in e for e in check(run))
        assert check(Path(d) / "nope") == [f"{Path(d) / 'nope'}/run.md not found"]
        rep = Path(d) / "r.md"
        good = "## Branch\nb\n## Commits\n- abc x\n## Criteria\n| criterion | evidence |\n| --- | --- |\n| 400 on bad email | curl -> 400 |\n## Assumptions\nnone\n## Escalation\nnone\n"
        rep.write_text(good)
        assert check_report(rep) == [], check_report(rep)
        rep.write_text(good.replace("curl -> 400 |", " |"))
        assert any("evidence" in e for e in check_report(rep)), check_report(rep)
        rep.write_text(good.replace("## Escalation\nnone\n", ""))
        assert check_report(rep)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--selftest"]:
        _selftest()
        print("selftest ok")
    elif len(a) == 4 and a[0] == "new":
        print(new(a[1], a[2], a[3]))
    elif len(a) == 2 and a[0] == "latest":
        r = latest(a[1])
        print(r) if r else sys.exit("no runs in .simply/runs/")
    elif len(a) >= 3 and a[0] == "get":
        print(get(a[1], a[2:]))
    elif len(a) >= 3 and a[0] == "set":
        set_fields(a[1], a[2:])
    elif len(a) == 3 and a[0] == "log":
        add_log(a[1], a[2])
    elif len(a) == 2 and a[0] == "check-report":
        e = check_report(a[1])
        print("\n".join(e) or "ok")
        sys.exit(1 if e else 0)
    elif len(a) == 2 and a[0] == "check":
        e = check(a[1])
        print("\n".join(e) or "ok")
        sys.exit(1 if e else 0)
    else:
        sys.exit(__doc__)
