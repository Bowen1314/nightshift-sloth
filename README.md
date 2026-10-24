# nightshift-sloth

**One chore a night.** While you sleep, an open-weight model picks the next item off your
`CHORES.md`, does it on a throwaway branch with a strict time budget, runs your tests, and
leaves a morning report. It never merges, never pushes, never touches `main`. You read the
report over coffee and decide: keep it or bin it.

Built on [Backboard R-CLI](https://github.com/Backboard-io/Backboard-R-CLI) (MIT), the
open-source terminal coding agent, running headless against open-weight models on
[Nebius Token Factory](https://tokenfactory.nebius.com/). No Backboard account needed.

![nightshift-sloth doing one chore and leaving a morning report](docs/assets/demo.gif)

<!-- RESULTS -->

## Why

Every repo has a list of chores nobody wants: the TODO that says *"blows up on a fresh install"*,
the deprecation warning that prints on every run, the README that drifted three releases ago,
the function with no tests "because it's simple". None of them is hard. All of them lose to
whatever is more interesting today.

They are also exactly the size of task a cheap model can do well, as long as someone keeps it on a
short leash. nightshift-sloth is the leash:

- **one chore per night**, the first open item in `CHORES.md` that has no `sloth/` branch yet;
- **a time budget** given to the agent (R-CLI's `--timer`) and a **hard kill** at budget + grace;
- **a dollar cap** per run, metered live from the agent's own token-usage events;
- **a throwaway git worktree** on its own branch, `sloth/<chore>/<stamp>-<model>`;
- **your tests before and after**, and a **morning report** with the diff stat, test results,
  tokens, cost, model, and the exact commands to keep or discard the change.

Slow and steady: one small, reviewable change a day, for a fraction of a cent.

## How it works

```
CHORES.md ──► pick next open chore
                 │
                 ▼
git worktree add sloth/<chore>/<stamp>-<model>      (main is never checked out or modified)
                 │
                 ▼
tests before ──► backboard --print "<chore>" --timer 600 --format json --permission-mode bypass
                 │   │
                 │   ├─ fresh throwaway HOME: ~/.backboard/config.json knows one provider
                 │   ├─ scrubbed env: PATH, HOME, TMPDIR, locale + the one provider key
                 │   ├─ deny rules: no git push/commit/checkout, no gh, curl, installs, env dumps
                 │   ├─ no web tools (WebSearch, FetchUrl excluded)
                 │   └─ every `usage` event priced live ──► ledger.jsonl ──► kill at $ cap
                 │
                 ├─ hard kill of the whole process group at timer + grace
                 ▼
tests after ──► local commit on the sloth branch ──► (bench: hidden acceptance check)
                 │
                 ▼
MORNING_REPORT.md + run.json + diff.patch + R-CLI transcript
```

The agent is [Backboard R-CLI](https://github.com/Backboard-io/Backboard-R-CLI). nightshift-sloth
is a small Python harness (standard library only, ~900 lines) around it.

## Quick start

You need Python 3.11+, git, [ripgrep](https://github.com/BurntSushi/ripgrep) and
[Bun](https://bun.sh/) (to build R-CLI).

**1. Build R-CLI from source.** When this was written (October 2026), the released binary
(`backboard` 3.0.5 from the official installer) did not include custom model providers or
`--timer`; both are on `main`. Build the commit this project was tested with:

```sh
git clone https://github.com/Backboard-io/Backboard-R-CLI.git && cd Backboard-R-CLI
git checkout 51bee17e02344de5fffd89523ce2b73d5042f216
bun install --frozen-lockfile && bun run build      # produces ./backboard
export NIGHTSHIFT_RCLI="$PWD/backboard"
```

**2. Give it a model provider key.** Any OpenAI-compatible endpoint works; the defaults use
Nebius Token Factory. The key is read from your environment and only ever passed to the agent
process; it is never written to disk by nightshift-sloth.

```sh
export NEBIUS_API_KEY=...        # never commit this
```

**3. Try it on the demo repo**, a tiny expense tracker with six real chores:

```sh
git clone https://github.com/Bowen1314/nightshift-sloth.git && cd nightshift-sloth
bin/nightshift-sloth demo ~/tallyho
bin/nightshift-sloth night --repo ~/tallyho
cat ~/.nightshift-sloth/reports/LATEST.md
```

**4. Point it at your own repo.** Add a `CHORES.md`:

```markdown
---
test: python3 -m unittest discover -s tests
timer: 600
---
- [ ] fix-empty-report: `tally report` crashes on an empty ledger. Print "No entries yet." instead.
- [ ] readme-usage-drift: the Usage section no longer matches `--help`. Fix it.
```

Then run it nightly. `bin/nightshift-sloth schedule --repo ~/code/myapp` prints a launchd plist
(macOS) and a cron line; nightshift-sloth does not install anything for you.

## Commands

| Command | What it does |
|---|---|
| `night --repo R [--chore ID] [--model M]` | Do one chore now. Without `--chore`, takes the first open chore with no `sloth/` branch. |
| `bench --repo R --models a,b,c --checks DIR` | Every chore × every model, plus hidden acceptance checks. Writes `SUMMARY.md`. |
| `summary` | Rebuild `SUMMARY.md` from a report folder. |
| `ledger` | Spend so far, per model, against the cap. |
| `prices` | Live per-token prices for the configured models. |
| `demo DIR` | Create the tallyho demo repo. |
| `schedule --repo R` | Print a launchd plist / cron line for a nightly run. |

Common flags: `--out` (report folder), `--ledger` (spend ledger), `--key-file` (dotenv file with
the key, instead of the environment), `--config` (defaults to `nightshift.toml`).

## Configuration

`nightshift.toml` holds the provider, the models and the budget. No secrets.

```toml
[provider]
base_url = "https://api.tokenfactory.nebius.com/v1"
key_env = "NEBIUS_API_KEY"

[budget]
total_usd = 3.00     # the ledger refuses to start a run that could cross this
per_run_usd = 0.25   # a run is killed the moment its metered cost reaches this

[night]
timer = 600          # handed to R-CLI's --timer (advisory, for the model)
grace = 120          # hard kill at timer + grace (enforced by nightshift-sloth)

[[models]]
alias = "deepseek-v4-flash"
id = "deepseek-ai/DeepSeek-V4-Flash-0731"
```

Swapping models is one line. Swapping providers is two (`base_url`, `key_env`); prices are
fetched live from the provider's `/models` endpoint, so the ledger is always billed at the
current list price.

## What the sloth can and cannot do

R-CLI runs headless with `--permission-mode bypass`, because nobody is awake to approve
prompts. That is only acceptable because of what surrounds it:

- It works in a **separate git worktree** on its own branch. `main` is never checked out there.
- It gets a **throwaway HOME** and a **scrubbed environment**. Your shell's other API keys
  (`OPENAI_API_KEY`, `BACKBOARD_API_KEY`, ...) never reach it, nor does your git identity or
  credential helper (`GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`).
- R-CLI **deny rules** (which outrank bypass mode in its permission engine) block `git push`,
  `git commit`, branch switching, `gh`, `curl`, package installs and environment dumps.
- Web tools are switched off; the only network it needs is the model endpoint.
- The **process group is killed** at timer + grace, and at the per-run dollar cap.
- The harness, not the agent, makes the one local commit on the sloth branch.

It is **not a sandbox**: the agent can still run shell commands as your user inside that
worktree and could, if it went badly wrong, touch files elsewhere. Use it on repos you would
let a junior colleague work on unsupervised, ideally on a dev machine. Evidence files are
scrubbed of the key and of local absolute paths before they are written.

## Repository layout

```
nightshift_sloth/     the harness (stdlib only)
  night.py            one chore: worktree → R-CLI → tests → commit → report
  rcli.py             R-CLI runner: throwaway HOME, scrubbed env, live metering, hard kill
  chores.py           CHORES.md parser
  report.py           morning reports and the bench summary
examples/tallyho/     the demo app and its CHORES.md
bench/tallyho-checks/ hidden acceptance checks (one per chore), never shown to the agent
bench/tallyho-reference/  reference solutions the checks were validated against
docs/runs/            every bench run: MORNING_REPORT.md, run.json, diff.patch, transcripts
ledger/spend.jsonl    every model call this project made, priced
tests/                tests for the harness itself
```

## License

MIT. Backboard R-CLI is MIT-licensed by Backboard.
