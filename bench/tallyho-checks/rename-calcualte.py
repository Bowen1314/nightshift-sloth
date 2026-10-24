import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import WT, check, finish, py, suite  # noqa: E402

PROBE = r"""
import warnings
from datetime import datetime
from decimal import Decimal
from tally.ledger import Entry
import tally.report as rep
E = [Entry(datetime(2026,10,1,12), Decimal("4.50"), "coffee"), Entry(datetime(2026,10,2,12), Decimal("62.10"), "groceries")]
new = rep.calculate_totals(E)
assert new == {"groceries": Decimal("62.10"), "coffee": Decimal("4.50")}, new
assert list(new) == ["groceries", "coffee"]
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    old = rep.calcualte_totals(E)
assert old == new, old
assert any(issubclass(w.category, DeprecationWarning) for w in caught), [str(w.message) for w in caught]
with warnings.catch_warnings():
    warnings.simplefilter("error", DeprecationWarning)
    rep.render(E)  # internal callers must use the new name
print("probe ok")
"""
r = py(PROBE)
check(r.returncode == 0 and "probe ok" in r.stdout, "calculate_totals works, the old name warns and still works, render() uses the new name"
      + ("" if r.returncode == 0 else f"\n     {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ''}"))

others = [p for p in (WT / "tally").glob("*.py") if p.name != "report.py"]
check(not any("calcualte" in p.read_text() for p in others), "no other module still calls the misspelled name")
tests = "".join(p.read_text() for p in (WT / "tests").glob("*.py"))
check("calculate_totals" in tests, "tests use the new name")
check(suite().returncode == 0, "the repo's own test suite passes")
finish()
