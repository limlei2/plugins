#!/usr/bin/env python3
"""Survey /simply pipeline runs for /simply:cleanup. Read-only: prints what cleaning would touch, never changes the repo.

usage:
  survey.py <git-root>    prints one JSON object: current_branch, dirty, runs, handoffs_taken
  survey.py --selftest
exit: 0 ok, 1 error (not a git repo, or gh missing or failing)"""
import json
import re
import subprocess
import sys
from pathlib import Path

FINISHED = {"done", "escalated"}
PR_FLAG = {"MERGED": "merged", "OPEN": "open-pr", "CLOSED": "closed-unmerged"}


def git(root, *args):
    # --no-optional-locks: git status would otherwise rewrite the index's stat cache
    r = subprocess.run(["git", "--no-optional-locks", "-C", str(root), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def gh_pr_state(root, branch):
    """Newest PR whose head is <branch>: {number, state, headRefOid}, or None."""
    try:
        r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all", "--json", "number,state,headRefOid"],
                           cwd=root, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit("gh failed: gh not found")
    if r.returncode != 0:
        sys.exit(f"gh failed: {(r.stderr.strip().splitlines() or ['exit ' + str(r.returncode)])[0]}")
    prs = json.loads(r.stdout or "[]")
    return max(prs, key=lambda p: p["number"]) if prs else None


def run_fields(run):
    text = (run / "run.md").read_text(errors="replace").split("\n## Log", 1)[0]
    return dict(re.findall(r"^- (\w+): (.*)$", text, re.M))


def report_branches(run):
    names = []
    for p in sorted((run / "reports").glob("*.md")):
        m = re.search(r"^## Branch[ \t]*\n(.+)$", p.read_text(errors="replace"), re.M)
        if m and m.group(1).strip() != "none":
            names.append(m.group(1).strip())
    return names


def default_base(root):
    head = git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    # shortcut: assumes main when origin/HEAD is unset, upgrade if a repo without origin/HEAD uses another default
    return head.split("/", 1)[1] if head else "main"


def worktrees(root):
    """(path, branch) for every linked worktree; the first block is the main checkout."""
    out = []
    for block in (git(root, "worktree", "list", "--porcelain") or "").split("\n\n")[1:]:
        path = re.search(r"^worktree (.+)$", block, re.M)
        branch = re.search(r"^branch refs/heads/(.+)$", block, re.M)
        if path and branch:
            out.append((path.group(1), branch.group(1)))
    return out


def count(root, rng):
    return int(git(root, "rev-list", "--count", rng) or 0)


def branch_info(root, name, local, remote, base, pr_lookup):
    pr = pr_lookup(root, name)
    if not local:
        unpushed = 0
    elif remote:
        unpushed = count(root, f"origin/{name}..{name}")
    elif pr and git(root, "cat-file", "-e", pr["headRefOid"]) is not None:
        unpushed = count(root, f"{pr['headRefOid']}..{name}")  # squash merges leave no shared commits with base
    else:
        unpushed = count(root, f"origin/{base}..{name}")
    flags = [PR_FLAG.get(pr["state"], "no-pr") if pr else "no-pr"] + (["unpushed"] if unpushed else [])
    return {"name": name, "local": local, "remote": remote,
            "pr": {"number": pr["number"], "state": pr["state"]} if pr else None,
            "unpushed": unpushed, "flags": flags}


def survey(root, pr_lookup=gh_pr_state):
    root = Path(root).resolve()
    if git(root, "rev-parse", "--show-toplevel") is None:
        sys.exit(f"not a git repository: {root}")
    local = set((git(root, "for-each-ref", "--format=%(refname:short)", "refs/heads") or "").split())
    remote = {r.split("/", 1)[1] for r in (git(root, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin") or "").split()
              if "/" in r and r != "origin/HEAD"}
    trees = worktrees(root)
    found = []
    for run in sorted((root / ".simply" / "runs").glob("*/run.md")):
        f = run_fields(run.parent)
        named = {b for b in [f.get("branch", "none"), *report_branches(run.parent)] if b != "none"}
        found.append((run.parent, f, re.sub(r"^\d{4}-\d{2}-\d{2}-\d{4}-", "", run.parent.name), named))
    slugs = [slug for _, _, slug, _ in found]
    runs = []
    for run, f, slug, named in found:
        base = f.get("base", "none")
        base = default_base(root) if base == "none" else base
        names = set(named)
        if slugs.count(slug) == 1:  # a shared slug makes the prefix ambiguous: trust only what each run names
            names |= {b for b in local | remote if b.startswith(slug + "/")}
        names = sorted(b for b in names if b in local or b in remote)
        branches = [branch_info(root, b, b in local, b in remote, base, pr_lookup) for b in names]
        stage = f.get("stage", "")
        state = "in-progress" if stage not in FINISHED else (
            "skip-open-pr" if any("open-pr" in b["flags"] for b in branches) else "clean")
        runs.append({"run": str(run), "slug": slug, "stage": stage, "base": base, "state": state,
                     "branches": branches,
                     "worktrees": [{"path": p, "branch": b, "dirty": bool(git(p, "status", "--porcelain"))}
                                   for p, b in trees if b in names]})
    taken = [str(p) for p in sorted((root / ".simply" / "handoffs").glob("*.md"))
             if re.search(r"^Status: taken", p.read_text(errors="replace"), re.M)]
    return {"current_branch": git(root, "branch", "--show-current") or "",
            "dirty": bool(git(root, "status", "--porcelain", "--", ".", ":!.simply")),
            "runs": runs, "handoffs_taken": taken}


def _selftest():
    import os
    import tempfile
    os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                      GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    with tempfile.TemporaryDirectory() as d:
        d = Path(d).resolve()
        sh = lambda *a: subprocess.run(["git", *a], cwd=d / "work", check=True, capture_output=True)
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(d / "origin.git")], check=True)
        subprocess.run(["git", "clone", "-q", str(d / "origin.git"), str(d / "work")], check=True, capture_output=True)
        sh("commit", "-q", "--allow-empty", "-m", "init")
        sh("push", "-q", "origin", "main")

        def branch(name, push=True, extra=0):
            sh("switch", "-q", "-c", name, "main")
            sh("commit", "-q", "--allow-empty", "-m", name)
            if push:
                sh("push", "-q", "origin", name)
            for i in range(extra):
                sh("commit", "-q", "--allow-empty", "-m", f"{name} {i}")
            sh("switch", "-q", "main")

        for name in ["demo/all", "demo/2-open", "demo/3-closed", "demo/4-nopr", "fin/all", "side/x"]:
            branch(name)
        branch("demo/5-unpushed", extra=1)
        branch("simply/demo", push=False)  # old naming, found only through a report
        sh("worktree", "add", "-q", str(d / "wt"), "demo/4-nopr")
        (d / "wt" / "edit.txt").write_text("unsaved")

        runs = d / "work" / ".simply" / "runs"
        for folder, stage, br in [("2026-01-01-0000-demo", "done", "demo/all"),
                                  ("2026-01-02-0000-fin", "escalated", "fin/all"),
                                  ("2026-01-03-0000-wip", "execute", "none")]:
            (runs / folder / "reports").mkdir(parents=True)
            (runs / folder / "run.md").write_text(f"# Run: x\n\n- mode: auto\n- stage: {stage}\n- base: main\n- branch: {br}\n\n## Log\n- 2026-01-01 00:00 start: mode auto\n")
        branch("demo/9-rerun")  # a later run reusing the slug owns this one
        (runs / "2026-01-04-0000-demo" / "reports").mkdir(parents=True)
        (runs / "2026-01-04-0000-demo" / "run.md").write_text("# Run: demo\n\n- stage: execute\n- base: main\n- branch: demo/9-rerun\n")
        for i, b in enumerate(["simply/demo", "demo/2-open", "demo/3-closed", "demo/4-nopr", "demo/5-unpushed"], 1):
            (runs / "2026-01-01-0000-demo" / "reports" / f"{i}-r.md").write_text(f"## Branch\n{b}\nChecks passed at: none\n")
        (runs / "2026-01-02-0000-fin" / "run.md").write_text((runs / "2026-01-02-0000-fin" / "run.md").read_text().replace("- branch: fin/all", "- branch: none"))
        hand = d / "work" / ".simply" / "handoffs"
        hand.mkdir()
        (hand / "a.md").write_text("# Handoff: a\n\nStatus: taken by t at 2026-01-01 00:00\n")
        (hand / "b.md").write_text("# Handoff: b\n\nStatus: open\n")

        prs = {"demo/all": "MERGED", "demo/2-open": "OPEN", "demo/3-closed": "CLOSED",
               "demo/5-unpushed": "MERGED", "fin/all": "MERGED"}
        fake = lambda root, b: {"number": 1, "state": prs[b], "headRefOid": "0" * 40} if b in prs else None
        out = json.loads(json.dumps(survey(d / "work", fake)))
        assert out["current_branch"] == "main" and out["dirty"] is False, out
        assert out["handoffs_taken"] == [str(hand / "a.md")], out["handoffs_taken"]
        demo, fin, wip, rerun = out["runs"]
        assert [b["name"] for b in rerun["branches"]] == ["demo/9-rerun"], rerun
        flags = {b["name"]: b["flags"] for b in demo["branches"]}
        assert flags == {"demo/all": ["merged"], "demo/2-open": ["open-pr"], "demo/3-closed": ["closed-unmerged"],
                         "demo/4-nopr": ["no-pr"], "demo/5-unpushed": ["merged", "unpushed"],
                         "simply/demo": ["no-pr", "unpushed"]}, flags
        assert demo["state"] == "skip-open-pr" and demo["slug"] == "demo", demo
        assert [(Path(w["path"]).name, w["branch"], w["dirty"]) for w in demo["worktrees"]] == [("wt", "demo/4-nopr", True)]
        assert fin["state"] == "clean" and [b["name"] for b in fin["branches"]] == ["fin/all"], fin
        assert wip["state"] == "in-progress" and wip["branches"] == [], wip
        assert all("side/x" not in b["name"] for r in out["runs"] for b in r["branches"]), "unrelated branch skipped"

        path = os.environ["PATH"]
        os.environ["PATH"] = ""
        try:
            gh_pr_state(d / "work", "demo/all")
            raise AssertionError("missing gh should exit")
        except SystemExit as e:
            assert str(e).startswith("gh failed:"), e
        finally:
            os.environ["PATH"] = path


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--selftest"]:
        _selftest()
        print("selftest ok")
    elif len(a) == 1:
        print(json.dumps(survey(a[0]), indent=2))
    else:
        sys.exit("usage: survey.py <git-root> | --selftest")
