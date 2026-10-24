"""The ledger: a JSON list of entries in ~/.tallyho.json (or $TALLY_FILE).

    {"when": "2026-10-03T08:15:00", "amount": "4.50", "category": "coffee", "note": ""}
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

DEFAULT_FILE = Path.home() / ".tallyho.json"


def ledger_path() -> Path:
    return Path(os.environ.get("TALLY_FILE", DEFAULT_FILE))


@dataclass
class Entry:
    when: datetime
    amount: Decimal
    category: str
    note: str = ""

    def to_json(self) -> dict:
        return {
            "when": self.when.isoformat(timespec="seconds"),
            "amount": str(self.amount),
            "category": self.category,
            "note": self.note,
        }

    @classmethod
    def from_json(cls, data: dict) -> "Entry":
        return cls(
            when=datetime.fromisoformat(data["when"]),
            amount=Decimal(data["amount"]),
            category=data["category"],
            note=data.get("note", ""),
        )


def load(path: Path | None = None) -> list[Entry]:
    path = path or ledger_path()
    if not path.exists():
        return []
    raw = path.read_text().strip() or "[]"
    return [Entry.from_json(item) for item in json.loads(raw)]


def save(entries: list[Entry], path: Path | None = None) -> None:
    path = path or ledger_path()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps([e.to_json() for e in entries], indent=1) + "\n")
    tmp.replace(path)


def add(amount: Decimal, category: str, note: str = "", when: datetime | None = None, path: Path | None = None) -> Entry:
    entry = Entry(
        when=when or datetime.utcnow(),
        amount=amount,
        category=category.strip().lower(),
        note=note.strip(),
    )
    entries = load(path)
    entries.append(entry)
    save(entries, path)
    return entry


def recent(entries: list[Entry], limit: int = 10) -> list[Entry]:
    return sorted(entries, key=lambda e: e.when, reverse=True)[:limit]
