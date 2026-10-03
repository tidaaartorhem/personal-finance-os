"""Rule-based transaction categorizer driven by data/category-rules.json.

Rules are ordered: the first rule whose keyword or regex matches the
merchant description wins. Unmatched merchants fall back to
"Uncategorized" so nothing is silently mislabeled.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

UNCATEGORIZED = "Uncategorized"


def load_rules(path: str | Path) -> list[dict[str, Any]]:
    """Load the ordered rule list from a JSON file."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        data = data.get("rules", [])
    return list(data)


def categorize(description: str, rules: list[dict[str, Any]]) -> str:
    """Return the first matching rule's category, else Uncategorized."""
    text = description.lower()
    for rule in rules:
        for keyword in rule.get("keywords", []):
            if keyword.lower() in text:
                return rule["category"]
        for pattern in rule.get("regex", []):
            if re.search(pattern, text):
                return rule["category"]
    return UNCATEGORIZED


def add_rule(
    rules: list[dict[str, Any]],
    category: str,
    keywords: list[str] | None = None,
    regex: list[str] | None = None,
    position: int | None = None,
) -> list[dict[str, Any]]:
    """Insert a new rule into the ordered list (appended by default)."""
    rule: dict[str, Any] = {"category": category}
    if keywords:
        rule["keywords"] = list(keywords)
    if regex:
        rule["regex"] = list(regex)
    if position is None:
        rules.append(rule)
    else:
        rules.insert(position, rule)
    return rules


def categorize_all(
    descriptions: list[str], rules: list[dict[str, Any]]
) -> dict[str, str]:
    """Categorize many descriptions at once; returns {description: category}."""
    return {d: categorize(d, rules) for d in descriptions}
