"""Git plumbing: a private throwaway clone per night, on a sloth/ branch. Never touches main.

The agent works in its own clone, not a `git worktree` of your repo. The clone
holds only the history of the base commit, has no remote, and shares no refs
with your repo, so the agent cannot see your other branches (including earlier
sloth attempts at the same chore) or move any of your refs. When the night is
over, the harness fetches the one sloth branch back into your repo.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

SLOTH_AUTHOR = ("nightshift-sloth", "nightshift-sloth@localhost")


def git(repo: Path, *args: str, check: bool = True) -> str:
    res = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {res.stderr.strip()}")
    return res.stdout


def head_branch(repo: Path) -> str:
    return git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()


def rev(repo: Path, ref: str) -> str:
    return git(repo, "rev-parse", ref).strip()


def sloth_branches(repo: Path) -> list[str]:
    out = git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/sloth/")
    return [line.strip() for line in out.splitlines() if line.strip()]


def is_clean(repo: Path) -> bool:
    return git(repo, "status", "--porcelain").strip() == ""


def exclude_backboard_dir(repo: Path) -> None:
    """Keep R-CLI's session folder out of the working copy's status and commits."""
    common = Path(git(repo, "rev-parse", "--git-common-dir").strip())
    if not common.is_absolute():
        common = (repo / common).resolve()
    exclude = common / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude.read_text() if exclude.exists() else ""
    if ".backboard/" not in existing.splitlines():
        with exclude.open("a") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            fh.write(".backboard/\n")


def add_workspace(repo: Path, workdir: Path, branch: str, base_sha: str) -> str:
    """Make a private clone of `base_sha`'s history only, checked out on a new sloth branch."""
    workdir.mkdir(parents=True, exist_ok=False)
    git(workdir, "init", "-q")
    # Fetch exactly the base commit (and its ancestors). No other refs, no tags, no remote.
    git(workdir, "fetch", "-q", "--no-tags", "--no-write-fetch-head", str(repo.resolve()), base_sha)
    git(workdir, "checkout", "-q", "-b", branch, base_sha)
    exclude_backboard_dir(workdir)
    return rev(workdir, "HEAD")


def bring_back(repo: Path, workdir: Path, branch: str) -> None:
    """Fetch the finished sloth branch from the private clone into the user's repo."""
    git(repo, "fetch", "-q", "--no-tags", "--no-write-fetch-head", str(workdir.resolve()), f"refs/heads/{branch}:refs/heads/{branch}")


def commit_all(worktree: Path, message: str) -> str | None:
    """Commit whatever the agent left, as nightshift-sloth, on the sloth branch only."""
    git(worktree, "add", "-A")
    if subprocess.run(["git", "-C", str(worktree), "diff", "--cached", "--quiet"]).returncode == 0:
        return None  # nothing staged: the agent changed nothing
    name, email = SLOTH_AUTHOR
    git(
        worktree,
        "-c", f"user.name={name}",
        "-c", f"user.email={email}",
        "-c", "commit.gpgsign=false",
        "commit", "-q", "--no-verify", "-m", message,
    )
    return rev(worktree, "HEAD")


def diff_stat(worktree: Path, base: str) -> str:
    return git(worktree, "diff", "--stat", f"{base}..HEAD").rstrip()


def diff_patch(worktree: Path, base: str) -> str:
    return git(worktree, "diff", f"{base}..HEAD")


def numstat(worktree: Path, base: str) -> tuple[int, int, int]:
    files = added = removed = 0
    for line in git(worktree, "diff", "--numstat", f"{base}..HEAD").splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            files += 1
            added += int(parts[0]) if parts[0].isdigit() else 0
            removed += int(parts[1]) if parts[1].isdigit() else 0
    return files, added, removed


def remove_workspace(workdir: Path) -> None:
    shutil.rmtree(workdir, ignore_errors=True)
