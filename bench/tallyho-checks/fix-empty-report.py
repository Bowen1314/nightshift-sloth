import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import check, finish, read, suite, tally, tmpdir, no_traceback, WT  # noqa: E402

d = tmpdir()

r = tally("report", ledger_file=d / "missing.json")
check(r.returncode == 0 and no_traceback(r), "report on a missing/empty ledger exits 0 without a traceback")
check("No entries yet." in r.stdout, "report on an empty ledger prints 'No entries yet.'")

(d / "empty.json").write_text("[]\n")
r = tally("report", ledger_file=d / "empty.json")
check(r.returncode == 0 and "No entries yet." in r.stdout, "report on a ledger file containing [] prints 'No entries yet.'")

lf = d / "full.json"
tally("add", "4.50", "coffee", "--date", "2026-10-01", ledger_file=lf)
r = tally("report", "--month", "2026-01", ledger_file=lf)
check(r.returncode == 0 and no_traceback(r) and "No entries yet." in r.stdout, "report --month with no matching entries prints 'No entries yet.'")

r = tally("report", "--month", "2026-10", ledger_file=lf)
check(r.returncode == 0 and "1 entries, average $4.50" in r.stdout and "No entries yet." not in r.stdout, "a non-empty report is unchanged")

tests = "".join(p.read_text() for p in (WT / "tests").glob("*.py"))
check("No entries yet" in tests, "a regression test mentions 'No entries yet'")

r = suite()
check(r.returncode == 0, "the repo's own test suite passes")
finish()
