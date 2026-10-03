"""Deterministic monthly money brief: plain declarative sentences, no hype.

The brief reads the pipeline outputs and states what happened, what it
costs, and what to set aside. Everything is computed from the data;
nothing is invented.
"""
from __future__ import annotations

from .ingest import Transaction

ANOMALY_MULTIPLE = 2.5  # a transaction is anomalous above this x of category monthly avg


def _fmt(value: float) -> str:
    return f"${value:,.2f}"


def detect_anomalies(
    transactions: list[Transaction],
    category_of: dict[str, str],
    months_covered: int,
) -> list[dict]:
    """Flag outflows larger than 2.5x their category's monthly average."""
    totals: dict[str, float] = {}
    for txn in transactions:
        if txn.amount < 0:
            cat = category_of.get(txn.description, "Uncategorized")
            totals[cat] = totals.get(cat, 0.0) + abs(txn.amount)
    anomalies = []
    for txn in transactions:
        if txn.amount >= 0:
            continue
        cat = category_of.get(txn.description, "Uncategorized")
        monthly_avg = totals[cat] / max(months_covered, 1)
        if monthly_avg > 0 and abs(txn.amount) > ANOMALY_MULTIPLE * monthly_avg:
            anomalies.append(
                {
                    "date": txn.date.isoformat(),
                    "description": txn.description,
                    "category": cat,
                    "amount": round(abs(txn.amount), 2),
                    "category_monthly_avg": round(monthly_avg, 2),
                    "multiple": round(abs(txn.amount) / monthly_avg, 1),
                }
            )
    anomalies.sort(key=lambda a: a["amount"], reverse=True)
    return anomalies


def build_brief(
    transactions: list[Transaction],
    category_of: dict[str, str],
    categories: list[dict],
    subscriptions: list[dict],
    cashflow: dict,
    tax: dict,
) -> dict:
    """Assemble the monthly money brief as structured data and Markdown."""
    months = cashflow.get("months_covered", 1)
    top3 = categories[:3]
    anomalies = detect_anomalies(transactions, category_of, months)
    sub_total = round(sum(s["monthly_amount"] for s in subscriptions), 2)
    sub_annual = round(sum(s["annualized_cost"] for s in subscriptions), 2)

    lines: list[str] = []
    lines.append("# Monthly money brief")
    lines.append("")
    lines.append(
        f"Over the last {months} months you averaged "
        f"{_fmt(cashflow['avg_monthly_income'])} of income against "
        f"{_fmt(cashflow['avg_monthly_expenses'])} of expenses."
    )
    if top3:
        top_desc = ", ".join(f"{c['category']} ({_fmt(c['total'])})" for c in top3)
        lines.append(f"Your top spend categories were {top_desc}.")
    lines.append(
        f"Your safe monthly spend is {_fmt(cashflow['safe_spend'])}. "
        f"That is average income minus essential spend of "
        f"{_fmt(cashflow['avg_essential_spend'])} and a tax set-aside of "
        f"{_fmt(cashflow['tax_setaside_monthly'])}."
    )
    lines.append(
        f"You have {len(subscriptions)} recurring charges costing "
        f"{_fmt(sub_total)} a month, or {_fmt(sub_annual)} a year."
    )
    if cashflow.get("runway_months") is not None:
        lines.append(
            f"At your average burn, {_fmt(cashflow['liquid_cash_assumed'])} "
            f"of liquid cash covers {cashflow['runway_months']} months."
        )
    if anomalies:
        lines.append("Unusual transactions worth a second look:")
        for a in anomalies[:5]:
            lines.append(
                f"- {a['date']}: {a['description']} ({_fmt(a['amount'])}, "
                f"{a['multiple']}x the {a['category']} monthly average)."
            )
    lines.append(
        f"Tax planning: set aside {_fmt(tax['monthly_set_aside'])} a month, "
        f"an estimated effective rate of {tax['effective_rate']:.1%} on "
        f"{_fmt(tax['net_business_income'])} of net business income. "
        "This is a planning estimate, not tax advice."
    )
    lines.append("")
    lines.append(
        "Next month's forecast: "
        f"{_fmt(cashflow['forecast'][0]['income'])} in, "
        f"{_fmt(cashflow['forecast'][0]['expenses'])} out."
        if cashflow.get("forecast")
        else "No forecast available."
    )

    return {
        "markdown": "\n".join(lines),
        "bullets": [l for l in lines if l and not l.startswith("#")],
        "anomalies": anomalies,
        "subscription_monthly_total": sub_total,
        "subscription_annual_total": sub_annual,
    }
