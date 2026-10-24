# Morning report: fix-empty-report

_2026-10-24 11:25 · tallyho_

**READY FOR REVIEW** · hidden check PASS · tests green · 2 files changed (+13 -1) · $0.0083 · 44s of a 10m 00s budget

## The chore

> `tally report` crashes with a traceback on a fresh install, because the ledger is empty
> (see the TODO in `tally/report.py`). The same happens when `--month` matches no entries. In both cases it should
> print `No entries yet.` and exit 0. Add a regression test.

## Night at a glance

| | |
|---|---|
| Chore | `fix-empty-report` |
| Branch | `sloth/fix-empty-report/20261024-112501-minimax-m3.1-flash` (from `main` @ `d5bfc0f`) |
| Agent | Backboard R-CLI 3.0.4 (built from source @ 51bee17), headless (`--print --timer 600`) |
| Model | `MiniMaxAI/MiniMax-M3.1-Flash` ($0.15 in, cached $0.015, $0.60 out per 1M tokens) |
| Stopped by | agent finished (exit 0); hard stop at 12m 00s, cap $0.25 |
| Model calls | 10 |
| Tokens | 110,719 in (84,864 cached) · 5,283 out |
| Cost | $0.0083 |
| Tests before | pass: Ran 12 tests in 0.007s · OK |
| Tests after | pass: Ran 14 tests in 0.015s · OK |
| Hidden acceptance check | PASS |

## What changed

```
 tally/report.py   |  3 ++-
 tests/test_cli.py | 11 +++++++++++
 2 files changed, 13 insertions(+), 1 deletion(-)
```

## What the agent says it did

> ## Changed
>
> - `tally/report.py` now returns `No entries yet.` for an empty ledger or an unmatched `--month`.
> - `tests/test_cli.py` includes regression tests confirming the message and exit code `0` in both cases.
>
> ## Verified
>
> - `python3 -m unittest discover -s tests`
> - All 14 tests pass.

## What it ran

- `python3 -m unittest discover -s tests`
- `git diff --check && git diff -- tally/report.py tests/test_cli.py tests/test_report.py && git status --short`

Tool calls: read 6, todo_write 4, edit 4, execute 2, glob 1, grep 1.

## Your move

```sh
git diff main...sloth/fix-empty-report/20261024-112501-minimax-m3.1-flash      # read it
git merge --no-ff sloth/fix-empty-report/20261024-112501-minimax-m3.1-flash      # keep it
git branch -D sloth/fix-empty-report/20261024-112501-minimax-m3.1-flash          # or bin it
```

Nothing was merged or pushed. The sloth only works on its own branch.

Full agent session: [TRANSCRIPT.md](TRANSCRIPT.md) (readable) · `events.jsonl` (raw R-CLI JSON events) · `diff.patch` · `run.json`.
