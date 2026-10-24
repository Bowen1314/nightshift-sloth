import unittest
from decimal import Decimal

from tally.money import format_amount


class FormatAmountTest(unittest.TestCase):
    def test_formats_two_decimals(self):
        self.assertEqual(format_amount(Decimal("4.5")), "$4.50")

    def test_thousands_separator(self):
        self.assertEqual(format_amount(Decimal("1234.56")), "$1,234.56")

    def test_refund_is_negative(self):
        self.assertEqual(format_amount(Decimal("-12")), "-$12.00")


if __name__ == "__main__":
    unittest.main()
