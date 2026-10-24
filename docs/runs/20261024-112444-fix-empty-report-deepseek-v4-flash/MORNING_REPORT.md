# Morning report: fix-empty-report

_2026-10-24 11:25 · tallyho_

**READY FOR REVIEW** · hidden check PASS · tests green · 2 files changed (+5 -1) · $0.0026 · 16s of a 10m 00s budget

## The chore

> `tally report` crashes with a traceback on a fresh install, because the ledger is empty
> (see the TODO in `tally/report.py`). The same happens when `--month` matches no entries. In both cases it should
> print `No entries yet.` and exit 0. Add a regression test.

## Night at a glance

| | |
|---|---|
| Chore | `fix-empty-report` |
| Branch | `sloth/fix-empty-report/20261024-112444-deepseek-v4-flash` (from `main` @ `d5bfc0f`) |
| Agent | Backboard R-CLI 3.0.4 (built from source @ 51bee17), headless (`--print --timer 600`) |
| Model | `deepseek-ai/DeepSeek-V4-Flash-0731` ($0.14 in, cached $0.010, $0.28 out per 1M tokens) |
| Stopped by | agent finished (exit 0); hard stop at 12m 00s, cap $0.25 |
| Model calls | 12 |
| Tokens | 97,875 in (89,088 cached) · 1,790 out |
| Cost | $0.0026 |
| Tests before | pass: Ran 12 tests in 0.009s · OK |
| Tests after | pass: Ran 13 tests in 0.008s · OK |
| Hidden acceptance check | PASS |

## What changed

```
 tally/report.py      | 3 ++-
 tests/test_report.py | 3 +++
 2 files changed, 5 insertions(+), 1 deletion(-)
```

## What the agent says it did

> Done. Both cases fixed and regression-tested.
>
> **Change:** In `tally/report.py`, `render()` now returns `"No entries yet."` for an empty result set, guarding both a fresh install (empty ledger) and a `--month` that matches nothing. This prevents the `division by zero` crash and the `max()` on an empty sequence.
>
> **Test:** Added `test_render_empty_ledger` in `tests/test_report.py`, covering both `render([])` and a non-matching month filter.
>
> **Verification:** `python3 -m unittest discover -s tests` → 13 tests, all OK (the only output is a pre-existing `utcnow()` DeprecationWarning unrelated to this change). Nothing committed; diff ready for review.

## What it ran

- `python3 -m unittest discover -s tests`

Tool calls: read 7, edit 4, glob 1, grep 1, execute 1. 1 of them failed.

## Your move

```sh
git diff main...sloth/fix-empty-report/20261024-112444-deepseek-v4-flash      # read it
git merge --no-ff sloth/fix-empty-report/20261024-112444-deepseek-v4-flash      # keep it
git branch -D sloth/fix-empty-report/20261024-112444-deepseek-v4-flash          # or bin it
```

Nothing was merged or pushed. The sloth only works on its own branch.

Full agent session: [TRANSCRIPT.md](TRANSCRIPT.md) (readable) · `events.jsonl` (raw R-CLI JSON events) · `diff.patch` · `run.json`.
