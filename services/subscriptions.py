"""Recurring-charge detector: find monthly subscriptions in transaction history.

A merchant counts as a recurring charge when it appears 3+ times with
median billing intervals of 28-32 days and charge amounts that stay
within 15% of the median. Confidence rises with tighter interval and
amount consistency.
"""
from __future__ import annotations

import re
from datetime import date
from statistics import median, pstdev

from .ingest import Transaction

MIN_OCCURRENCES = 3
MIN_INTERVAL_DAYS = 28
MAX_INTERVAL_DAYS = 32
AMOUNT_TOLERANCE = 0.15  # +/- 15% around the median charge

_NOISE = re.compile(r"[\d#*]+")  # confirmation numbers, card suffixes, etc.
_PUNCT = re.compile(r"[^\w\s&+.\-]")


def normalize_merchant(description: str) -> str:
    """Reduce a raw description to a stable merchant key."""
    text = description.lower()
    text = _PUNCT.sub(" ", text)
    text = _NOISE.sub(" ", text)
    return " ".join(text.split())


def _intervals(dates: list[date]) -> list[int]:
    return [(b - a).days for a, b in zip(dates, dates[1:])]


def detect_subscriptions(transactions: list[Transaction]) -> list[dict]:
    """Detect recurring monthly charges among outflow transactions."""
    groups: dict[str, list[Transaction]] = {}
    for txn in transactions:
        if txn.amount >= 0:
            continue  # only outflows can be subscriptions
        groups.setdefault(normalize_merchant(txn.description), []).append(txn)

    found: list[dict] = []
    for merchant, txns in groups.items():
        if len(txns) < MIN_OCCURRENCES:
            continue
        txns = sorted(txns, key=lambda t: t.date)
        dates = [t.date for t in txns]
        gaps = _intervals(dates)
        if not gaps:
            continue
        med_gap = median(gaps)
        if not (MIN_INTERVAL_DAYS <= med_gap <= MAX_INTERVAL_DAYS):
            continue
        amounts = sorted(abs(t.amount) for t in txns)
        med_amount = median(amounts)
        if med_amount <= 0:
            continue
        if any(abs(a - med_amount) / med_amount > AMOUNT_TOLERANCE for a in amounts):
            continue

        gap_spread = pstdev(gaps) if len(gaps) > 1 else 0.0
        amt_spread = pstdev(amounts) / med_amount if len(amounts) > 1 else 0.0
        confidence = max(
            0.0,
            min(
                1.0,
                0.55
                + 0.30 * max(0.0, 1.0 - gap_spread / 6.0)
                + 0.15 * max(0.0, 1.0 - amt_spread / AMOUNT_TOLERANCE),
            ),
        )
        found.append(
            {
                "merchant": merchant,
                "display_name": max(
                    (t.description for t in txns), key=len
                ).strip().title(),
                "monthly_amount": round(med_amount, 2),
                "annualized_cost": round(med_amount * 12, 2),
                "occurrences": len(txns),
                "last_charge": dates[-1].isoformat(),
                "median_interval_days": round(med_gap, 1),
                "confidence": round(confidence, 2),
            }
        )
    found.sort(key=lambda s: s["annualized_cost"], reverse=True)
    return found
