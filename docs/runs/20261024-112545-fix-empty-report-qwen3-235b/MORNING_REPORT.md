# Morning report: fix-empty-report

_2026-10-24 11:26 · tallyho_

**READY FOR REVIEW** · hidden check PASS · tests green · 2 files changed (+8 -1) · $0.0130 · 17s of a 10m 00s budget

## The chore

> `tally report` crashes with a traceback on a fresh install, because the ledger is empty
> (see the TODO in `tally/report.py`). The same happens when `--month` matches no entries. In both cases it should
> print `No entries yet.` and exit 0. Add a regression test.

## Night at a glance

| | |
|---|---|
| Chore | `fix-empty-report` |
| Branch | `sloth/fix-empty-report/20261024-112545-qwen3-235b` (from `main` @ `d5bfc0f`) |
| Agent | Backboard R-CLI 3.0.4 (built from source @ 51bee17), headless (`--print --timer 600`) |
| Model | `Qwen/Qwen3-235B-A22B-Instruct-2507` ($0.20 in, $0.60 out per 1M tokens) |
| Stopped by | agent finished (exit 0); hard stop at 12m 00s, cap $0.25 |
| Model calls | 9 |
| Tokens | 62,161 in (56,144 cached) · 1,004 out |
| Cost | $0.0130 |
| Tests before | pass: Ran 12 tests in 0.007s · OK |
| Tests after | pass: Ran 14 tests in 0.007s · OK |
| Hidden acceptance check | PASS |

## What changed

```
 tally/report.py      | 3 ++-
 tests/test_report.py | 6 ++++++
 2 files changed, 8 insertions(+), 1 deletion(-)
```

## What the agent says it did

> Fixed `tally report` to print "No entries yet." and exit cleanly when the ledger is empty or no entries match the given month. Added two regression tests in `tests/test_report.py` to verify both cases. The full test suite passes. No further work is needed.

## What it ran

- `python3 -m unittest discover -s tests`

Tool calls: todo_write 2, glob 2, read 2, grep 1, edit 1, write 1, execute 1.

## Your move

```sh
git diff main...sloth/fix-empty-report/20261024-112545-qwen3-235b      # read it
git merge --no-ff sloth/fix-empty-report/20261024-112545-qwen3-235b      # keep it
git branch -D sloth/fix-empty-report/20261024-112545-qwen3-235b          # or bin it
```

Nothing was merged or pushed. The sloth only works on its own branch.

Full agent session: [TRANSCRIPT.md](TRANSCRIPT.md) (readable) · `events.jsonl` (raw R-CLI JSON events) · `diff.patch` · `run.json`.
