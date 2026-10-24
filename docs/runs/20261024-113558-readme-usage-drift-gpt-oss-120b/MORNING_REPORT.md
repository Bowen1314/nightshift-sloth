# Morning report: readme-usage-drift

_2026-10-24 11:36 · tallyho_

**NEEDS A LOOK** · hidden check PASS · tests green · 1 file changed (+20 -3) · $0.0379 · 32s of a 10m 00s budget

## The chore

> The Usage section of `README.md` has drifted from the real CLI. It still shows a
> `--category` flag that no longer exists and never mentions `export` or most options. Rewrite the Usage section so it
> documents every subcommand and every option exactly as `python -m tally --help` and each subcommand's `--help`
> describe them. Leave the other README sections alone.

## Night at a glance

| | |
|---|---|
| Chore | `readme-usage-drift` |
| Branch | `sloth/readme-usage-drift/20261024-113558-gpt-oss-120b` (from `main` @ `d5bfc0f`) |
| Agent | Backboard R-CLI 3.0.4 (built from source @ 51bee17), headless (`--print --timer 600`) |
| Model | `openai/gpt-oss-120b` ($0.15 in, $0.60 out per 1M tokens) |
| Stopped by | stuck loop (exit -15); hard stop at 12m 00s, cap $0.25 |
| Model calls | 33 |
| Tokens | 221,994 in (217,264 cached) · 7,678 out |
| Cost | $0.0379 |
| Tests before | pass: Ran 12 tests in 0.011s · OK |
| Tests after | pass: Ran 12 tests in 0.007s · OK |
| Hidden acceptance check | PASS |

## What changed

```
 README.md | 23 ++++++++++++++++++++---
 1 file changed, 20 insertions(+), 3 deletions(-)
```

## What the agent says it did

> (the agent did not leave a summary)

## What it ran

- `python -m tally --help` ×2
- `python3 -m tally --help` ×2
- `python3 -m tally add --help` ×2
- `python3 -m tally list --help` ×2
- `python3 -m tally report --help` ×2
- `python3 -m tally export --help`
- `python3 -m unittest discover -s tests`

Tool calls: execute 19, read 7, glob 4, apply_patch 2,  1, executes 1. 16 of them failed.

## Your move

```sh
git diff main...sloth/readme-usage-drift/20261024-113558-gpt-oss-120b      # read it
git merge --no-ff sloth/readme-usage-drift/20261024-113558-gpt-oss-120b      # keep it
git branch -D sloth/readme-usage-drift/20261024-113558-gpt-oss-120b          # or bin it
```

Nothing was merged or pushed. The sloth only works on its own branch.

Full agent session: [TRANSCRIPT.md](TRANSCRIPT.md) (readable) · `events.jsonl` (raw R-CLI JSON events) · `diff.patch` · `run.json`.
