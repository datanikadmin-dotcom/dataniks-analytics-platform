"""
Ingestion pipeline runner.

Connects extractors → loaders for all configured sources.
Called directly by Airflow DAGs or as a standalone CLI.
"""

from __future__ import annotations
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from ingestion import get_connector
from ingestion.loaders.duckdb_loader import DuckDBLoader

logger = logging.getLogger(__name__)


def load_sources_config(path: str = "config/sources.yaml") -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


def load_client_config(path: str = "config/client.yaml") -> dict[str, Any]:
    with open(path) as f:
        raw = yaml.safe_load(f)
    # Resolve ${ENV_VAR} references
    def _resolve(obj):
        if isinstance(obj, str):
            import re
            return re.sub(r"\$\{(\w+)\}", lambda m: os.getenv(m.group(1), m.group(0)), obj)
        if isinstance(obj, dict):
            return {k: _resolve(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_resolve(i) for i in obj]
        return obj
    return _resolve(raw)


# Map source name → (connector_method, raw_table_name)
_SOURCE_MAP = {
    "customers":   ("get_customers",  "raw_customers"),
    "products":    ("get_products",   "raw_products"),
    "orders":      ("get_orders",     "raw_orders"),
    "order_items": ("get_order_items","raw_order_items"),
    "payments":    ("get_payments",   "raw_payments"),
    "refunds":     ("get_refunds",    "raw_refunds"),
    "inventory":   ("get_inventory",  "raw_inventory"),
    "shipments":   ("get_shipments",  "raw_shipments"),
    "advertising": ("get_ad_spend",   "raw_ad_spend"),
    "payouts":     ("get_payouts",    "raw_payouts"),
}


def run_source(
    connector_name: str,
    provider: str,
    connector_config: dict,
    entities: list[str],
    loader: DuckDBLoader,
    since: datetime | None = None,
    drop_first: bool = False,
) -> dict[str, int]:
    """Extract and load a set of entities from one connector."""
    connector = get_connector(connector_name, provider, connector_config)
    connector.authenticate()

    if not connector.health_check():
        logger.error("[pipeline] %s health-check failed — skipping", connector_name)
        return {}

    if drop_first:
        for entity in entities:
            _, table = _SOURCE_MAP[entity]
            try:
                loader.execute(f"DROP TABLE IF EXISTS raw.{table}")
            except Exception:
                pass

    results: dict[str, int] = {}
    for entity in entities:
        method_name, table = _SOURCE_MAP[entity]
        method = getattr(connector, method_name, None)
        if method is None:
            logger.warning("[pipeline] %s has no method %s", connector_name, method_name)
            continue

        total_rows = 0
        try:
            for batch in method(since=since):
                rows_written = loader.load(batch, table=table)
                total_rows += rows_written
        except Exception as exc:
            logger.error("[pipeline] %s.%s failed: %s", connector_name, method_name, exc)
            continue

        results[entity] = total_rows
        logger.info("[pipeline] %-15s → %-25s  rows=%d", connector_name, table, total_rows)

    return results


def run_full_pipeline(
    sources_path: str = "config/sources.yaml",
    client_path: str = "config/client.yaml",
    since: datetime | None = None,
    drop_first: bool = True,
) -> dict[str, int]:
    """Run the complete ingestion pipeline for all configured sources."""
    sources = load_sources_config(sources_path)
    db_path = os.getenv("DUCKDB_PATH", "data/warehouse.duckdb")
    loader = DuckDBLoader(db_path=db_path)

    if drop_first:
        loader.drop_schema("raw")

    totals: dict[str, int] = {}

    # ── Commerce connector ────────────────────────────────────────────────────
    commerce = sources["sources"]["commerce"]
    if commerce.get("enabled", True):
        res = run_source(
            "commerce", commerce["provider"], commerce,
            ["customers", "products", "orders", "order_items"],
            loader, since=since,
        )
        totals.update(res)

    # ── Payments connector ────────────────────────────────────────────────────
    payments = sources["sources"]["payments"]
    if payments.get("enabled", True):
        res = run_source(
            "payments", payments["provider"], payments,
            ["payments", "refunds"],
            loader, since=since,
        )
        totals.update(res)

    # ── CRM connector ─────────────────────────────────────────────────────────
    # CRM entities overlap with commerce for mock; skip in this demo.

    # ── Advertising connectors ────────────────────────────────────────────────
    for ad_src in sources["sources"]["advertising"]["providers"]:
        if ad_src.get("enabled", True):
            res = run_source(
                ad_src["name"], ad_src["provider"], ad_src,
                ["advertising"],
                loader, since=since,
            )
            # Merge: advertising may be loaded by multiple connectors
            totals["advertising"] = totals.get("advertising", 0) + res.get("advertising", 0)

    # ── Inventory connector ───────────────────────────────────────────────────
    inventory = sources["sources"]["inventory"]
    if inventory.get("enabled", True):
        res = run_source(
            "inventory", inventory["provider"], inventory,
            ["inventory"],
            loader, since=since,
        )
        totals.update(res)

    # ── Fulfillment connector ─────────────────────────────────────────────────
    fulfillment = sources["sources"]["fulfillment"]
    if fulfillment.get("enabled", True):
        res = run_source(
            "fulfillment", fulfillment["provider"], fulfillment,
            ["shipments", "payouts"],
            loader, since=since,
        )
        totals.update(res)

    logger.info("[pipeline] Complete. Summary: %s", totals)
    return totals


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
    totals = run_full_pipeline()
    print("\nIngestion Summary:")
    for entity, n in totals.items():
        print(f"  {entity:<20} {n:>10,} rows")
