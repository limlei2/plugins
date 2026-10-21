#!/usr/bin/env python3
"""List today's other Claude Code sessions for a project: first user request and last
assistant reply of each, newest first, 5 max. Read-only.

usage: recent_sessions.py <git root> [<current session id to skip>]"""
import json
import sys
import time
from pathlib import Path

MAX_SESSIONS, MAX_CHARS = 5, 400


def text_of(msg):
    content = (msg.get("message") or {}).get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):  # tool results are lists without text blocks; they yield ""
        return " ".join(b.get("text", "") for b in content if b.get("type") == "text").strip()
    return ""


def summarize(path):
    first_user = last_assistant = ""
    for line in path.read_text(errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        t = text_of(entry)
        if entry.get("type") == "user" and t and not first_user and not t.startswith("<"):
            first_user = t
        elif entry.get("type") == "assistant" and t:
            last_assistant = t
    return first_user[:MAX_CHARS], last_assistant[:MAX_CHARS]


def sessions(root, skip="", projects=Path.home() / ".claude" / "projects"):
    slug = str(root).replace("/", "-").replace(".", "-")
    midnight = time.mktime(time.localtime()[:3] + (0, 0, 0, 0, 0, -1))
    files = [p for p in (projects / slug).glob("*.jsonl")
             if p.stat().st_mtime >= midnight and p.stem != skip]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [(p.stem, *summarize(p)) for p in files[:MAX_SESSIONS]]


def _selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d) / "-repo-x"
        proj.mkdir()
        rows = [{"type": "user", "message": {"content": "fix the login bug"}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "content": "x"}]}},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "Fixed in auth.ts"}]}}]
        (proj / "abc.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\nnot json\n")
        (proj / "cur.jsonl").write_text(json.dumps(rows[0]))
        got = sessions("/repo/x", skip="cur", projects=Path(d))
        assert got == [("abc", "fix the login bug", "Fixed in auth.ts")], got


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        _selftest()
        print("selftest ok")
        sys.exit(0)
    if not 2 <= len(sys.argv) <= 3:
        sys.exit(__doc__.strip().splitlines()[-1])
    found = sessions(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else "")
    for sid, asked, last in found:
        print(f"## session {sid}\nasked: {asked or '(none)'}\nlast reply: {last or '(none)'}\n")
    if not found:
        print("no other sessions today")
