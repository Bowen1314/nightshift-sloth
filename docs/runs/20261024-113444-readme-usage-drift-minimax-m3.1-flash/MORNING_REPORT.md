# Morning report: readme-usage-drift

_2026-10-24 11:35 · tallyho_

**READY FOR REVIEW** · hidden check PASS · tests green · 1 file changed (+70 -4) · $0.0112 · 57s of a 10m 00s budget

## The chore

> The Usage section of `README.md` has drifted from the real CLI. It still shows a
> `--category` flag that no longer exists and never mentions `export` or most options. Rewrite the Usage section so it
> documents every subcommand and every option exactly as `python -m tally --help` and each subcommand's `--help`
> describe them. Leave the other README sections alone.

## Night at a glance

| | |
|---|---|
| Chore | `readme-usage-drift` |
| Branch | `sloth/readme-usage-drift/20261024-113444-minimax-m3.1-flash` (from `main` @ `d5bfc0f`) |
| Agent | Backboard R-CLI 3.0.4 (built from source @ 51bee17), headless (`--print --timer 600`) |
| Model | `MiniMaxAI/MiniMax-M3.1-Flash` ($0.15 in, cached $0.015, $0.60 out per 1M tokens) |
| Stopped by | agent finished (exit 0); hard stop at 12m 00s, cap $0.25 |
| Model calls | 12 |
| Tokens | 127,510 in (90,368 cached) · 7,070 out |
| Cost | $0.0112 |
| Tests before | pass: Ran 12 tests in 0.007s · OK |
| Tests after | pass: Ran 12 tests in 0.008s · OK |
| Hidden acceptance check | PASS |

## What changed

```
 README.md | 74 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++----
 1 file changed, 70 insertions(+), 4 deletions(-)
```

## What the agent says it did

> ## Completed
>
> - Rewrote only the Usage section in `README.md`.
> - Documented the top-level CLI and every subcommand (`add`, `list`, `report`, `export`) with their exact `--help` output, including all arguments and options.
> - Removed the obsolete `--category` example and left all other README sections unchanged.
>
> ## Verification
>
> - `python3 -m unittest discover -s tests` — 12 tests passed.
> - Confirmed every documented help block exactly matches the corresponding CLI output.
> - `git diff --check` passed; only `README.md` is modified.
> - No commit created; nothing left undone.

## What it ran

- `python3 -m unittest discover -s tests` ×2
- `python3 -m tally --help`
- `python3 -m tally add --help`
- `python3 -m tally list --help`
- `python3 -m tally report --help`
- `python3 -m tally export --help`
- `git status --short && git diff -- README.md`
- `git diff --check && git diff -- README.md`
- `python3 - <<'PY'
import re
import subprocess
from pathlib import Path

readme = Path("README.md").read_text()
blocks = re.findall(r"```text\n(.*?)```", readme, re.DOTALL)
commands = [
    ["python3", "-m", "tally"],
    ["python3", "-m", "tally", "add"],
    ["python3", "-m", "tally", "list"],
    [`
- `git status --short && git diff --check && git diff --stat && git diff -- README.md`
- `python3 - <<'PY'
import re
import subprocess
from pathlib import Path

readme = Path('README.md').read_text()
blocks = re.findall(r'```text\n(.*?)```', readme, re.DOTALL)
commands = [
    ['python3', '-m', 'tally'],
    ['python3', '-m', 'tally', 'add'],
    ['python3', '-m', 'tally', 'list'],
    [`
- `git status --short && git diff --check && git diff --name-only`

Tool calls: execute 13, read 5, todo_write 4, glob 1, grep 1, edit 1.

## Your move

```sh
git diff main...sloth/readme-usage-drift/20261024-113444-minimax-m3.1-flash      # read it
git merge --no-ff sloth/readme-usage-drift/20261024-113444-minimax-m3.1-flash      # keep it
git branch -D sloth/readme-usage-drift/20261024-113444-minimax-m3.1-flash          # or bin it
```

Nothing was merged or pushed. The sloth only works on its own branch.

Full agent session: [TRANSCRIPT.md](TRANSCRIPT.md) (readable) · `events.jsonl` (raw R-CLI JSON events) · `diff.patch` · `run.json`.
