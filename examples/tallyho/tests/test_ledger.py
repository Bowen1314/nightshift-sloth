import os
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from tally import ledger


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "ledger.json"

    def tearDown(self):
        self.dir.cleanup()

    def test_missing_file_is_empty(self):
        self.assertEqual(ledger.load(self.path), [])

    def test_add_then_load_roundtrip(self):
        ledger.add(Decimal("4.50"), " Coffee ", note="flat white", path=self.path)
        ledger.add(Decimal("-2.00"), "coffee", note="refund", path=self.path)
        entries = ledger.load(self.path)
        self.assertEqual([e.amount for e in entries], [Decimal("4.50"), Decimal("-2.00")])
        self.assertEqual(entries[0].category, "coffee")
        self.assertEqual(entries[0].note, "flat white")

    def test_recent_is_newest_first(self):
        for day in (1, 3, 2):
            ledger.add(Decimal("1"), "x", when=datetime(2026, 10, day, 9, 0), path=self.path)
        days = [e.when.day for e in ledger.recent(ledger.load(self.path), 2)]
        self.assertEqual(days, [3, 2])


if __name__ == "__main__":
    unittest.main()
