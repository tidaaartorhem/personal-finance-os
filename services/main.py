"""CLI orchestrator: python services/main.py build --input data/sample-transactions.csv --cash 15000

Runs ingest -> categorize -> subscriptions -> tax -> cashflow -> brief and
writes web/public/finance.json plus a Markdown brief under data/.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from services import ingest  # noqa: E402
from services import categorize, subscriptions, cashflow, tax, brief  # noqa: E402


def run_build(input_csv: Path, liquid_cash: float) -> dict:
    txns, skipped, warnings = ingest.load_csv(input_csv)
    rules = categorize.load_rules(ROOT / "data" / "category-rules.json")
    category_of = {t.description: categorize.categorize(t.description, rules) for t in txns}

    subs = subscriptions.detect_subscriptions(txns)

    total_income = round(sum(t.amount for t in txns if t.amount > 0), 2)
    business_expenses = round(
        sum(
            abs(t.amount)
            for t in txns
            if t.amount < 0 and category_of[t.description] == "Business"
        ),
        2,
    )
    months = len({(t.date.year, t.date.month) for t in txns}) or 1
    annualized_net = (total_income - business_expenses) * 12 / months
    tax_estimate = tax.estimate_tax(annualized_net)

    flow = cashflow.compute_cashflow(
        txns, category_of, tax_estimate["monthly_set_aside"], liquid_cash
    )
    cats = cashflow.category_totals(txns, category_of)
    money_brief = brief.build_brief(txns, category_of, cats, subs, flow, tax_estimate)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": {
            "start": min(t.date for t in txns).isoformat(),
            "end": max(t.date for t in txns).isoformat(),
        },
        "summary": {
            "transactions": len(txns),
            "skipped_rows": skipped,
            "total_income": total_income,
            "total_expenses": round(sum(abs(t.amount) for t in txns if t.amount < 0), 2),
            "business_expenses": business_expenses,
            "annualized_net_business_income": round(annualized_net, 2),
            "warnings": warnings[:10],
        },
        "monthly_series": cashflow.monthly_series(txns),
        "categories": cats,
        "subscriptions": subs,
        "cashflow": flow,
        "tax": tax_estimate,
        "brief": money_brief,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="personal-finance-os pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="run the full pipeline")
    build.add_argument("--input", default="data/sample-transactions.csv")
    build.add_argument("--cash", type=float, default=15000.0,
                       help="assumed liquid cash for the runway calculation")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    result = run_build(input_path, args.cash)

    out_dir = ROOT / "web" / "public"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "finance.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    brief_path = ROOT / "data" / "latest-brief.md"
    brief_path.write_text(result["brief"]["markdown"] + "\n", encoding="utf-8")

    s = result["summary"]
    f = result["cashflow"]
    print(f"transactions : {s['transactions']} ({s['skipped_rows']} rows skipped)")
    print(f"period       : {result['period']['start']} to {result['period']['end']}")
    print(f"income       : ${s['total_income']:,.2f}")
    print(f"expenses     : ${s['total_expenses']:,.2f}")
    print(f"subscriptions: {len(result['subscriptions'])} recurring charges")
    print(f"safe spend   : ${f['safe_spend']:,.2f}/mo")
    print(f"runway       : {f['runway_months']} months")
    print(f"tax set-aside: ${result['tax']['monthly_set_aside']:,.2f}/mo")
    print(f"wrote        : {out_path}")
    print(f"wrote        : {brief_path}")


if __name__ == "__main__":
    main()
