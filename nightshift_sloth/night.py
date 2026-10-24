"""One night, one chore: worktree -> R-CLI -> tests -> local commit -> report."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import gitops, report
from .chores import Chore
from .config import Config, ModelConfig
from .ledger import Ledger
from .pricing import Price
from .rcli import ProviderConfig, Redactor, copy_session_transcript, rmtree_quiet, run_rcli, scrubbed_env, write_project_policy, write_rcli_home

PROMPT = """You are working the night shift on this repository. Do exactly one chore, then stop.

Chore `{chore_id}`:
{chore_text}

Ground rules:
- Your time budget is {timer} seconds and it is enforced: you will be stopped, so leave the code working at every step.
- Keep the change small and focused on this chore. Do not refactor or reformat unrelated code.
- Before you finish, run the test suite with `{test_cmd}` and make sure it passes.
- Do not commit, push, create branches or change git config. A human reviews your diff in the morning.
- Do not install packages and do not use the network.
- Finish with a short plain-text summary: what you changed, how you verified it, and anything you left undone.
"""


def short(path: Path) -> str:
    """Print paths relative to the cwd or with ~ so logs and demos stay readable."""
    path = Path(path).resolve()
    for base, label in ((Path.cwd().resolve(), "."), (Path.home().resolve(), "~")):
        try:
            return f"{label}/{path.relative_to(base)}"
        except ValueError:
            continue
    return str(path)


@dataclass
class TestResult:
    ok: bool
    summary: str
    seconds: float
    tail: str

    def to_json(self) -> dict:
        return dict(self.__dict__)


def run_tests(worktree: Path, command: str, home: Path, tmp: Path, timeout: int = 300) -> TestResult:
    env = scrubbed_env(home, tmp)
    started = time.monotonic()
    try:
        res = subprocess.run(
            shlex.split(command), cwd=str(worktree), env=env, capture_output=True, text=True, timeout=timeout
        )
        out = (res.stdout + "\n" + res.stderr).strip()
        ok = res.returncode == 0
    except subprocess.TimeoutExpired:
        out, ok = f"test command timed out after {timeout}s", False
    lines = [line for line in out.splitlines() if line.strip()]
    summary_lines = [line for line in lines if line.startswith("Ran ") or line.startswith("OK") or line.startswith("FAILED")]
    summary = " · ".join(summary_lines[-2:]) if summary_lines else (lines[-1] if lines else "(no output)")
    return TestResult(ok=ok, summary=summary[:200], seconds=round(time.monotonic() - started, 1), tail="\n".join(lines[-25:]))


def run_check(check: Path, worktree: Path, home: Path, tmp: Path, timeout: int = 180) -> dict:
    """Hidden acceptance check (bench mode). Lives outside the repo; the agent never sees it."""
    env = scrubbed_env(home, tmp)
    try:
        res = subprocess.run(
            [sys.executable, "-I", str(check), str(worktree)], env=env, capture_output=True, text=True, timeout=timeout
        )
        out = (res.stdout + "\n" + res.stderr).strip()
        return {"ok": res.returncode == 0, "output": "\n".join(out.splitlines()[-30:])}
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": f"check timed out after {timeout}s"}


def verdict(stats_stopped_by: str, committed: bool, tests_after: TestResult) -> str:
    if not committed:
        return "NO CHANGE"
    if not tests_after.ok:
        return "TESTS FAILING"
    if stats_stopped_by != "agent finished":
        return "NEEDS A LOOK"
    return "READY FOR REVIEW"


def run_night(
    *,
    cfg: Config,
    repo: Path,
    chore: Chore,
    test_cmd: str,
    model: ModelConfig,
    timer: int,
    out_dir: Path,
    ledger: Ledger,
    prices: dict[str, Price],
    api_key: str,
    check: Path | None = None,
    keep_worktree: bool = False,
) -> dict:
    price = prices.get(model.id)
    if price is None:
        raise SystemExit(f"model {model.id} is not in the provider's live catalog; refusing to run unpriced")
    ledger.require(cfg.per_run_usd)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{stamp}-{chore.id}-{model.alias}"
    branch = f"sloth/{chore.id}/{stamp}-{model.alias}"
    run_dir = out_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    state = cfg.state_dir
    worktree = state / "worktrees" / run_id
    home = state / "homes" / run_id
    tmp = state / "tmp" / run_id
    home.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)

    base_ref = cfg.base or gitops.head_branch(repo)
    base_sha = gitops.rev(repo, base_ref)
    gitops.exclude_backboard_dir(repo)
    gitops.add_worktree(repo, worktree, branch, base_sha)

    print(f"[sloth] {run_id}: tests before ...", flush=True)
    tests_before = run_tests(worktree, test_cmd, home, tmp)

    write_project_policy(worktree)
    provider = ProviderConfig(
        id=cfg.provider_id,
        name=cfg.provider_name,
        base_url=cfg.base_url,
        key_env=cfg.key_env,
        models=[m.rcli_definition() for m in cfg.models],
    )
    write_rcli_home(home, provider)
    prompt = PROMPT.format(chore_id=chore.id, chore_text=chore.text, timer=timer, test_cmd=test_cmd)
    (run_dir / "prompt.txt").write_text(prompt)

    print(f"[sloth] {run_id}: R-CLI on {model.id}, timer {timer}s, cap ${cfg.per_run_usd:.2f} ...", flush=True)
    stats = run_rcli(
        binary=cfg.rcli_binary,
        worktree=worktree,
        home=home,
        tmp=tmp,
        provider=provider,
        model=model.id,
        price=price,
        prompt=prompt,
        timer=timer,
        grace=cfg.grace,
        max_usd=cfg.per_run_usd,
        api_key=api_key,
        ledger=ledger,
        run_id=run_id,
        events_path=run_dir / "events.jsonl",
        stderr_path=run_dir / "rcli.stderr.txt",
    )
    redact = Redactor(api_key, worktree, home, tmp)
    copy_session_transcript(worktree, run_dir / "transcript.jsonl", redact)
    (run_dir / "rcli.stderr.txt").write_text(redact((run_dir / "rcli.stderr.txt").read_text(errors="replace")))

    print(f"[sloth] {run_id}: agent stopped ({stats.stopped_by}, {stats.wall_seconds}s, ${stats.usd:.4f}); tests after ...", flush=True)
    tests_after = run_tests(worktree, test_cmd, home, tmp)

    commit_msg = (
        f"sloth: {chore.id} ({model.alias})\n\n{chore.text}\n\n"
        f"Agent: Backboard R-CLI headless, model {model.id}\n"
        f"Stopped by: {stats.stopped_by}; tests after: {'pass' if tests_after.ok else 'FAIL'}\n"
    )
    sha = gitops.commit_all(worktree, commit_msg)
    committed = sha is not None
    stat = gitops.diff_stat(worktree, base_sha) if committed else ""
    files, added, removed = gitops.numstat(worktree, base_sha) if committed else (0, 0, 0)
    if committed:
        (run_dir / "diff.patch").write_text(gitops.diff_patch(worktree, base_sha))

    acceptance = None
    if check is not None:
        if check.exists():
            print(f"[sloth] {run_id}: hidden acceptance check ...", flush=True)
            acceptance = run_check(check, worktree, home, tmp)
        else:
            acceptance = {"ok": False, "output": f"no check script at {check}"}

    result = {
        "run_id": run_id,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "repo": repo.name,
        "chore": {"id": chore.id, "text": chore.text},
        "branch": branch,
        "base": {"ref": base_ref, "sha": base_sha},
        "commit": sha,
        "agent": cfg.rcli_version,
        "model": {"alias": model.alias, "id": model.id, "price": price.per_million()},
        "timer": timer,
        "grace": cfg.grace,
        "per_run_cap_usd": cfg.per_run_usd,
        "stats": stats.to_json(),
        "tests_before": tests_before.to_json(),
        "tests_after": tests_after.to_json(),
        "diff": {"files": files, "added": added, "removed": removed, "stat": stat},
        "acceptance": acceptance,
        "verdict": verdict(stats.stopped_by, committed, tests_after),
        "ledger_total_usd": round(ledger.total(), 6),
    }
    (run_dir / "run.json").write_text(json.dumps(result, indent=2) + "\n")
    morning = report.render_run(result)
    (run_dir / "MORNING_REPORT.md").write_text(morning)
    (out_dir / "LATEST.md").write_text(morning)  # what you open with your coffee

    rmtree_quiet(home)
    rmtree_quiet(tmp)
    if not keep_worktree:
        gitops.remove_worktree(repo, worktree)
    print(f"[sloth] {run_id}: {result['verdict']} -> {short(run_dir / 'MORNING_REPORT.md')}", flush=True)
    return result
