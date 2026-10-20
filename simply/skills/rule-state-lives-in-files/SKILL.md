---
name: rule-state-lives-in-files
description: "Apply when anything must survive this session: progress, decisions, next steps, plans. Write it to a file with a fixed format and a checker script, never only in chat."
disable-model-invocation: true
---

# State Lives in Files

Chat ends when the session does. Anything the next session, another agent, or tomorrow needs goes in a file under `.simply/`, in a format defined once, validated by a script before it is written and again before it is read.

**Why:** State kept only in chat is lost on `/clear`, compaction, or a new session, and a free-form file drifts until the reader cannot parse it.

**Do:**
- Daily state: `.simply/daily/<YYYY-MM-DD>.md`, checked by `check_log.py`.
- One task's handoff: `.simply/handoffs/<YYYY-MM-DD-HHMM>-<slug>.md`, checked by `check_handoff.py`.
- Factory briefs: `.simply/factory/<YYYY-MM-DD-HHMM>-<slug>/<task-slug>.md`, checked by `check_briefs.py`.
- Define each format once in `references/<name>-format.md` with a filled example; the writer and the reader both run the same checker.
- Write facts true beyond today to `CLAUDE.md`, not to `.simply/`.

**Not this:**
- "I'll remember to pick this up tomorrow" with no daily log.
- A handoff pasted into chat instead of written to `.simply/handoffs/`.
- A reader that parses a file without running its checker first.

**In simply:** `/simply:goodnight` writes and `/simply:goodmorning` reads the daily log; `/simply:give` writes and `/simply:take` reads handoffs; `/simply:factory` writes briefs that `/simply:build` workers execute.
