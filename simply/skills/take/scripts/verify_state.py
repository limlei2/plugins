#!/usr/bin/env python3
"""Compare the repo with a /simply:give handoff's Code state. Read-only: never changes the repo.

Exit codes: 0 everything matches, 1 mismatch (table printed), 2 tree is clean and the
recorded stash must be applied first (`git stash apply --index <sha>`, then re-run)."""
import re
import subprocess
import sys
from pathlib import Path

EXCLUDE = ["--", ".", ":(exclude).simply"]


def git(*args, cwd=None):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout.rstrip("\n")


def parse(text):
    code = re.split(r"^## Code state\s*$", text, flags=re.M)[1]
    code = re.split(r"^## ", code, flags=re.M)[0]
    field = lambda k: (re.search(rf"^{k}: ?(.*)$", code, re.M) or [None, ""])[1].strip()
    dirty = code.split("Dirty files:", 1)[1]
    dirty = [l.rstrip() for l in dirty.splitlines() if l.strip()]
    if dirty == ["none"] or dirty[:1] == ["none"]:
        dirty = []
    files = re.split(r"^## Files involved\s*$", text, flags=re.M)[1]
    files = re.split(r"^## ", files, flags=re.M)[0]
    paths = re.findall(r"^- `([^`]+)`", files, re.M)
    return field("Branch"), field("Commit"), field("Stash"), dirty, paths


def verify(handoff, cwd=None):
    branch, commit, stash, dirty, paths = parse(Path(handoff).read_text())
    rows = []  # (check, expected, actual, ok, fix)
    _, cur = git("branch", "--show-current", cwd=cwd)
    rows.append(("Branch", branch, cur, cur == branch, f"git switch {branch}"))
    _, head = git("rev-parse", "HEAD", cwd=cwd)
    rows.append(("Commit", commit, head, head == commit, f"git reset --hard {commit} (destroys local commits; ask first)"))
    if stash != "none":
        _, kind = git("cat-file", "-t", stash, cwd=cwd)
        rows.append(("Stash", f"{stash[:12]} exists", kind or "missing", kind == "commit", "stash lives in another clone; ask the giver to commit and push the WIP"))
    missing = [p for p in paths if not (Path(cwd or ".") / p).exists()]
    rows.append(("Files", "all listed paths exist", "missing: " + ", ".join(missing) if missing else "all exist", not missing, "check whether these are new or deleted per the handoff"))

    _, status = git("status", "--porcelain", *EXCLUDE, cwd=cwd)
    status = [l for l in status.splitlines() if l.strip()]
    if not status and dirty and stash != "none":
        print(f"NEEDS_APPLY: tree is clean; run: git stash apply --index {stash}  then re-run this script")
        return 2 if all(r[3] for r in rows) else 1
    same = status == dirty
    if same and stash != "none":
        same = git("diff", "--quiet", stash, *EXCLUDE, cwd=cwd)[0] == 0
    rows.append(("Working tree", f"{len(dirty)} dirty files as recorded", f"{len(status)} dirty files" + ("" if same else ", contents differ"), same, "inspect `git status` and `git diff <stash>`"))

    print("| Check | Expected | Actual | OK | Fix (do not run without the user) |")
    print("| --- | --- | --- | --- | --- |")
    for name, exp, act, ok, fix in rows:
        print(f"| {name} | {exp} | {act} | {'yes' if ok else 'NO'} | {'' if ok else fix} |")
    return 0 if all(r[3] for r in rows) else 1


def _selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        run = lambda *a: subprocess.run(a, cwd=d, check=True, capture_output=True)
        run("git", "init", "-q", "-b", "main")
        run("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init")
        Path(d, "a.txt").write_text("one\n")
        run("git", "add", "a.txt")
        run("git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "a")
        Path(d, "a.txt").write_text("two\n")
        run("git", "-c", "user.email=t@t", "-c", "user.name=t", "stash", "push", "-q", "-u", *EXCLUDE)
        stash = git("rev-parse", "stash@{0}", cwd=d)[1]
        run("git", "stash", "apply", "-q", "--index", stash)
        head = git("rev-parse", "HEAD", cwd=d)[1]
        h = Path(d, ".simply/h.md")
        h.parent.mkdir()
        h.write_text(f"# Handoff: t\n\nStatus: open\n\n## Files involved\n- `a.txt`: file\n\n## Code state\n"
                     f"Branch: main\nCommit: {head}\nStash: {stash}\nDirty files:\n M a.txt\n\n## How to verify\nx\n")
        assert verify(h, d) == 0, "matching state must pass"
        Path(d, "a.txt").write_text("three\n")
        assert verify(h, d) == 1, "changed contents must fail"
        run("git", "checkout", "-q", "a.txt")
        assert verify(h, d) == 2, "clean tree with stash must ask to apply"
        run("git", "stash", "apply", "-q", "--index", stash)
        assert verify(h, d) == 0, "after apply must pass"


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            _selftest()
        print("selftest ok")
        sys.exit(0)
    if len(sys.argv) != 2:
        sys.exit("usage: verify_state.py <handoff.md> | --selftest   (run from the git root)")
    sys.exit(verify(sys.argv[1]))
