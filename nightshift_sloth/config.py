"""nightshift.toml: provider, models, budget. Never holds secrets."""

from __future__ import annotations

import os
import shutil
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ModelConfig:
    alias: str
    id: str
    context_limit: int = 131072
    max_output_tokens: int = 16384
    supports_thinking: bool = False

    def rcli_definition(self) -> dict:
        return {
            "id": self.id,
            "contextLimit": self.context_limit,
            "maxOutputTokens": self.max_output_tokens,
            "supportsThinking": self.supports_thinking,
            "noImageSupport": True,
        }


@dataclass
class Config:
    rcli_binary: str = "backboard"
    provider_id: str = "nebius"
    provider_name: str = "Nebius Token Factory"
    base_url: str = "https://api.tokenfactory.nebius.com/v1"
    key_env: str = "NEBIUS_API_KEY"
    total_usd: float = 3.00
    per_run_usd: float = 0.25
    timer: int = 600
    grace: int = 120
    base: str | None = None
    default_model: str | None = None
    models: list[ModelConfig] = field(default_factory=list)
    state_dir: Path = Path("~/.nightshift-sloth").expanduser()
    rcli_version: str = "unknown"

    def model(self, alias_or_id: str | None) -> ModelConfig:
        wanted = alias_or_id or self.default_model or (self.models[0].alias if self.models else None)
        for m in self.models:
            if wanted in (m.alias, m.id):
                return m
        raise SystemExit(f"model {wanted!r} is not configured in nightshift.toml")


def load(path: Path) -> Config:
    data = tomllib.loads(path.read_text())
    rcli = data.get("rcli", {})
    prov = data.get("provider", {})
    budget = data.get("budget", {})
    night = data.get("night", {})
    cfg = Config(
        rcli_binary=os.path.expanduser(os.environ.get("NIGHTSHIFT_RCLI", rcli.get("binary", "backboard"))),
        provider_id=prov.get("id", "nebius"),
        provider_name=prov.get("name", "Nebius Token Factory"),
        base_url=prov.get("base_url", "https://api.tokenfactory.nebius.com/v1"),
        key_env=prov.get("key_env", "NEBIUS_API_KEY"),
        total_usd=float(budget.get("total_usd", 3.0)),
        per_run_usd=float(budget.get("per_run_usd", 0.25)),
        timer=int(night.get("timer", 600)),
        grace=int(night.get("grace", 120)),
        base=night.get("base"),
        default_model=night.get("default_model"),
        models=[
            ModelConfig(
                alias=m["alias"],
                id=m["id"],
                context_limit=int(m.get("context_limit", 131072)),
                max_output_tokens=int(m.get("max_output_tokens", 16384)),
                supports_thinking=bool(m.get("supports_thinking", False)),
            )
            for m in data.get("models", [])
        ],
    )
    state = os.environ.get("NIGHTSHIFT_STATE") or night.get("state_dir")
    if state:
        cfg.state_dir = Path(state).expanduser()
    cfg.rcli_version = rcli_version(cfg.rcli_binary)
    return cfg


def rcli_version(binary: str) -> str:
    """`backboard --version`, plus the git commit when it is a source build."""
    try:
        out = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=30, env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent"})
        version = out.stdout.strip() or "unknown"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    resolved = shutil.which(binary) or binary
    src = Path(resolved).resolve().parent
    sha = subprocess.run(["git", "-C", str(src), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    if sha.returncode == 0 and sha.stdout.strip():
        version += f" (built from source @ {sha.stdout.strip()})"
    return version


def load_key(key_env: str, key_file: str | None) -> str:
    """Read the provider key from the environment or a dotenv-style file. Never printed."""
    if key_file:
        for line in Path(key_file).expanduser().read_text().splitlines():
            line = line.strip()
            if line.startswith(f"{key_env}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
        raise SystemExit(f"{key_env} not found in {key_file}")
    value = os.environ.get(key_env, "").strip()
    if not value:
        raise SystemExit(f"set {key_env} in your environment (or pass --key-file)")
    return value
