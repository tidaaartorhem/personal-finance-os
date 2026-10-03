"""Tests for the personal-finance-os deterministic pipeline (stdlib only)."""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services import brief, cashflow, categorize, ingest, subscriptions, tax
from services.ingest import Transaction


def _txn(year, month, day, description, amount):
    return Transaction(date=date(year, month, day), description=description, amount=amount)


# ---------------------------------------------------------------- ingest

def test_parse_date_formats():
    assert ingest.parse_date("2026-03-15") == date(2026, 3, 15)
    assert ingest.parse_date("03/15/2026") == date(2026, 3, 15)
    assert ingest.parse_date("15-Mar-26") == date(2026, 3, 15)
    assert ingest.parse_date("15-Mar-2026") == date(2026, 3, 15)


def test_parse_amount_formats():
    assert ingest.parse_amount("$1,234.56") == 1234.56
    assert ingest.parse_amount("-45.00") == -45.00
    assert ingest.parse_amount("(45.00)") == -45.00


def test_load_csv_skips_bad_rows(tmp_path):
    csv_path = tmp_path / "bank.csv"
    csv_path.write_text(
        "date,description,amount\n"
        "2026-01-05,NETFLIX.COM,-16.99\n"
        "\n"
        "not-a-date,WHAT,-xx\n"
        "01/06/2026,PRESTO RELOAD,-25.00\n"
    )
    txns, skipped, warnings = ingest.load_csv(csv_path)
    assert len(txns) == 2
    assert skipped == 1
    assert len(warnings) == 1
    assert txns[0].description == "NETFLIX.COM"


# ---------------------------------------------------------------- categorize

def _rules():
    return [
        {"category": "Housing", "keywords": ["rent"]},
        {"category": "Income", "keywords": ["invoice"]},
        {"category": "Groceries", "regex": [r"\blo?blaws\b"]},
    ]


def test_categorize_rules_match():
    rules = _rules()
    assert categorize.categorize("INTERAC E-TRANSFER TO LANDLORD - RENT", rules) == "Housing"
    assert categorize.categorize("FROM NORTHWIND - INVOICE 1042", rules) == "Income"
    assert categorize.categorize("LOBLAWS #4821", rules) == "Groceries"


def test_categorize_unknown_fallback():
    assert categorize.categorize("SQ *MYSTERY MERCHANT", _rules()) == "Uncategorized"


def test_add_rule_extends_and_wins_by_position():
    rules = _rules()
    categorize.add_rule(rules, "Restaurants", keywords=["ramen"])
    assert categorize.categorize("KINTON RAMEN", rules) == "Restaurants"


# ---------------------------------------------------------------- subscriptions

def _monthly_series(merchant, amount, months=4, day=5, amount_wobble=0.0):
    txns = []
    for m in range(1, months + 1):
        txns.append(_txn(2026, m, day, merchant, -(amount + amount_wobble)))
    return txns


def test_detects_planted_monthly_subscription():
    txns = _monthly_series("NETFLIX.COM 866-579-7172", 16.99, months=6)
    found = subscriptions.detect_subscriptions(txns)
    assert len(found) == 1
    s = found[0]
    assert s["monthly_amount"] == 16.99
    assert s["annualized_cost"] == 203.88
    assert s["occurrences"] == 6
    assert s["confidence"] >= 0.7


def test_ignores_one_offs_and_quarterly():
    txns = [
        _txn(2026, 3, 8, "IKEA", -1250.00),
        _txn(2026, 2, 15, "MNP LLP - TAX ADVISORY", -450.00),
        _txn(2026, 5, 15, "MNP LLP - TAX ADVISORY", -450.00),  # quarterly: only 2
    ]
    txns += _monthly_series("SPOTIFY CANADA", 11.99, months=6)
    found = subscriptions.detect_subscriptions(txns)
    merchants = [s["merchant"] for s in found]
    assert any("spotify" in m for m in merchants)
    assert not any("ikea" in m or "mnp" in m for m in merchants)


def test_amount_drift_rejects_subscription():
    txns = []
    amounts = [50.0, 80.0, 50.0, 80.0]  # swings beyond 15% of median
    for i, a in enumerate(amounts, start=1):
        txns.append(_txn(2026, i, 5, "WOBBLY SERVICE", -a))
    assert subscriptions.detect_subscriptions(txns) == []


# ---------------------------------------------------------------- cashflow

def _fixture_cashflow():
    txns = []
    for m in range(1, 4):
        txns.append(_txn(2026, m, 3, "FROM CLIENT - INVOICE 1", 10000.0))
        txns.append(_txn(2026, m, 1, "RENT", -2000.0))
        txns.append(_txn(2026, m, 5, "LOBLAWS", -500.0))
        txns.append(_txn(2026, m, 7, "STAPLES", -300.0))
    category_of = {
        "FROM CLIENT - INVOICE 1": "Income",
        "RENT": "Housing",
        "LOBLAWS": "Groceries",
        "STAPLES": "Business",
    }
    return txns, category_of


def test_safe_spend_math():
    txns, category_of = _fixture_cashflow()
    flow = cashflow.compute_cashflow(txns, category_of, tax_setaside_monthly=1500.0,
                                    liquid_cash=12000.0)
    # 10000 income - 2500 essential (housing+groceries) - 1500 tax
    assert flow["safe_spend"] == 6000.0
    assert flow["avg_monthly_income"] == 10000.0
    assert flow["avg_essential_spend"] == 2500.0
    # burn = 2000+500+300 = 2800 -> 12000/2800 = 4.3
    assert flow["runway_months"] == round(12000 / 2800, 1)
    assert len(flow["forecast"]) == 3
    assert flow["forecast"][0]["month"] == "2026-04"


def test_monthly_series_net():
    txns, _ = _fixture_cashflow()
    series = cashflow.monthly_series(txns)
    assert [m["month"] for m in series] == ["2026-01", "2026-02", "2026-03"]
    assert series[0]["net"] == 10000.0 - 2800.0


# ---------------------------------------------------------------- tax

def test_higher_income_means_higher_effective_rate():
    low = tax.estimate_tax(60_000)
    high = tax.estimate_tax(200_000)
    assert high["effective_rate"] > low["effective_rate"]


def test_tax_set_aside_positive_and_sums():
    est = tax.estimate_tax(120_000)
    assert est["monthly_set_aside"] == round(est["total_estimated"] / 12, 2)
    assert est["total_estimated"] == round(
        est["federal_tax"] + est["ontario_tax"] + est["cpp_self_employed"], 2
    )
    assert est["federal_tax"] > 0 and est["ontario_tax"] > 0
    assert "not tax advice" in est["disclaimer"].lower()


def test_zero_income_zero_tax():
    est = tax.estimate_tax(0)
    assert est["total_estimated"] == 0
    assert est["monthly_set_aside"] == 0
    assert est["effective_rate"] == 0


# ---------------------------------------------------------------- brief

def test_anomaly_detection_flags_outlier():
    txns = [_txn(2026, m, 10, "LOBLAWS", -100.0) for m in range(1, 7)]
    txns.append(_txn(2026, 4, 17, "APPLE STORE", -2900.0))
    category_of = {"LOBLAWS": "Groceries", "APPLE STORE": "Shopping"}
    anomalies = brief.detect_anomalies(txns, category_of, months_covered=6)
    assert len(anomalies) == 1
    assert anomalies[0]["description"] == "APPLE STORE"
    assert anomalies[0]["multiple"] > 2.5


# ---------------------------------------------------------------- pipeline smoke

def test_pipeline_smoke_on_sample_data():
    from services import main
    result = main.run_build(ROOT / "data" / "sample-transactions.csv", 15000.0)
    assert result["summary"]["transactions"] > 200
    assert result["summary"]["skipped_rows"] >= 1
    assert len(result["subscriptions"]) >= 10
    assert result["cashflow"]["safe_spend"] > 0
    assert result["tax"]["monthly_set_aside"] > 0
    assert len(result["brief"]["bullets"]) > 3
    assert len(result["monthly_series"]) == 6
