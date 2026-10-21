---
name: rule-keep-context-lean
description: "Apply when a task needs bulk reading: many files, long logs, wide searches, many sources. Send the reading to subagents or scripts and keep only summaries and decisions in the main thread."
disable-model-invocation: true
---

# Keep Context Lean

The main thread's context is for planning, deciding, and checking. Bulk reading goes to subagents or scripts that return a short summary, never the raw payload. Read only the files the task names and what they import.

**Why:** A context full of raw logs and whole files degrades reasoning, gets compressed and loses details, and halts long runs.

**Do:**
- Read the named files and their imports; read nothing else until a gap appears.
- Route sweeps over many files or sources to an `Explore` or research agent with a cap on what it returns (for example 10 findings, file and line each).
- Filter command output before it lands: `| tail -50`, `grep`, `--json` with `-q`, never a full log dump.
- Read a long file by range (`offset`, `limit`), not whole.
- Keep a file path and line number in the thread, not the file's contents.

**Not this:**
- `cat`-ing a 3,000-line log to find one error.
- Reading the whole repo "for context" before planning.
- Pasting every worker's full report into the main thread instead of a verdict line.

**In simply:** `/simply:brainstorm` reads only the named files and their imports; `/simply:subagents` keeps one line per worker; `/simply:research` returns findings, not pages; `recent_sessions.py` in `/simply:goodnight` returns a first request and last reply, not transcripts.
