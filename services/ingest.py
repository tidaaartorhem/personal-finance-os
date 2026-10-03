"""CSV ingestion: parse bank CSV exports into canonical Transaction records.

Tolerates multiple date formats (YYYY-MM-DD, MM/DD/YYYY, DD-Mon-YY and
common variants) and amount formats ("1,234.56", "(123.45)" for debits,
leading minus). Blank or malformed rows are skipped with a warning count
instead of aborting the run.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True)
class Transaction:
    date: date
    description: str
    amount: float  # positive = money in, negative = money out


DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d-%b-%y",
    "%d-%b-%Y",
    "%Y/%m/%d",
    "%d/%m/%Y",
)

_AMOUNT_CLEAN = re.compile(r"[^\d.\-]")


def parse_date(raw: str) -> date:
    """Parse a date string against the supported formats, else ValueError."""
    text = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unrecognized date format: {raw!r}")


def parse_amount(raw: str) -> float:
    """Parse a signed amount. Parentheses mean debit, e.g. (123.45)."""
    text = raw.strip()
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    text = _AMOUNT_CLEAN.sub("", text)
    if text in ("", ".", "-"):
        raise ValueError(f"unrecognized amount: {raw!r}")
    value = float(text)
    return -value if negative else value


_HEADER_ALIASES = {
    "date": {"date", "posted", "transaction date", "posting date"},
    "description": {"description", "desc", "merchant", "details", "narrative"},
    "amount": {"amount", "amt", "value", "net"},
}


def _column_map(header: list[str]) -> dict[str, int] | None:
    """Map canonical column names to header indexes, or None if not a header."""
    lowered = [h.strip().lower() for h in header]
    mapping: dict[str, int] = {}
    for canonical, aliases in _HEADER_ALIASES.items():
        for i, cell in enumerate(lowered):
            if cell in aliases:
                mapping[canonical] = i
                break
    return mapping if len(mapping) == 3 else None


def load_csv(path: str | Path) -> tuple[list[Transaction], int, list[str]]:
    """Load transactions from a CSV file.

    Returns (transactions, skipped_count, warnings). Header rows are
    auto-detected; without a header the columns are date, description,
    amount in that order.
    """
    transactions: list[Transaction] = []
    warnings: list[str] = []
    skipped = 0
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = [r for r in csv.reader(fh) if any(c.strip() for c in r)]
    col_map: dict[str, int] | None = None
    start = 0
    if rows:
        col_map = _column_map(rows[0])
        if col_map is not None:
            start = 1
    for lineno, row in enumerate(rows[start:], start=start + 1):
        try:
            if col_map is not None:
                raw_date = row[col_map["date"]]
                raw_desc = row[col_map["description"]]
                raw_amount = row[col_map["amount"]]
            else:
                raw_date, raw_desc, raw_amount = row[0], row[1], row[2]
            transactions.append(
                Transaction(
                    date=parse_date(raw_date),
                    description=raw_desc.strip(),
                    amount=parse_amount(raw_amount),
                )
            )
        except (ValueError, IndexError) as exc:
            skipped += 1
            warnings.append(f"line {lineno}: skipped ({exc})")
    transactions.sort(key=lambda t: t.date)
    return transactions, skipped, warnings
