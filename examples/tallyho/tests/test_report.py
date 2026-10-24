import unittest
from datetime import datetime
from decimal import Decimal

from tally.ledger import Entry
from tally.report import calcualte_totals, entries_for_month, render


def entry(day, amount, category, month=10):
    return Entry(when=datetime(2026, month, day, 12, 0), amount=Decimal(amount), category=category)


ENTRIES = [
    entry(1, "4.50", "coffee"),
    entry(2, "62.10", "groceries"),
    entry(3, "3.80", "coffee"),
    entry(28, "1200.00", "rent", month=9),
]


class ReportTest(unittest.TestCase):
    def test_totals_are_sorted_biggest_first(self):
        totals = calcualte_totals(ENTRIES)
        self.assertEqual(list(totals), ["rent", "groceries", "coffee"])
        self.assertEqual(totals["coffee"], Decimal("8.30"))

    def test_month_filter(self):
        self.assertEqual(len(entries_for_month(ENTRIES, "2026-10")), 3)
        self.assertEqual(len(entries_for_month(ENTRIES, None)), 4)

    def test_render_month(self):
        text = render(ENTRIES, "2026-10")
        self.assertIn("tallyho report: 2026-10", text)
        self.assertIn("$62.10", text)
        self.assertIn("total", text)
        self.assertIn("3 entries, average $23.47", text)


if __name__ == "__main__":
    unittest.main()
