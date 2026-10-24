import tempfile
import unittest
from pathlib import Path

from nightshift_sloth.ledger import BudgetExceeded, Ledger
from nightshift_sloth.pricing import Price
from nightshift_sloth.rcli import Redactor


class PriceTest(unittest.TestCase):
    def test_cached_tokens_use_cache_rate(self):
        p = Price("m", prompt=1e-6, cached_prompt=1e-7, completion=2e-6)
        # 1000 in of which 600 cached, 100 out
        self.assertAlmostEqual(p.cost(1000, 600, 100), 400e-6 + 600e-7 + 200e-6)

    def test_no_cache_discount_bills_full_price(self):
        p = Price("m", prompt=1e-6, cached_prompt=None, completion=0)
        self.assertAlmostEqual(p.cost(1000, 900, 0), 1000e-6)


class LedgerTest(unittest.TestCase):
    def test_cap_is_enforced_before_a_run(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = Ledger(Path(d) / "l.jsonl", total_cap_usd=1.00)
            ledger.append({"model": "m", "usd": 0.80})
            ledger.require(0.20)  # exactly at the cap is fine
            with self.assertRaises(BudgetExceeded):
                ledger.require(0.25)
            self.assertAlmostEqual(ledger.remaining(), 0.20)


class RedactorTest(unittest.TestCase):
    def test_key_and_paths_are_scrubbed(self):
        with tempfile.TemporaryDirectory() as d:
            wt, home, tmp = Path(d) / "wt", Path(d) / "home", Path(d) / "tmp"
            for p in (wt, home, tmp):
                p.mkdir()
            redact = Redactor("sk-secret-123", wt, home, tmp)
            text = redact(f"cd {wt}/src && echo sk-secret-123 > {home}/x")
            self.assertEqual(text, "cd $WORKTREE/src && echo [REDACTED] > $SLOTH_HOME/x")


if __name__ == "__main__":
    unittest.main()
