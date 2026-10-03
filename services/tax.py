"""Ontario self-employed tax estimator (2026 planning figures).

IMPORTANT: these are APPROXIMATE brackets used for planning estimates
only. They are not tax advice and are not a substitute for a tax
professional. Always verify against current CRA and Ontario figures.

Federal brackets below are approximations of the 2026 indexed tiers;
Ontario brackets approximate the 2026 provincial tiers. Self-employed
workers pay both halves of CPP, modeled here as a flat approximation.
"""
from __future__ import annotations

# (upper bound, marginal rate). Values are planning approximations for 2026.
FEDERAL_BRACKETS_2026 = [
    (57_375, 0.15),
    (114_750, 0.205),
    (177_882, 0.26),
    (253_414, 0.29),
    (float("inf"), 0.33),
]

ONTARIO_BRACKETS_2026 = [
    (55_231, 0.0505),
    (110_462, 0.0915),
    (150_000, 0.1116),
    (220_000, 0.1216),
    (float("inf"), 0.1316),
]

# CPP for the self-employed (both halves), 2026 approximations.
CPP_YMPE = 74_500      # year's maximum pensionable earnings
CPP_YAMPE = 80_400     # year's additional maximum pensionable earnings
CPP_EXEMPTION = 3_500
CPP_RATE_TIER1 = 0.119  # self-employed: employee + employer share
CPP_RATE_TIER2 = 0.08


def _apply_brackets(income: float, brackets: list[tuple]) -> tuple[float, list[dict]]:
    """Apply marginal brackets; returns (total_tax, per-bracket breakdown)."""
    tax = 0.0
    breakdown: list[dict] = []
    lower = 0.0
    for upper, rate in brackets:
        if income <= lower:
            break
        taxable = min(income, upper) - lower
        amount = taxable * rate
        tax += amount
        breakdown.append(
            {
                "lower": lower,
                "upper": None if upper == float("inf") else upper,
                "rate": rate,
                "taxable_amount": round(taxable, 2),
                "tax": round(amount, 2),
            }
        )
        lower = upper
    return round(tax, 2), breakdown


def estimate_cpp(net_income: float) -> float:
    """Approximate annual self-employed CPP contributions."""
    if net_income <= CPP_EXEMPTION:
        return 0.0
    tier1_base = min(net_income, CPP_YMPE) - CPP_EXEMPTION
    cpp = tier1_base * CPP_RATE_TIER1
    if net_income > CPP_YMPE:
        cpp += (min(net_income, CPP_YAMPE) - CPP_YMPE) * CPP_RATE_TIER2
    return round(cpp, 2)


def estimate_tax(net_business_income: float) -> dict:
    """Estimate combined 2026 tax on self-employment net income.

    Returns federal tax, Ontario tax, CPP, total, effective rate, monthly
    set-aside target, and the bracket breakdown. All figures are planning
    estimates, clearly labeled as such.
    """
    income = max(0.0, net_business_income)
    federal_tax, federal_brackets = _apply_brackets(income, FEDERAL_BRACKETS_2026)
    ontario_tax, ontario_brackets = _apply_brackets(income, ONTARIO_BRACKETS_2026)
    cpp = estimate_cpp(income)
    total = round(federal_tax + ontario_tax + cpp, 2)
    effective_rate = round(total / income, 4) if income > 0 else 0.0
    return {
        "net_business_income": round(income, 2),
        "federal_tax": federal_tax,
        "ontario_tax": ontario_tax,
        "cpp_self_employed": cpp,
        "total_estimated": total,
        "effective_rate": effective_rate,
        "monthly_set_aside": round(total / 12, 2),
        "bracket_breakdown": [
            {**b, "level": "Federal"} for b in federal_brackets
        ]
        + [{**b, "level": "Ontario"} for b in ontario_brackets],
        "disclaimer": (
            "Planning estimate only, based on approximate 2026 federal and "
            "Ontario brackets plus estimated self-employed CPP. Not tax advice."
        ),
    }
