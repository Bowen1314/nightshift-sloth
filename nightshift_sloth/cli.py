"""nightshift-sloth: one chore a night, done by an open-weight model, reviewed by you over coffee."""

from __future__ import annotations

import argparse
import collections
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import chores as chores_mod
from . import gitops, report
from .config import load as load_config
from .config import load_key
from .ledger import BudgetExceeded, Ledger
from .night import run_night
from .pricing import fetch_prices

ROOT = Path(__file__).resolve().parent.parent


def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", default=str(ROOT / "nightshift.toml"), help="nightshift.toml (default: the one next to this package)")
    p.add_argument("--key-file", help="dotenv-style file holding the provider key (default: read it from the environment)")
    p.add_argument("--out", help="where morning reports go (default: <state>/reports)")
    p.add_argument("--ledger", default=os.environ.get("NIGHTSHIFT_LEDGER"), help="spend ledger JSONL (default: $NIGHTSHIFT_LEDGER or <state>/ledger.jsonl)")


def _setup(args):
    cfg = load_config(Path(args.config))
    out = Path(args.out).expanduser().resolve() if args.out else cfg.state_dir / "reports"
    ledger = Ledger(Path(args.ledger).expanduser().resolve() if args.ledger else cfg.state_dir / "ledger.jsonl", cfg.total_usd)
    return cfg, out, ledger


def cmd_night(args) -> int:
    cfg, out, ledger = _setup(args)
    repo = Path(args.repo).expanduser().resolve()
    chore_file = chores_mod.load(repo)
    if args.chore:
        chore = chore_file.get(args.chore)
    else:
        chore = chore_file.next_open(chores_mod.attempted(gitops.sloth_branches(repo)))
        if chore is None:
            print("[sloth] nothing to do: every open chore already has a sloth/ branch. Back to sleep.")
            return 0
    test_cmd = args.test or chore_file.test_command
    if not test_cmd:
        raise SystemExit("no test command: add `test: ...` to the CHORES.md front matter or pass --test")
    model = cfg.model(args.model)
    timer = args.timer or chore_file.timer or cfg.timer
    key = load_key(cfg.key_env, args.key_file)
    try:
        ledger.require(cfg.per_run_usd)
    except BudgetExceeded as exc:
        print(f"[sloth] {exc}")
        return 2
    prices = fetch_prices(cfg.base_url, key, cache_file=out / "prices.json")
    check = Path(args.checks).expanduser().resolve() / f"{chore.id}.py" if args.checks else None
    result = run_night(
        cfg=cfg, repo=repo, chore=chore, test_cmd=test_cmd, model=model, timer=timer, out_dir=out,
        ledger=ledger, prices=prices, api_key=key, check=check, keep_worktree=args.keep_worktree,
    )
    print(report.headline(result).replace("**", ""))
    return 0


def cmd_bench(args) -> int:
    cfg, out, ledger = _setup(args)
    repo = Path(args.repo).expanduser().resolve()
    chore_file = chores_mod.load(repo)
    test_cmd = args.test or chore_file.test_command
    chore_ids = [c.id for c in chore_file.chores if not c.done] if args.chores == "all" else args.chores.split(",")
    models = [cfg.model(m) for m in args.models.split(",")]
    key = load_key(cfg.key_env, args.key_file)
    prices = fetch_prices(cfg.base_url, key, cache_file=out / "prices.json")
    checks = Path(args.checks).expanduser().resolve()
    timer = args.timer or chore_file.timer or cfg.timer
    for chore_id in chore_ids:
        for model in models:
            try:
                ledger.require(cfg.per_run_usd)
            except BudgetExceeded as exc:
                print(f"[sloth] stopping bench: {exc}")
                break
            run_night(
                cfg=cfg, repo=repo, chore=chore_file.get(chore_id), test_cmd=test_cmd, model=model, timer=timer,
                out_dir=out, ledger=ledger, prices=prices, api_key=key, check=checks / f"{chore_id}.py",
            )
    _write_summary(out, ledger)
    return 0


def _write_summary(out: Path, ledger: Ledger) -> Path:
    runs = report.load_runs(out)
    path = out / "SUMMARY.md"
    path.write_text(report.render_summary(runs, ledger.total(), ledger.total_cap_usd))
    print(f"[sloth] summary -> {path}")
    return path


def cmd_summary(args) -> int:
    _, out, ledger = _setup(args)
    print(_write_summary(out, ledger).read_text())
    return 0


def cmd_ledger(args) -> int:
    cfg, _, ledger = _setup(args)
    rows = ledger.rows()
    per_model = collections.defaultdict(lambda: [0, 0, 0, 0, 0.0])
    for r in rows:
        m = per_model[r.get("model", "?")]
        m[0] += 1
        m[1] += r.get("prompt_tokens", 0)
        m[2] += r.get("cached_tokens", 0)
        m[3] += r.get("completion_tokens", 0)
        m[4] += float(r.get("usd", 0))
    print(f"{'model':<46} {'calls':>6} {'in':>11} {'cached':>11} {'out':>9} {'usd':>9}")
    for model, (n, i, c, o, usd) in sorted(per_model.items()):
        print(f"{model:<46} {n:>6} {i:>11,} {c:>11,} {o:>9,} {usd:>9.4f}")
    print(f"total ${ledger.total():.4f} of ${cfg.total_usd:.2f} cap (${ledger.remaining():.4f} left)")
    return 0


def cmd_prices(args) -> int:
    cfg, out, _ = _setup(args)
    key = load_key(cfg.key_env, args.key_file)
    prices = fetch_prices(cfg.base_url, key)
    for m in cfg.models:
        p = prices.get(m.id)
        print(f"{m.alias:<22} {m.id:<46} {p.per_million() if p else 'NOT IN CATALOG'}")
    return 0


def cmd_demo(args) -> int:
    dest = Path(args.dest).expanduser().resolve()
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"{dest} exists and is not empty")
    shutil.copytree(ROOT / "examples" / "tallyho", dest, dirs_exist_ok=True)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(dest), "GIT_CONFIG_NOSYSTEM": "1"}
    for argv in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "add", "-A"],
        ["git", "-c", "user.name=tallyho", "-c", "user.email=tallyho@localhost", "commit", "-q", "-m", "tallyho: initial import"],
    ):
        subprocess.run(argv, cwd=dest, env=env, check=True)
    print(f"[sloth] demo repo ready at {dest} (chores in {dest / 'CHORES.md'})")
    return 0


PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>dev.nightshift-sloth</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python}</string><string>-m</string><string>nightshift_sloth</string>
    <string>night</string><string>--repo</string><string>{repo}</string>
  </array>
  <key>WorkingDirectory</key><string>{root}</string>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>2</integer><key>Minute</key><integer>30</integer></dict>
  <key>StandardOutPath</key><string>{log}</string>
  <key>StandardErrorPath</key><string>{log}</string>
</dict>
</plist>"""


def cmd_schedule(args) -> int:
    repo = Path(args.repo).expanduser().resolve()
    print("# macOS: save as ~/Library/LaunchAgents/dev.nightshift-sloth.plist, then `launchctl load` it.")
    print("# Export your provider key in the agent's environment yourself; nightshift-sloth never stores it.")
    print(PLIST.format(python=sys.executable, repo=repo, root=ROOT, log=Path("~/.nightshift-sloth/night.log").expanduser()))
    print()
    print("# Linux / cron alternative (02:30 every night):")
    print(f"30 2 * * * cd {ROOT} && {sys.executable} -m nightshift_sloth night --repo {repo} >> ~/.nightshift-sloth/night.log 2>&1")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="nightshift-sloth", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("night", help="do one chore now (what the nightly schedule runs)")
    _common(p)
    p.add_argument("--repo", required=True)
    p.add_argument("--chore", help="chore id (default: first open chore without a sloth/ branch)")
    p.add_argument("--model", help="model alias or id from nightshift.toml")
    p.add_argument("--timer", type=int, help="time budget in seconds (default: CHORES.md, then nightshift.toml)")
    p.add_argument("--test", help="test command (default: CHORES.md front matter)")
    p.add_argument("--checks", help="directory of hidden acceptance checks (<chore-id>.py)")
    p.add_argument("--keep-worktree", action="store_true")
    p.set_defaults(fn=cmd_night)

    p = sub.add_parser("bench", help="run chores x models with hidden acceptance checks")
    _common(p)
    p.add_argument("--repo", required=True)
    p.add_argument("--chores", default="all")
    p.add_argument("--models", required=True, help="comma-separated aliases")
    p.add_argument("--checks", required=True)
    p.add_argument("--timer", type=int)
    p.add_argument("--test")
    p.set_defaults(fn=cmd_bench)

    for name, fn, help_ in (
        ("summary", cmd_summary, "rebuild SUMMARY.md from the report folder"),
        ("ledger", cmd_ledger, "show spend so far"),
        ("prices", cmd_prices, "show live prices for configured models"),
    ):
        p = sub.add_parser(name, help=help_)
        _common(p)
        p.set_defaults(fn=fn)

    p = sub.add_parser("demo", help="create the tallyho demo repo (a small app with real chores)")
    p.add_argument("dest")
    p.set_defaults(fn=cmd_demo)

    p = sub.add_parser("schedule", help="print a launchd plist / cron line for a nightly run")
    p.add_argument("--repo", required=True)
    p.set_defaults(fn=cmd_schedule)

    args = ap.parse_args(argv)
    return args.fn(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
