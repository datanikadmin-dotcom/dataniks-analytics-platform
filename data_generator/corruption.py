"""
Intentional data-quality corruption step.

Inserts realistic defects into the synthetic dataset to demonstrate
data-quality monitoring. Corruption is reproducible via the random seed.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from data_generator.config import GeneratorConfig

logger = logging.getLogger(__name__)


@dataclass
class CorruptionReport:
    total_records_affected: int = 0
    defects: list[dict] = field(default_factory=list)

    def add(self, defect_type: str, dataset: str, count: int, description: str) -> None:
        self.defects.append({
            "defect_type": defect_type,
            "dataset":     dataset,
            "count":       count,
            "description": description,
        })
        self.total_records_affected += count
        logger.info("  [corruption] %-40s  n=%d", defect_type, count)


def apply(
    datasets: dict[str, pd.DataFrame],
    cfg: GeneratorConfig,
) -> tuple[dict[str, pd.DataFrame], CorruptionReport]:
    """Apply all corruption defects and return modified datasets + report."""
    rng = np.random.default_rng(cfg.seed + 99)
    pct = cfg.corruption_pct
    report = CorruptionReport()

    orders      = datasets["orders"].copy()
    items       = datasets["order_items"].copy()
    payments    = datasets["payments"].copy()
    refunds     = datasets["refunds"].copy()
    customers   = datasets["customers"].copy()
    products    = datasets["products"].copy()
    inventory   = datasets["inventory"].copy()
    shipments   = datasets["shipments"].copy()

    # ── 1. Duplicate orders ──────────────────────────────────────────────────
    n_dupe = max(1, int(len(orders) * pct * 0.5))
    dupe_idx = rng.choice(orders.index, size=n_dupe, replace=False)
    dupes = orders.loc[dupe_idx].copy()
    orders = pd.concat([orders, dupes], ignore_index=True)
    report.add("duplicate_orders", "orders", n_dupe, "Exact duplicates appended")

    # ── 2. Orphan order items (order_id not in orders) ───────────────────────
    n_orphan = max(1, int(len(items) * pct * 0.3))
    orphan_idx = rng.choice(items.index, size=n_orphan, replace=False)
    items.loc[orphan_idx, "order_id"] = "ORD-INVALID-9999"
    report.add("orphan_order_items", "order_items", n_orphan, "order_id → non-existent order")

    # ── 3. Payments without matching orders ──────────────────────────────────
    n_pay_orphan = max(1, int(len(payments) * pct * 0.2))
    orphan_pay_idx = rng.choice(payments.index, size=n_pay_orphan, replace=False)
    payments.loc[orphan_pay_idx, "order_id"] = "ORD-GHOST-0000"
    report.add("orphan_payments", "payments", n_pay_orphan, "payment references non-existent order")

    # ── 4. Refunds exceeding payment amount ──────────────────────────────────
    n_over_refund = max(1, int(len(refunds) * pct))
    over_idx = rng.choice(refunds.index, size=n_over_refund, replace=False)
    refunds.loc[over_idx, "amount"] *= float(rng.uniform(1.1, 2.0))
    refunds.loc[over_idx, "amount"] = refunds.loc[over_idx, "amount"].round(2)
    report.add("refund_exceeds_payment", "refunds", n_over_refund, "refund.amount > payment.amount")

    # ── 5. Null required fields ───────────────────────────────────────────────
    n_null_email = max(1, int(len(customers) * pct * 0.5))
    null_email_idx = rng.choice(customers.index, size=n_null_email, replace=False)
    customers.loc[null_email_idx, "email"] = None
    report.add("null_customer_email", "customers", n_null_email, "customers.email is null")

    n_null_sku = max(1, int(len(products) * pct * 0.3))
    null_sku_idx = rng.choice(products.index, size=n_null_sku, replace=False)
    products.loc[null_sku_idx, "sku"] = None
    report.add("null_product_sku", "products", n_null_sku, "products.sku is null")

    # ── 6. Invalid status values ─────────────────────────────────────────────
    n_bad_status = max(1, int(len(orders) * pct * 0.4))
    bad_status_idx = rng.choice(orders.index, size=n_bad_status, replace=False)
    orders.loc[bad_status_idx, "order_status"] = "UNKNOWN_STATUS"
    report.add("invalid_order_status", "orders", n_bad_status, "order_status not in accepted values")

    # ── 7. Negative inventory closing qty ────────────────────────────────────
    n_neg_inv = max(1, int(len(inventory) * pct * 0.5))
    neg_inv_idx = rng.choice(inventory.index, size=n_neg_inv, replace=False)
    inventory.loc[neg_inv_idx, "closing_qty"] = -abs(inventory.loc[neg_inv_idx, "closing_qty"])
    report.add("negative_inventory", "inventory", n_neg_inv, "closing_qty < 0")

    # ── 8. Revenue/payment mismatches ────────────────────────────────────────
    n_mismatch = max(1, int(len(payments) * pct * 0.3))
    mismatch_idx = rng.choice(payments.index, size=n_mismatch, replace=False)
    payments.loc[mismatch_idx, "amount"] = (
        payments.loc[mismatch_idx, "amount"] * rng.uniform(0.80, 0.95, n_mismatch)
    ).round(2)
    report.add("payment_amount_mismatch", "payments", n_mismatch, "payment.amount ≠ order.total_amount")

    # ── 9. Duplicate payments ────────────────────────────────────────────────
    n_dupe_pay = max(1, int(len(payments) * pct * 0.2))
    dupe_pay_idx = rng.choice(payments.index, size=n_dupe_pay, replace=False)
    dup_pays = payments.loc[dupe_pay_idx].copy()
    payments = pd.concat([payments, dup_pays], ignore_index=True)
    report.add("duplicate_payments", "payments", n_dupe_pay, "Exact duplicate payment rows")

    # ── 10. Late shipment records (shipped_date after delivered_date) ─────────
    non_null_delivered = shipments[shipments["delivered_date"].notna()].index
    n_late = max(1, int(len(non_null_delivered) * pct * 0.5))
    late_idx = rng.choice(non_null_delivered, size=n_late, replace=False)
    shipments.loc[late_idx, "shipped_date"] = shipments.loc[late_idx, "delivered_date"]
    report.add("late_shipment_date", "shipments", n_late, "shipped_date >= delivered_date")

    return {
        "customers":   customers,
        "products":    products,
        "orders":      orders,
        "order_items": items,
        "payments":    payments,
        "refunds":     refunds,
        "inventory":   inventory,
        "shipments":   shipments,
        "advertising": datasets["advertising"],
        "payouts":     datasets["payouts"],
    }, report
