"""Cash-flow engine: monthly series, safe-spend number, runway, forecast.

safe_spend = avg monthly income - avg essential spend - monthly tax set-aside
runway   = liquid cash / avg monthly burn
The 3-month forecast extrapolates average income and average spend.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date
from statistics import mean

from .ingest import Transaction

ESSENTIAL_CATEGORIES = {"Housing", "Utilities", "Insurance", "Groceries"}
FORECAST_MONTHS = 3


def month_key(d: date) -> str:
    return d.strftime("%Y-%m")


def add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    total = (year * 12 + (month - 1)) + delta
    return total // 12, total % 12 + 1


def monthly_series(transactions: list[Transaction]) -> list[dict]:
    """Per-month income, expenses, and net, oldest month first."""
    buckets: dict[str, dict] = {}
    for txn in transactions:
        key = month_key(txn.date)
        bucket = buckets.setdefault(key, {"income": 0.0, "expenses": 0.0})
        if txn.amount >= 0:
            bucket["income"] += txn.amount
        else:
            bucket["expenses"] += abs(txn.amount)
    series = []
    for key in sorted(buckets):
        income = round(buckets[key]["income"], 2)
        expenses = round(buckets[key]["expenses"], 2)
        series.append(
            {
                "month": key,
                "income": income,
                "expenses": expenses,
                "net": round(income - expenses, 2),
            }
        )
    return series


def category_totals(
    transactions: list[Transaction], category_of: dict[str, str]
) -> list[dict]:
    """Aggregate outflows by category, largest first."""
    totals: dict[str, dict] = {}
    for txn in transactions:
        if txn.amount >= 0:
            continue
        category = category_of.get(txn.description, "Uncategorized")
        entry = totals.setdefault(category, {"total": 0.0, "count": 0})
        entry["total"] += abs(txn.amount)
        entry["count"] += 1
    return [
        {
            "category": name,
            "total": round(v["total"], 2),
            "count": v["count"],
        }
        for name, v in sorted(totals.items(), key=lambda kv: kv[1]["total"], reverse=True)
    ]


def essential_spend_by_month(
    transactions: list[Transaction], category_of: dict[str, str]
) -> dict[str, float]:
    """Essential-category spend (housing, utilities, insurance, groceries)."""
    spend: dict[str, float] = {}
    for txn in transactions:
        if txn.amount >= 0:
            continue
        if category_of.get(txn.description, "Uncategorized") in ESSENTIAL_CATEGORIES:
            key = month_key(txn.date)
            spend[key] = spend.get(key, 0.0) + abs(txn.amount)
    return {k: round(v, 2) for k, v in spend.items()}


def compute_cashflow(
    transactions: list[Transaction],
    category_of: dict[str, str],
    tax_setaside_monthly: float,
    liquid_cash: float = 15000.0,
) -> dict:
    """Compute the headline cash-flow numbers."""
    series = monthly_series(transactions)
    if not series:
        raise ValueError("no transactions to analyze")
    essential = essential_spend_by_month(transactions, category_of)

    avg_income = mean(m["income"] for m in series)
    avg_expenses = mean(m["expenses"] for m in series)
    avg_essential = mean(list(essential.values())) if essential else 0.0

    safe_spend = avg_income - avg_essential - tax_setaside_monthly
    runway = liquid_cash / avg_expenses if avg_expenses > 0 else float("inf")

    last = series[-1]["month"]
    last_year, last_mon = int(last[:4]), int(last[5:7])
    forecast = []
    for i in range(1, FORECAST_MONTHS + 1):
        y, m = add_months(last_year, last_mon, i)
        forecast.append(
            {
                "month": f"{y:04d}-{m:02d}",
                "income": round(avg_income, 2),
                "expenses": round(avg_expenses, 2),
                "net": round(avg_income - avg_expenses, 2),
            }
        )

    return {
        "months_covered": len(series),
        "avg_monthly_income": round(avg_income, 2),
        "avg_monthly_expenses": round(avg_expenses, 2),
        "avg_essential_spend": round(avg_essential, 2),
        "tax_setaside_monthly": round(tax_setaside_monthly, 2),
        "safe_spend": round(safe_spend, 2),
        "runway_months": round(runway, 1) if runway != float("inf") else None,
        "liquid_cash_assumed": round(liquid_cash, 2),
        "essential_categories": sorted(ESSENTIAL_CATEGORIES),
        "forecast": forecast,
    }
