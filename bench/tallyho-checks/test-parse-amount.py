"""Mutation check: the new tests must catch each bug the chore names."""

import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import WT, check, copy_tree, finish, read, suite  # noqa: E402

ORIGINAL_SHA = "ac1a984ede7495a4931c97cef2cc46b65c6cc5131f22ed4926f0d054332b6c58"
money = (WT / "tally" / "money.py").read_bytes()
unchanged = hashlib.sha256(money).hexdigest() == ORIGINAL_SHA
check(unchanged, "tally/money.py is unchanged (behaviour must not change)")

tests = read("tests/test_money.py")
check("parse_amount" in tests, "tests/test_money.py tests parse_amount")
check(suite().returncode == 0, "the repo's own test suite passes")

MUTANTS = {
    "thousands separators ignored": ('cleaned = text.strip().replace(",", "")', "cleaned = text.strip()"),
    "leading $ not stripped": ('    if cleaned.startswith("$"):\n        cleaned = cleaned[1:]\n', ""),
    "refund sign dropped": ("return -value if negative else value", "return value"),
    "invalid input returns 0": ('raise ValueError(f"not an amount: {text!r}") from None', 'return Decimal("0.00")'),
}
if unchanged:
    for name, (old, new) in MUTANTS.items():
        tree = copy_tree()
        path = tree / "tally" / "money.py"
        src = path.read_text()
        assert old in src, name
        path.write_text(src.replace(old, new, 1))
        killed = suite(root=tree, target=("tests.test_money",)).returncode != 0
        check(killed, f"tests catch the mutant: {name}")
finish()
