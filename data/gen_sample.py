"""Generate data/sample-transactions.csv: SYNTHETIC sample data.

All merchants, amounts, and dates are invented for documentation and
testing purposes. Deterministic: seed 42, so the file is reproducible.
Covers Jan-Jun 2026 with lumpy freelance income, fixed monthly costs,
variable spend, and 10 recurring monthly subscriptions (plus one
quarterly charge and one annual charge, which the detector ignores).
"""
from __future__ import annotations

import csv
import random
from datetime import date
from pathlib import Path

RNG = random.Random(42)
OUT = Path(__file__).resolve().parent / "sample-transactions.csv"


def fmt(amount: float) -> str:
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):,.2f}"


def fmt_date(d: date) -> str:
    """Mix supported date formats so the parser's tolerance is exercised."""
    r = RNG.random()
    if r < 0.60:
        return d.strftime("%Y-%m-%d")
    if r < 0.85:
        return d.strftime("%m/%d/%Y")
    return d.strftime("%d-%b-%y")


def safe_day(year: int, month: int, day: int) -> int:
    return min(day, 28)


def main() -> None:
    rows: list[tuple[str, str, str]] = []

    def add(d: date, desc: str, amount: float) -> None:
        rows.append((fmt_date(d), desc, fmt(amount)))

    clients = [
        "NORTHWIND ANALYTICS", "LUMEN LABS", "BEACON RETAIL GROUP",
        "COPPERLINE STUDIOS", "FERN GULLY MARKETING", "TIDEWATER OPS",
    ]
    invoice_no = 1040
    grocery_stores = ["LOBLAWS", "NOFRILLS", "FARM BOY", "METRO", "FRESHCO"]
    restaurants = ["UBEREATS", "SKIPTHEDISHES", "STARBUCKS", "TIM HORTONS",
                   "KINTON RAMEN", "TACOS EL GORDO", "PIZZERIA LIBRETTO"]

    subscriptions = [
        ("NETFLIX.COM", 16.99, 5), ("SPOTIFY CANADA", 11.99, 12),
        ("ICLOUD+ 50GB PLAN", 3.99, 3), ("NOTION LABS", 12.50, 18),
        ("GITHUB INC", 7.00, 20), ("GOODLIFE FITNESS", 49.99, 8),
        ("ADOBE CREATIVE CLOUD", 69.99, 15), ("FIGMA INC", 20.00, 22),
        ("AWS CANADA", 38.40, 27), ("OPENAI", 28.00, 9),
    ]

    for month in range(1, 7):
        # --- fixed monthly outflows
        add(date(2026, month, 1), "INTERAC E-TRANSFER TO LANDLORD - RENT", -2450.00)
        add(date(2026, month, safe_day(2026, month, 14)), "TORONTO HYDRO",
            -round(RNG.uniform(103, 133), 2))
        add(date(2026, month, 7), "BELL INTERNET", -79.95)
        add(date(2026, month, 10), "DESJARDINS INSURANCE", -86.50)
        add(date(2026, month, 3), "WORKHAUS COWORKING", -325.00)
        add(date(2026, month, 25), "ROGERS WIRELESS", -65.00)

        # --- recurring subscriptions (monthly cadence, 3+ occurrences)
        for merchant, amount, day in subscriptions:
            jitter = RNG.choice([-1, 0, 0, 1])
            billed = amount * RNG.choice([1.0, 1.0, 1.0, 0.98, 1.02])  # within 15%
            add(date(2026, month, safe_day(2026, month, day + jitter)),
                merchant, -round(billed, 2))

        # --- lumpy freelance income: 3-4 invoices a month, varying sizes
        for _ in range(RNG.choice([3, 3, 4, 4])):
            client = RNG.choice(clients)
            invoice_no += RNG.randint(1, 3)
            amount = round(RNG.choice([2500, 3200, 4500, 5800, 7200, 9000])
                           * RNG.uniform(0.9, 1.1), 2)
            add(date(2026, month, RNG.randint(2, 27)),
                f"INTERAC E-TRANSFER FROM {client} - INVOICE {invoice_no}", amount)

        # --- variable spend
        for _ in range(RNG.randint(5, 6)):
            add(date(2026, month, RNG.randint(1, 28)),
                RNG.choice(grocery_stores), -round(RNG.uniform(25, 140), 2))
        for _ in range(RNG.randint(4, 5)):
            add(date(2026, month, RNG.randint(1, 28)),
                RNG.choice(restaurants), -round(RNG.uniform(12, 85), 2))
        for _ in range(3):
            merchant = "PRESTO RELOAD" if RNG.random() < 0.7 else "UBER TRIP"
            add(date(2026, month, RNG.randint(1, 28)), merchant,
                -round(RNG.uniform(18, 60), 2))
        for _ in range(RNG.randint(1, 2)):
            add(date(2026, month, RNG.randint(1, 28)), "AMAZON.CA",
                -round(RNG.uniform(30, 200), 2))
        add(date(2026, month, RNG.randint(1, 28)), "SHOPPERS DRUG MART",
            -round(RNG.uniform(20, 60), 2))
        if RNG.random() < 0.5:
            add(date(2026, month, RNG.randint(1, 28)), "STAPLES",
                -round(RNG.uniform(40, 120), 2))

    # --- one-off events
    add(date(2026, 3, 8), "IKEA", -1250.00)
    add(date(2026, 4, 17), "APPLE STORE", -2899.00)  # anomaly: big laptop buy
    add(date(2026, 2, 14), "UNIQLO", -180.00)
    add(date(2026, 5, 22), "PORTER AIRLINES", -486.00)
    add(date(2026, 6, 5), "HOTEL", -312.00)
    add(date(2026, 4, 3), "VISTAPRINT", -96.00)
    # quarterly charge: only 2 occurrences in the window, detector ignores it
    add(date(2026, 2, 15), "MNP LLP - TAX ADVISORY", -450.00)
    add(date(2026, 5, 15), "MNP LLP - TAX ADVISORY", -450.00)
    # annual charge: single occurrence, detector ignores it
    add(date(2026, 3, 11), "HOVER.COM DOMAIN RENEWAL", -21.98)
    # merchants with no rules: exercise the Uncategorized fallback
    add(date(2026, 2, 9), "SQ *MYSTERY MERCHANT", -45.00)
    add(date(2026, 5, 30), "POS PURCHASE 4821", -23.75)

    rows.sort(key=lambda r: r[0])  # order is cosmetic; ingest re-sorts by date
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["date", "description", "amount"])
        writer.writerows(rows)
        writer.writerow([])  # blank row: documents skip behavior
        writer.writerow(["oops", "not a date", "NaN"])  # malformed: skipped w/ warning
    print(f"wrote {len(rows)} synthetic transactions to {OUT}")


if __name__ == "__main__":
    main()
