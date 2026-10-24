"""Parse CHORES.md: a markdown checklist plus a tiny front-matter block.

    ---
    test: python3 -m unittest discover -s tests
    timer: 600
    ---
    - [ ] fix-empty-report: `tally report` crashes on an empty ledger ...
          continuation lines are indented
    - [x] already-done: checked items are skipped

One chore per night: the first unchecked item that has no sloth/<id>/ branch yet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ITEM_RE = re.compile(r"^- \[( |x|X)\]\s+(?:\*\*)?`?([a-z0-9][a-z0-9-]*)`?(?:\*\*)?\s*(?::|—|-)\s*(.*)$")


@dataclass
class Chore:
    id: str
    text: str
    done: bool


@dataclass
class ChoreFile:
    settings: dict[str, str]
    chores: list[Chore]

    @property
    def test_command(self) -> str | None:
        return self.settings.get("test")

    @property
    def timer(self) -> int | None:
        value = self.settings.get("timer")
        return int(value) if value and value.isdigit() else None

    def get(self, chore_id: str) -> Chore:
        for chore in self.chores:
            if chore.id == chore_id:
                return chore
        raise KeyError(f"no chore with id {chore_id!r} in CHORES.md")

    def next_open(self, attempted_ids: set[str]) -> Chore | None:
        for chore in self.chores:
            if not chore.done and chore.id not in attempted_ids:
                return chore
        return None


def parse(text: str) -> ChoreFile:
    settings: dict[str, str] = {}
    lines = text.splitlines()
    i = 0
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            if ":" in lines[i]:
                key, value = lines[i].split(":", 1)
                settings[key.strip().lower()] = value.strip()
            i += 1
        i += 1
    chores: list[Chore] = []
    current: Chore | None = None
    for line in lines[i:]:
        m = ITEM_RE.match(line)
        if m:
            current = Chore(id=m.group(2), text=m.group(3).strip(), done=m.group(1).lower() == "x")
            chores.append(current)
        elif current is not None and line.startswith("  ") and line.strip():
            current.text += "\n" + line.strip()
        elif not line.strip():
            current = None
    return ChoreFile(settings=settings, chores=chores)


def load(repo: Path) -> ChoreFile:
    path = repo / "CHORES.md"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found: add a CHORES.md checklist to the repo")
    return parse(path.read_text())


def attempted(branches: list[str]) -> set[str]:
    """sloth/<chore-id>/<stamp>-<model> -> chore ids that already had a night."""
    ids = set()
    for b in branches:
        parts = b.split("/")
        if len(parts) >= 3 and parts[0] == "sloth":
            ids.add(parts[1])
    return ids
