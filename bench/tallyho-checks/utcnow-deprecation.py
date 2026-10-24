import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import WT, check, finish, no_traceback, suite, tally, tmpdir  # noqa: E402

src = "".join(p.read_text() for p in (WT / "tally").glob("*.py"))
check("utcnow" not in src, "no datetime.utcnow() left in tally/")

strict = ("-W", "error::DeprecationWarning")
d = tmpdir()
fresh = d / "fresh.json"
r = tally("add", "3.50", "coffee", ledger_file=fresh, pyflags=strict)
check(r.returncode == 0 and no_traceback(r), "`tally add` runs with DeprecationWarning turned into an error")
try:
    when = datetime.fromisoformat(json.loads(fresh.read_text())[0]["when"])
    check(when.tzinfo is not None and when.utcoffset().total_seconds() == 0, "new entries are stored as timezone-aware UTC")
except Exception as exc:  # noqa: BLE001
    check(False, f"new entry timestamp readable ({exc})")

mixed = d / "mixed.json"
mixed.write_text(json.dumps([
    {"when": "2026-09-01T08:15:00", "amount": "4.50", "category": "coffee", "note": ""},
    {"when": "2026-10-02T12:00:00", "amount": "1200.00", "category": "rent", "note": "october"},
]))
r = tally("add", "3.50", "coffee", ledger_file=mixed)
check(r.returncode == 0 and no_traceback(r), "`tally add` appends to an old ledger with naive timestamps")
r = tally("add", "2.00", "snack", "--date", "2026-10-05", ledger_file=mixed)
check(r.returncode == 0 and no_traceback(r), "`tally add --date` works on the mixed ledger")
for args in (("list",), ("list", "-n", "2"), ("report",), ("report", "--month", "2026-10"), ("export",)):
    r = tally(*args, ledger_file=mixed)
    check(r.returncode == 0 and no_traceback(r), f"`tally {' '.join(args)}` works on a ledger mixing old and new entries")
r = tally("report", ledger_file=mixed)
check("4 entries" in r.stdout, "all-time report counts all 4 mixed entries")

r = suite(pyflags=strict)
check(r.returncode == 0, "the repo's test suite passes with DeprecationWarning as an error")
finish()
