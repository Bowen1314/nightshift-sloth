# Morning report: readme-usage-drift

_2026-10-24 11:34 · tallyho_

**READY FOR REVIEW** · hidden check PASS · tests green · 1 file changed (+45 -3) · $0.0022 · 15s of a 10m 00s budget

## The chore

> The Usage section of `README.md` has drifted from the real CLI. It still shows a
> `--category` flag that no longer exists and never mentions `export` or most options. Rewrite the Usage section so it
> documents every subcommand and every option exactly as `python -m tally --help` and each subcommand's `--help`
> describe them. Leave the other README sections alone.

## Night at a glance

| | |
|---|---|
| Chore | `readme-usage-drift` |
| Branch | `sloth/readme-usage-drift/20261024-113429-deepseek-v4-flash` (from `main` @ `d5bfc0f`) |
| Agent | Backboard R-CLI 3.0.4 (built from source @ 51bee17), headless (`--print --timer 600`) |
| Model | `deepseek-ai/DeepSeek-V4-Flash-0731` ($0.14 in, cached $0.010, $0.28 out per 1M tokens) |
| Stopped by | agent finished (exit 0); hard stop at 12m 00s, cap $0.25 |
| Model calls | 9 |
| Tokens | 70,483 in (62,464 cached) · 1,772 out |
| Cost | $0.0022 |
| Tests before | pass: Ran 12 tests in 0.008s · OK |
| Tests after | pass: Ran 12 tests in 0.015s · OK |
| Hidden acceptance check | PASS |

## What changed

```
 README.md | 48 +++++++++++++++++++++++++++++++++++++++++++++---
 1 file changed, 45 insertions(+), 3 deletions(-)
```

## What the agent says it did

> Tests pass (12 OK; the DeprecationWarning is pre-existing in `ledger.py:62`, untouched by this chore). Done.
>
> What I changed: rewrote the `## Usage` section in `README.md` to document all four subcommands (`add`, `list`, `report`, `export`) and every option exactly as the CLI's `--help` output describes them. Removed the stale `--category` flag (there is no such option; category is a positional arg), added `export`, and listed each option per subcommand, including `--version` and `-h/--help`. Other README sections were left alone.
>
> How verified: ran `python3 -m tally --help` and each subcommand's `--help` to capture exact usage text, matched the README prose to it, and ran `python3 -m unittest discover -s tests` (12 passed).
>
> Left undone: nothing.

## What it ran

- `cd $WORKTREE && python3 -m tally --help && echo "===ADD===" && python3 -m tally add --help && echo "===LIST===" && python3 -m tally list --help && echo "===REPORT===" && python3 -m tally report --help && echo "===EXPORT===" && python3 -m tally export --help`
- `cd $WORKTREE && python3 -m unittest discover -s tests`

Tool calls: read 5, execute 2, edit 2, glob 1.

## Your move

```sh
git diff main...sloth/readme-usage-drift/20261024-113429-deepseek-v4-flash      # read it
git merge --no-ff sloth/readme-usage-drift/20261024-113429-deepseek-v4-flash      # keep it
git branch -D sloth/readme-usage-drift/20261024-113429-deepseek-v4-flash          # or bin it
```

Nothing was merged or pushed. The sloth only works on its own branch.

Full agent session: [TRANSCRIPT.md](TRANSCRIPT.md) (readable) · `events.jsonl` (raw R-CLI JSON events) · `diff.patch` · `run.json`.
