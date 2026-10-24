"""Monthly and all-time totals by category."""

from decimal import Decimal

from .ledger import Entry
from .money import CENT, format_amount


def entries_for_month(entries: list[Entry], month: str | None) -> list[Entry]:
    """Filter to one month ("2026-10"), or keep everything when month is None."""
    if month is None:
        return list(entries)
    return [e for e in entries if e.when.strftime("%Y-%m") == month]


def calcualte_totals(entries: list[Entry]) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for entry in entries:
        totals[entry.category] = totals.get(entry.category, Decimal("0")) + entry.amount
    return dict(sorted(totals.items(), key=lambda kv: (-kv[1], kv[0])))


def render(entries: list[Entry], month: str | None = None) -> str:
    entries = sorted(entries_for_month(entries, month), key=lambda e: e.when)
    totals = calcualte_totals(entries)
    grand = sum(totals.values(), Decimal("0"))
    # TODO: blows up with a traceback on a fresh install (empty ledger).
    average = (grand / len(entries)).quantize(CENT)
    width = max(len(category) for category in totals)
    lines = [f"tallyho report: {month or 'all time'}", ""]
    for category, amount in totals.items():
        share = (amount / grand * 100) if grand else Decimal("0")
        lines.append(f"  {category:<{width}}  {format_amount(amount):>10}  {share:5.1f}%")
    lines += [
        "",
        f"  {'total':<{width}}  {format_amount(grand):>10}",
        f"  {len(entries)} entries, average {format_amount(average)}",
    ]
    return "\n".join(lines)
