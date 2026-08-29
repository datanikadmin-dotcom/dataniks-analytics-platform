"""Load and query the metric catalog from config/metrics.yaml."""

from __future__ import annotations
from pathlib import Path
from typing import Any

import yaml


_DEFAULT_CATALOG_PATH = Path(__file__).resolve().parents[2] / "config" / "metrics.yaml"


class MetricCatalog:

    def __init__(self, path: str | Path = _DEFAULT_CATALOG_PATH) -> None:
        with open(path) as f:
            data = yaml.safe_load(f)
        self._metrics: dict[str, dict] = data.get("metrics", {})

    def get(self, name: str) -> dict[str, Any] | None:
        return self._metrics.get(name)

    def all_names(self) -> list[str]:
        return list(self._metrics.keys())

    def display_names(self) -> list[str]:
        return [m.get("display_name", k) for k, m in self._metrics.items()]

    def summary_text(self) -> str:
        """Return a compact text description of all metrics for prompt injection."""
        lines = ["Available metrics:"]
        for key, m in self._metrics.items():
            lines.append(f"  - {m.get('display_name', key)}: {m.get('description', '')}")
        return "\n".join(lines)

    def detect_relevant(self, question: str) -> list[str]:
        """Return metric keys whose keywords appear in the question."""
        q = question.lower()
        relevant = []
        keyword_map = {
            "gross_revenue":   ["revenue", "gross revenue", "sales"],
            "net_revenue":     ["net revenue", "net sales"],
            "cogs":            ["cogs", "cost of goods"],
            "gross_profit":    ["profit", "gross profit"],
            "gross_margin_pct": ["margin", "margin %"],
            "order_count":     ["orders", "order count", "order volume"],
            "aov":             ["aov", "average order", "order value"],
            "new_customers":   ["new customer", "acquisition"],
            "cac":             ["cac", "acquisition cost", "cost per customer"],
            "roas":            ["roas", "return on ad", "ad spend"],
            "refund_rate":     ["refund", "return rate"],
            "inventory_turnover": ["inventory", "stock", "turnover"],
            "ltv":             ["ltv", "lifetime value", "customer value"],
        }
        for key, keywords in keyword_map.items():
            if any(kw in q for kw in keywords):
                relevant.append(key)
        return relevant
