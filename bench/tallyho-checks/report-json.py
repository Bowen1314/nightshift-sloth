import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import WT, check, finish, no_traceback, suite, tally, tmpdir  # noqa: E402

d = tmpdir()
lf = d / "l.json"
for args in (("4.50", "coffee", "--date", "2026-10-01"), ("62.10", "groceries", "--date", "2026-10-02"),
             ("3.80", "coffee", "--date", "2026-10-03"), ("1200", "rent", "--date", "2026-09-28")):
    tally("add", *args, ledger_file=lf)

r = tally("report", "--json", "--month", "2026-10", ledger_file=lf)
check(r.returncode == 0 and no_traceback(r), "`report --json --month 2026-10` exits 0")
try:
    data = json.loads(r.stdout)
except json.JSONDecodeError:
    data = None
check(data is not None, "`report --json` prints valid JSON (and nothing else)")
want = {"month": "2026-10", "count": 3, "total": "70.40", "by_category": {"groceries": "62.10", "coffee": "8.30"}}
check(data == want, f"month JSON matches {json.dumps(want)} (got {json.dumps(data)})")

r = tally("report", "--json", ledger_file=lf)
try:
    data = json.loads(r.stdout)
except json.JSONDecodeError:
    data = None
want = {"month": None, "count": 4, "total": "1270.40", "by_category": {"rent": "1200.00", "groceries": "62.10", "coffee": "8.30"}}
check(data == want, f"all-time JSON matches {json.dumps(want)} (got {json.dumps(data)})")

TEXT = "tallyho report: 2026-10\n\n  groceries      $62.10   88.2%\n  coffee          $8.30   11.8%\n\n  total          $70.40\n  3 entries, average $23.47\n"
r = tally("report", "--month", "2026-10", ledger_file=lf)
check(r.stdout == TEXT, "plain-text report is byte-for-byte unchanged")

tests = "".join(p.read_text() for p in (WT / "tests").glob("*.py"))
check("--json" in tests or "json" in tests.lower(), "tests cover the JSON output")
check(suite().returncode == 0, "the repo's own test suite passes")
finish()
