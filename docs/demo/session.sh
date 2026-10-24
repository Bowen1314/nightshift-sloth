#!/bin/bash
# The terminal session behind docs/assets/demo.gif. Every command shown is the
# command that ran; nothing is mocked. Recorded with:
#
#   asciinema rec --headless --window-size 104x34 -c docs/demo/session.sh demo.cast
#   agg --idle-time-limit 2 --font-size 15 demo.cast docs/assets/demo.gif
#
# Expects: NEBIUS_API_KEY and NIGHTSHIFT_RCLI exported, ~/tallyho created with
# `nightshift-sloth demo ~/tallyho`, and nightshift-sloth's bin/ on PATH.
set -u
cd ~/tallyho || exit 1

say() { printf '\n\033[2m# %s\033[0m\n' "$*"; sleep 1.2; }
run() { printf '\033[1;32m~/tallyho $\033[0m %s\n' "$*"; sleep 0.8; eval "$@"; sleep 1.5; }

say "the chores nobody gets round to"
run "sed -n '6,9p' CHORES.md | cut -c1-100"
say "bedtime: the sloth takes the first open chore"
run "nightshift-sloth night --repo ."
say "morning: read the report"
run "sed -n '1,30p' ~/.nightshift-sloth/reports/LATEST.md | cut -c1-104"
say "main is untouched; the work sits on its own branch"
run "git log --oneline --all | cat"
sleep 2
