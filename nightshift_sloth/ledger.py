"""Append-only spend ledger (JSONL). One row per model call."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path


class BudgetExceeded(RuntimeError):
    pass


class Ledger:
    def __init__(self, path: Path, total_cap_usd: float):
        self.path = path
        self.total_cap_usd = total_cap_usd
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)

    def rows(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text().splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out

    def total(self) -> float:
        return sum(float(r.get("usd", 0)) for r in self.rows())

    def remaining(self) -> float:
        return self.total_cap_usd - self.total()

    def require(self, per_run_usd: float) -> None:
        """Refuse to start a run that could push the ledger past the cap."""
        spent = self.total()
        if spent + per_run_usd > self.total_cap_usd:
            raise BudgetExceeded(
                f"ledger total ${spent:.4f} + per-run ceiling ${per_run_usd:.2f} "
                f"would exceed the ${self.total_cap_usd:.2f} cap; not starting"
            )

    def append(self, row: dict) -> None:
        row = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **row}
        with self._lock, self.path.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
