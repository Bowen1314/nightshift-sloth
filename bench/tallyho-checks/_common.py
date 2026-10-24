"""Shared helpers for the hidden acceptance checks.

Each check is run as `python -I <check>.py <worktree>` after the agent has
finished. The agent never sees these files. Exit 0 = accepted.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WT = Path(sys.argv[1]).resolve()
FAILS: list[str] = []


def check(cond: bool, msg: str) -> bool:
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)
    return bool(cond)


def finish() -> None:
    print(f"\n{'ACCEPTED' if not FAILS else f'REJECTED ({len(FAILS)} failed)'}")
    sys.exit(1 if FAILS else 0)


def env(ledger_file: Path | None = None, root: Path | None = None) -> dict:
    e = dict(os.environ)
    e["PYTHONPATH"] = str(root or WT)
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    if ledger_file is not None:
        e["TALLY_FILE"] = str(ledger_file)
    return e


def tally(*args: str, ledger_file: Path, pyflags: tuple = (), root: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *pyflags, "-m", "tally", *args],
        cwd=str(root or WT), env=env(ledger_file, root), capture_output=True, text=True, timeout=60,
    )


def py(code: str, root: Path | None = None, pyflags: tuple = ()) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *pyflags, "-c", code], cwd=str(root or WT), env=env(None, root), capture_output=True, text=True, timeout=60
    )


def suite(root: Path | None = None, pyflags: tuple = (), target: tuple = ("discover", "-s", "tests")) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *pyflags, "-m", "unittest", *target],
        cwd=str(root or WT), env=env(Path(tempfile.mkdtemp()) / "x.json", root), capture_output=True, text=True, timeout=120,
    )


def tmpdir() -> Path:
    return Path(tempfile.mkdtemp(prefix="sloth-check-"))


def copy_tree() -> Path:
    dst = tmpdir() / "wt"
    shutil.copytree(WT, dst, ignore=shutil.ignore_patterns(".git", ".backboard", "__pycache__"))
    return dst


def read(rel: str) -> str:
    p = WT / rel
    return p.read_text() if p.exists() else ""


def no_traceback(res: subprocess.CompletedProcess) -> bool:
    return "Traceback" not in (res.stderr + res.stdout)
