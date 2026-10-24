"""Run Backboard R-CLI headless, with a hard deadline and a hard dollar cap.

R-CLI's ``--timer`` is advisory: the model is told its budget and reminded at
50/25/10 %, but nothing is cancelled. nightshift-sloth adds the hard stop:

* the process group is killed at ``timer + grace`` seconds, and
* every ``usage`` event in R-CLI's JSON stream is priced as it arrives; the
  run is killed the moment it crosses its dollar ceiling.

Each run gets a throwaway HOME (so ``~/.backboard`` holds only the provider
definition for this run) and a scrubbed environment: only PATH, HOME, TMPDIR,
locale, and the one provider key variable are passed through. Ambient keys
such as OPENAI_API_KEY, LLM_API_KEY or BACKBOARD_API_KEY never reach it.
"""

from __future__ import annotations

import collections
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from .ledger import Ledger
from .pricing import Price

# Events that are pure streaming noise; everything else is kept as evidence.
NOISY_EVENTS = {"assistant:delta", "tool:pending", "tool:start", "tool:progress", "assistant:thinking:delta"}

# A model that keeps emitting malformed tool calls is not going to recover;
# stop paying for it after this many tool errors in a row.
MAX_CONSECUTIVE_TOOL_ERRORS = 6

# Hidden from the agent: no web browsing, no desktop control at night.
EXCLUDED_TOOLS = "WebSearch,FetchUrl"

# Deny rules sit above bypass mode in R-CLI's permission engine, so they hold
# even in --permission-mode bypass. Best-effort guard rails; the real ones are
# the throwaway worktree, the isolated HOME and the hard kill.
DENY_RULES = [
    "execute(git push:*)",
    "execute(git commit:*)",
    "execute(git checkout:*)",
    "execute(git switch:*)",
    "execute(git reset:*)",
    "execute(git branch:*)",
    "execute(git worktree:*)",
    "execute(git config:*)",
    "execute(git remote:*)",
    "execute(gh:*)",
    "execute(curl:*)",
    "execute(wget:*)",
    "execute(pip install:*)",
    "execute(pip3 install:*)",
    "execute(npm install:*)",
    "execute(brew:*)",
    "execute(sudo:*)",
    "execute(env)",
    "execute(printenv:*)",
]


@dataclass
class ProviderConfig:
    id: str
    name: str
    base_url: str
    key_env: str
    models: list[dict]  # [{"id":..., "contextLimit":..., "maxOutputTokens":..., "supportsThinking":...}]


@dataclass
class RunStats:
    exit_code: int | None = None
    stopped_by: str = "agent finished"  # | "hard timeout" | "budget cap" | "stuck loop" | "error"
    wall_seconds: float = 0.0
    model_calls: int = 0
    prompt_tokens: int = 0
    cached_tokens: int = 0
    completion_tokens: int = 0
    usd: float = 0.0
    tool_calls: collections.Counter = field(default_factory=collections.Counter)
    tool_errors: int = 0
    commands: list[str] = field(default_factory=list)
    final_message: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    turn_status: str | None = None
    session_id: str | None = None

    def to_json(self) -> dict:
        d = dict(self.__dict__)
        d["tool_calls"] = dict(self.tool_calls)
        return d


class Redactor:
    """Scrub the key and local absolute paths from everything we keep as evidence."""

    def __init__(self, api_key: str, worktree: Path, home: Path, tmp: Path, state: Path | None = None):
        self.pairs: list[tuple[str, str]] = []
        if api_key:
            self.pairs.append((api_key, "[REDACTED]"))
        places = [(worktree, "$WORKTREE"), (home, "$SLOTH_HOME"), (tmp, "$TMPDIR")]
        if state is not None:
            places.append((state, "$SLOTH_STATE"))
        for path, label in places:
            for variant in {str(path), str(path.resolve())}:
                self.pairs.append((variant, label))
        self.pairs.sort(key=lambda kv: -len(kv[0]))

    def __call__(self, text: str) -> str:
        for old, new in self.pairs:
            if old in text:
                text = text.replace(old, new)
        return text


def write_rcli_home(home: Path, provider: ProviderConfig) -> None:
    """Create a fresh R-CLI user dir that knows exactly one custom provider."""
    cfg_dir = home / ".backboard"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "providers": [
            {
                "id": provider.id,
                "name": provider.name,
                "protocol": "openai-chat",
                "baseUrl": provider.base_url,
                # The key is referenced by name; R-CLI reads it from the env.
                "auth": {"type": "env", "variable": provider.key_env},
                "discoverModels": False,
                # Custom providers only report token usage when asked to.
                "extraArgs": {"stream_options": {"include_usage": True}},
                "models": provider.models,
            }
        ]
    }
    (cfg_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n")


def write_project_policy(worktree: Path) -> None:
    pol_dir = worktree / ".backboard"
    pol_dir.mkdir(parents=True, exist_ok=True)
    (pol_dir / "settings.json").write_text(json.dumps({"permissions": {"deny": DENY_RULES}}, indent=2) + "\n")


def scrubbed_env(home: Path, tmp: Path, key_env: str | None = None, key: str | None = None) -> dict[str, str]:
    path_dirs = [str(Path(sys.executable).parent), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
    seen: list[str] = []
    for d in path_dirs:
        if d not in seen and Path(d).is_dir():
            seen.append(d)
    env = {
        "HOME": str(home),
        "TMPDIR": str(tmp),
        "PATH": ":".join(seen),
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
        "TERM": "dumb",
        "NO_COLOR": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        # Keep git from finding the user's identity, credential helpers or
        # signing config: the agent should not be able to push or commit.
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
    }
    if key_env and key:
        env[key_env] = key
    return env


def run_rcli(
    *,
    binary: str,
    worktree: Path,
    home: Path,
    tmp: Path,
    provider: ProviderConfig,
    model: str,
    price: Price,
    prompt: str,
    timer: int,
    grace: int,
    max_usd: float,
    api_key: str,
    ledger: Ledger,
    run_id: str,
    events_path: Path,
    stderr_path: Path,
) -> RunStats:
    stats = RunStats()
    redact = Redactor(api_key, worktree, home, tmp)
    env = scrubbed_env(home, tmp, provider.key_env, api_key)
    argv = [
        "nice", "-n", "19",
        binary,
        "--cwd", str(worktree),
        "--model", f"{provider.id}/{model}",
        "--format", "json",
        "--permission-mode", "bypass",
        "--timer", str(timer),
        "--no-lsp",
        "--memory", "off",
        "--excluded-tools", EXCLUDED_TOOLS,
        "--print", prompt,
    ]
    events_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    budget_hit = threading.Event()
    stuck = threading.Event()
    streak = [0]  # consecutive tool errors
    with stderr_path.open("w") as err_fh:
        proc = subprocess.Popen(
            argv,
            cwd=str(worktree),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=err_fh,
            start_new_session=True,  # own process group: kill takes the agent's children too
            text=True,
            bufsize=1,
        )

        def kill_group(sig: int) -> None:
            try:
                os.killpg(proc.pid, sig)
            except ProcessLookupError:
                pass

        def reader() -> None:
            assert proc.stdout is not None
            with events_path.open("w") as ev_fh:
                for line in proc.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    line = redact(line)
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        ev_fh.write(json.dumps({"type": "raw", "line": line[:2000]}) + "\n")
                        continue
                    etype = rec.get("type")
                    payload = rec.get("payload") or {}
                    stats.session_id = stats.session_id or rec.get("session_id")
                    if etype not in NOISY_EVENTS:
                        ev_fh.write(line + "\n")
                    if etype == "usage":
                        u = payload.get("usage") or {}
                        p_tok = int(u.get("inputTokens") or 0)
                        c_tok = int(u.get("cachedTokens") or 0)
                        o_tok = int(u.get("outputTokens") or 0)
                        usd = price.cost(p_tok, c_tok, o_tok)
                        stats.model_calls += 1
                        stats.prompt_tokens += p_tok
                        stats.cached_tokens += c_tok
                        stats.completion_tokens += o_tok
                        stats.usd += usd
                        ledger.append(
                            {
                                "source": "nightshift-sloth",
                                "run_id": run_id,
                                "model": model,
                                "prompt_tokens": p_tok,
                                "cached_tokens": c_tok,
                                "completion_tokens": o_tok,
                                "usd": round(usd, 6),
                            }
                        )
                        if stats.usd >= max_usd and not budget_hit.is_set():
                            budget_hit.set()
                            kill_group(signal.SIGTERM)
                    elif etype == "tool:requested":
                        for call in payload.get("calls") or []:
                            name = call.get("name", "?")
                            stats.tool_calls[name] += 1
                            if name == "execute":
                                cmd = (call.get("input") or {}).get("command")
                                if cmd:
                                    stats.commands.append(str(cmd)[:300])
                    elif etype == "tool:error":
                        stats.tool_errors += 1
                        streak[0] += 1
                        if streak[0] >= MAX_CONSECUTIVE_TOOL_ERRORS and not stuck.is_set():
                            stuck.set()
                            kill_group(signal.SIGTERM)
                    elif etype == "tool:result":
                        streak[0] = 0
                    elif etype == "assistant:message":
                        text = payload.get("text") or ""
                        if text.strip():
                            stats.final_message = text.strip()
                    elif etype == "run:error":
                        stats.errors.append(str(payload.get("error"))[:500])
                    elif etype == "system:warning":
                        stats.warnings.append(str(payload.get("message"))[:300])
                    elif etype == "turn:end":
                        stats.turn_status = payload.get("status")

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        try:
            proc.wait(timeout=timer + grace)
        except subprocess.TimeoutExpired:
            stats.stopped_by = "hard timeout"
            kill_group(signal.SIGTERM)
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                kill_group(signal.SIGKILL)
                proc.wait()
        t.join(timeout=15)
    stats.exit_code = proc.returncode
    stats.wall_seconds = round(time.monotonic() - started, 1)
    if budget_hit.is_set():
        stats.stopped_by = "budget cap"
    elif stuck.is_set():
        stats.stopped_by = "stuck loop"
    elif stats.stopped_by == "agent finished" and (proc.returncode != 0 or stats.errors):
        stats.stopped_by = "error"
    return stats


def copy_session_transcript(worktree: Path, dest: Path, redact: "Redactor") -> Path | None:
    """Copy R-CLI's own session transcript (client.jsonl) as run evidence."""
    sessions = worktree / ".backboard" / "sessions"
    if not sessions.is_dir():
        return None
    candidates = sorted(sessions.glob("sess_*/client.jsonl"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        return None
    dest.write_text(redact(candidates[-1].read_text(errors="replace")))
    return dest


def rmtree_quiet(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
