# Run Format

One pipeline run lives in `<git root>/.simply/runs/<YYYY-MM-DD-HHMM>-<slug>/`. Every stage reads and writes it through `${CLAUDE_PLUGIN_ROOT}/skills/start/scripts/run_state.py`; never edit `run.md` by hand.

## Folder

| File | Written by | Holds |
| --- | --- | --- |
| `run.md` | every stage, via `run_state.py` | the fields below and a one-line log per stage |
| `design.md` | brainstorm | goal, approach, decisions, out of scope, open questions |
| `tasks/<n>-<slug>.md` | plan | one brief per task, in `${CLAUDE_PLUGIN_ROOT}/skills/plan/references/brief.md` format; `<n>` is the run order |
| `reports/<n>-<slug>.md` | tdd (inline or as a subagents worker) | per task: `## Branch` (the branch, then `Checks passed at: <short sha>`, the commit the brief's full Checks last passed on, or `none`), `## Commits`, `## Criteria` (table `criterion \| evidence`, one row per criterion), `## Assumptions`, `## Escalation` (`none` or unresolved / tried / question). Checked by `run_state.py check-report` |
| `review.md` | review | a verdict per task, then `approve` or `changes` |

## `run.md` fields

| Field | Values | Meaning |
| --- | --- | --- |
| `mode` | `auto` \| `prompt` | `prompt`: each stage sends its summary and waits for the user before handing off. `auto`: hand off straight away |
| `stage` | `brainstorm` \| `plan` \| `execute` \| `review` \| `done` \| `escalated` | the stage running now, or how the run ended |
| `loop` | `0` \| `1` \| `2` | review → plan round trips so far; at `2` a failed review escalates instead of looping |
| `execute` | `none` \| `tdd` \| `subagents` | chosen by the user at the end of the first plan; loops reuse it |
| `base` | a branch name, or `none` | the branch the user was on at `/simply:start`; every task branch is cut from `origin/<base>`, review diffs against it, and PRs target it. `none` (a run made before this field): use the default branch |
| `branch` | a branch name, or `none` | the tdd branch; in subagents mode each report's `## Branch` names its worker branch |
| `pending` | comma-separated task numbers, or `none` | tasks the execute stage must run next; plan sets it, execute clears it to `none` |
| `created` | `YYYY-MM-DD HH:MM` | when `/simply:start` made the run |
| `task` | text | the user's request, verbatim |

Read fields with `run_state.py get <run> <field>` (prints the bare value) or `run_state.py get <run> <field> <field> …` (prints one `<field>: <value>` line per field, in order). An unknown field exits non-zero with `no field '<name>'`.

## Example

```markdown
# Run: add-input-validation

- mode: prompt
- stage: review
- loop: 1
- execute: tdd
- base: main
- branch: simply/add-input-validation
- pending: 3
- created: 2026-10-21 10:04
- task: POST /users should return 400 when name is missing or email has no @

## Log
- 2026-10-21 10:04 start: mode prompt
- 2026-10-21 10:09 brainstorm: design.md written, 0 open questions
- 2026-10-21 10:15 plan: 2 tasks, user chose tdd
- 2026-10-21 10:41 review: changes (task 2 missing 400 test)
- 2026-10-21 10:43 plan: loop 1, 1 fix task
```
