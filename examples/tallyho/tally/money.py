"""Money helpers. Amounts are Decimal, never float."""

from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")


def parse_amount(text: str) -> Decimal:
    """Parse a user-typed amount such as "4.50", "$4.50", "1,234.56" or "-12".

    Negative amounts are refunds. Raises ValueError for anything else.
    """
    # TODO: no tests for this at all, and it has bitten us twice already.
    cleaned = text.strip().replace(",", "")
    negative = cleaned.startswith("-")
    if negative:
        cleaned = cleaned[1:].strip()
    if cleaned.startswith("$"):
        cleaned = cleaned[1:]
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"not an amount: {text!r}") from None
    if not value.is_finite():
        raise ValueError(f"not an amount: {text!r}")
    value = value.quantize(CENT)
    return -value if negative else value


def format_amount(value: Decimal) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"
