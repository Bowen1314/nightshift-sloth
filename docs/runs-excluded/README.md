# Excluded runs

Runs kept as evidence but left out of the bench numbers in [`../runs/SUMMARY.md`](../runs/SUMMARY.md).
Their spend is still in the ledger.

## `20261024-112909-utcnow-deprecation-minimax-m3.1-flash`: it read another model's homework

The first bench used `git worktree`s of the bench repo. A worktree shares refs with the repo it came
from, so the agent could see every earlier `sloth/` branch. In this run MiniMax M3.1 Flash ran
`git log --oneline --all`, found DeepSeek V4 Flash's attempt at the same chore from a few minutes
earlier, and read it with `git show` (its `git branch --all --contains` was blocked by a deny rule).
It also looked at gpt-oss-120b's commit for a different chore.

DeepSeek's attempt was wrong, and MiniMax's fix was different and right, but a bench should not
let one contestant see another's answer. No other run looked at a branch it did not own (checked by
scanning every run's shell commands and tool results for `sloth/` refs).

Since then each night works in a private clone that holds only the base commit's history, with no
remote and no refs from your repo; the harness fetches the finished branch back. MiniMax was re-run
on this chore under that setup, and that re-run is the one in the bench numbers.
