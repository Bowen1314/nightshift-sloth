# Morning report: fix-empty-report

_2026-10-24 11:27 · tallyho_

**NEEDS A LOOK** · hidden check PASS · tests green · 2 files changed (+31 -1) · $0.1373 · 1m 18s of a 10m 00s budget

## The chore

> `tally report` crashes with a traceback on a fresh install, because the ledger is empty
> (see the TODO in `tally/report.py`). The same happens when `--month` matches no entries. In both cases it should
> print `No entries yet.` and exit 0. Add a regression test.

## Night at a glance

| | |
|---|---|
| Chore | `fix-empty-report` |
| Branch | `sloth/fix-empty-report/20261024-112602-gpt-oss-120b` (from `main` @ `d5bfc0f`) |
| Agent | Backboard R-CLI 3.0.4 (built from source @ 51bee17), headless (`--print --timer 600`) |
| Model | `openai/gpt-oss-120b` ($0.15 in, $0.60 out per 1M tokens) |
| Stopped by | error (exit 1); hard stop at 12m 00s, cap $0.25 |
| Model calls | 92 |
| Tokens | 850,570 in (834,880 cached) · 16,136 out |
| Cost | $0.1373 |
| Tests before | pass: Ran 12 tests in 0.007s · OK |
| Tests after | pass: Ran 14 tests in 0.009s · OK |
| Hidden acceptance check | PASS |

## What changed

```
 tally/report.py            | 14 +++++++++++++-
 tests/test_report_empty.py | 18 ++++++++++++++++++
 2 files changed, 31 insertions(+), 1 deletion(-)
```

## What the agent says it did

> (the agent did not leave a summary)

## What it ran

- `python3 -m unittest discover -s tests`

Tool calls: read 73, grep 6, apply_patch 6, glob 5,  1, execute 1, glob<|channel|>commentary 1. 79 of them failed.

## Errors

- Unable to process request. Repeat the request later.

## Your move

```sh
git diff main...sloth/fix-empty-report/20261024-112602-gpt-oss-120b      # read it
git merge --no-ff sloth/fix-empty-report/20261024-112602-gpt-oss-120b      # keep it
git branch -D sloth/fix-empty-report/20261024-112602-gpt-oss-120b          # or bin it
```

Nothing was merged or pushed. The sloth only works on its own branch.

Full agent session: [TRANSCRIPT.md](TRANSCRIPT.md) (readable) · `events.jsonl` (raw R-CLI JSON events) · `diff.patch` · `run.json`.
