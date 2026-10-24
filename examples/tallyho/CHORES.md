---
test: python3 -m unittest discover -s tests
timer: 600
---
# Chores

The stuff we keep meaning to do. nightshift-sloth takes the first open one each night.

- [ ] fix-empty-report: `tally report` crashes with a traceback on a fresh install, because the ledger is empty
  (see the TODO in `tally/report.py`). The same happens when `--month` matches no entries. In both cases it should
  print `No entries yet.` and exit 0. Add a regression test.
- [ ] utcnow-deprecation: `datetime.utcnow()` is deprecated since Python 3.12 and prints a DeprecationWarning on every
  `tally add`. Switch to timezone-aware UTC timestamps (`datetime.now(timezone.utc)`). Existing ledger files contain
  naive timestamps such as `2026-09-01T08:15:00`; they must keep loading, and `list`, `report` and `export` must keep
  working on a ledger that mixes old and new entries.
- [ ] test-parse-amount: `tally.money.parse_amount()` has no tests (see the TODO). Add unit tests to
  `tests/test_money.py` covering plain amounts (`4.50`), a leading `$`, thousands separators (`1,234.56`), surrounding
  whitespace, negative refunds (`-12.00`, `-$3`), and invalid input raising `ValueError`. Do not change how
  `parse_amount` behaves.
- [ ] readme-usage-drift: The Usage section of `README.md` has drifted from the real CLI. It still shows a
  `--category` flag that no longer exists and never mentions `export` or most options. Rewrite the Usage section so it
  documents every subcommand and every option exactly as `python -m tally --help` and each subcommand's `--help`
  describe them. Leave the other README sections alone.
- [ ] report-json: Add a `--json` flag to `tally report` that prints the same numbers as JSON, for scripts:
  `{"month": "2026-10" or null, "count": 3, "total": "70.40", "by_category": {"groceries": "62.10", "coffee": "8.30"}}`.
  Amounts are strings with exactly two decimals (no floats). The plain-text report stays the default and must not
  change. Add tests.
- [ ] rename-calcualte: `tally.report.calcualte_totals` is misspelled. Rename it to `calculate_totals` and update every
  caller and test, but keep `calcualte_totals` importable as a deprecated alias that emits a `DeprecationWarning`,
  because an external plugin still imports the old name.
