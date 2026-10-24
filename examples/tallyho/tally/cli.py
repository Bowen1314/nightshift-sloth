"""Command line interface: python -m tally <command>."""

import argparse
import csv
import sys
from datetime import datetime

from . import __version__, ledger
from .money import format_amount, parse_amount
from .report import render


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tally", description="tallyho: a tiny expense ledger for your terminal")
    parser.add_argument("--version", action="version", version=f"tallyho {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="record an expense (negative amount = refund)")
    add.add_argument("amount", help='e.g. 4.50, "$4.50", 1,234.56 or -12')
    add.add_argument("category", help="e.g. coffee, groceries, rent")
    add.add_argument("--note", default="", help="free-text note")
    add.add_argument("--date", help="YYYY-MM-DD (default: now)")

    lst = sub.add_parser("list", help="show the most recent entries")
    lst.add_argument("-n", "--limit", type=int, default=10, help="how many entries (default: 10)")

    rep = sub.add_parser("report", help="totals by category")
    rep.add_argument("--month", help="only this month, YYYY-MM")

    exp = sub.add_parser("export", help="write all entries as CSV")
    exp.add_argument("-o", "--output", help="file to write (default: stdout)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "add":
        try:
            amount = parse_amount(args.amount)
        except ValueError as exc:
            print(f"tally: {exc}", file=sys.stderr)
            return 2
        when = datetime.strptime(args.date, "%Y-%m-%d") if args.date else None
        entry = ledger.add(amount, args.category, note=args.note, when=when)
        print(f"added {format_amount(entry.amount)} to {entry.category}")
        return 0

    entries = ledger.load()

    if args.command == "list":
        for e in ledger.recent(entries, args.limit):
            note = f"  ({e.note})" if e.note else ""
            print(f"{e.when:%Y-%m-%d}  {format_amount(e.amount):>10}  {e.category}{note}")
        return 0

    if args.command == "report":
        print(render(entries, args.month))
        return 0

    if args.command == "export":
        out = open(args.output, "w", newline="") if args.output else sys.stdout
        try:
            writer = csv.writer(out)
            writer.writerow(["when", "amount", "category", "note"])
            for e in sorted(entries, key=lambda e: e.when):
                writer.writerow([e.when.isoformat(timespec="seconds"), str(e.amount), e.category, e.note])
        finally:
            if args.output:
                out.close()
        return 0

    return 1
