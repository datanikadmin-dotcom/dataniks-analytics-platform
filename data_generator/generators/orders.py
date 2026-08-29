"""Generate orders, order items, payments, refunds, and shipments together."""

from __future__ import annotations
from datetime import timedelta

import numpy as np
import pandas as pd

from data_generator.config import (
    GeneratorConfig,
    CHANNELS, CHANNEL_IDS,
    WAREHOUSES, WAREHOUSE_IDS,
    CARRIERS, PAYMENT_METHODS,
    is_holiday,
)


# ── Date weights (seasonal + weekend + holiday lifts) ─────────────────────────

def _build_date_weights(dates: pd.DatetimeIndex) -> np.ndarray:
    """Return normalized sampling weights per calendar date."""
    weights = np.ones(len(dates), dtype=float)
    for i, d in enumerate(dates):
        pd_date = d.date()
        # Seasonal: Q4 peak, Q1 slow
        q = (pd_date.month - 1) // 3 + 1
        weights[i] *= {1: 0.80, 2: 0.90, 3: 1.00, 4: 1.35}[q]
        # November and December extra bump (BFCM)
        if pd_date.month == 11:
            weights[i] *= 1.20
        if pd_date.month == 12:
            weights[i] *= 1.40
        # Weekend lift
        if d.dayofweek >= 5:
            weights[i] *= 1.15
        # Holiday lift
        if is_holiday(pd_date):
            weights[i] *= 1.60
    weights /= weights.sum()
    return weights


# ── Main generator ─────────────────────────────────────────────────────────────

def generate(
    cfg: GeneratorConfig,
    customers_df: pd.DataFrame,
    products_df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(cfg.seed + 2)

    date_range = pd.date_range(cfg.start_date, cfg.end_date)
    date_weights = _build_date_weights(date_range)

    customer_ids = customers_df["customer_id"].values
    product_ids = products_df["product_id"].values
    product_prices = products_df["list_price"].values
    product_costs = products_df["unit_cost"].values

    # Segment-based repeat probability already baked into customer selection;
    # here we give Champions/Loyal higher selection probability.
    seg_order_prob = customers_df["customer_segment"].map(
        {"Champions": 3.0, "Loyal": 2.5, "Promising": 1.5, "At-Risk": 1.0, "New": 0.8}
    ).fillna(1.0).values
    seg_order_prob /= seg_order_prob.sum()

    n_orders = cfg.orders

    # ── Orders ────────────────────────────────────────────────────────────────
    order_dates = rng.choice(date_range, size=n_orders, p=date_weights)
    order_customer_ids = rng.choice(customer_ids, size=n_orders, p=seg_order_prob)
    order_channels = rng.choice(CHANNELS, size=n_orders, p=[0.28, 0.24, 0.18, 0.12, 0.10, 0.05, 0.03])

    # Discount rate: 20 % of orders get a discount of 5-30 %
    discount_mask = rng.random(n_orders) < 0.20
    discount_rates = np.where(discount_mask, rng.uniform(0.05, 0.30, n_orders), 0.0)

    # Order status probabilities
    statuses = rng.choice(
        ["completed", "completed", "completed", "completed",
         "processing", "shipped", "refunded", "cancelled"],
        size=n_orders,
    )

    # Tax rate 0-10 %
    tax_rates = rng.uniform(0.0, 0.10, n_orders)
    # Shipping $0-$20
    shipping_amounts = np.round(rng.uniform(0, 20, n_orders), 2)

    orders = []
    order_items_rows = []
    item_id_counter = 1

    for i in range(n_orders):
        order_id = f"ORD-{i + 1:08d}"
        n_items = int(rng.choice([1, 1, 1, 2, 2, 3, 4, 5], p=[0.35, 0.25, 0.15, 0.12, 0.07, 0.04, 0.01, 0.01]))

        subtotal = 0.0
        item_cost = 0.0
        item_discount = 0.0

        # Sample products (weighted toward popular ones — power-law)
        prod_weights = 1.0 / (np.arange(len(product_ids)) + 1) ** 0.7
        prod_weights /= prod_weights.sum()
        chosen_idxs = rng.choice(len(product_ids), size=n_items, replace=False, p=prod_weights)

        for idx in chosen_idxs:
            qty = int(rng.choice([1, 1, 1, 2, 3], p=[0.60, 0.20, 0.10, 0.06, 0.04]))
            unit_price = float(product_prices[idx])
            cost = float(product_costs[idx])
            line_discount = round(unit_price * qty * discount_rates[i], 2)
            revenue = round(unit_price * qty - line_discount, 2)
            gp = round(revenue - cost * qty, 2)

            order_items_rows.append({
                "order_item_id": f"ITEM-{item_id_counter:010d}",
                "order_id":      order_id,
                "product_id":    product_ids[idx],
                "quantity":      qty,
                "unit_price":    round(unit_price, 2),
                "discount":      line_discount,
                "cost":          round(cost * qty, 2),
                "revenue":       revenue,
                "gross_profit":  gp,
            })
            subtotal += unit_price * qty
            item_cost += cost * qty
            item_discount += line_discount
            item_id_counter += 1

        subtotal = round(subtotal, 2)
        discount_amt = round(item_discount, 2)
        tax_amt = round((subtotal - discount_amt) * tax_rates[i], 2)
        total = round(subtotal - discount_amt + tax_amt + shipping_amounts[i], 2)

        orders.append({
            "order_id":     order_id,
            "customer_id":  order_customer_ids[i],
            "order_date":   pd.Timestamp(order_dates[i]).date(),
            "channel_id":   CHANNEL_IDS[order_channels[i]],
            "channel":      order_channels[i],
            "order_status": statuses[i],
            "subtotal":     subtotal,
            "discount":     discount_amt,
            "tax":          tax_amt,
            "shipping":     float(shipping_amounts[i]),
            "total_amount": total,
        })

    orders_df = pd.DataFrame(orders)
    items_df = pd.DataFrame(order_items_rows)

    # ── Payments ──────────────────────────────────────────────────────────────
    payment_rows = []
    for i, row in enumerate(orders):
        # 2 % of payments fail
        status = "failed" if rng.random() < 0.02 else "completed"
        offset_hours = int(rng.integers(0, 3))
        payment_rows.append({
            "payment_id":     f"PAY-{i + 1:09d}",
            "order_id":       row["order_id"],
            "payment_date":   (
                pd.Timestamp(order_dates[i]) + timedelta(hours=offset_hours)
            ).date(),
            "payment_method": rng.choice(PAYMENT_METHODS, p=[0.40, 0.20, 0.15, 0.10, 0.10, 0.05]),
            "amount":         row["total_amount"],
            "status":         status,
        })

    payments_df = pd.DataFrame(payment_rows)

    # ── Refunds ───────────────────────────────────────────────────────────────
    refundable_orders = orders_df[orders_df["order_status"] == "refunded"]["order_id"].tolist()
    # Also add random refunds to ~5 % of completed orders
    completed = orders_df[orders_df["order_status"] == "completed"]["order_id"].values
    extra_refund_ids = rng.choice(
        completed,
        size=max(0, cfg.refunds - len(refundable_orders)),
        replace=False,
    ).tolist()
    all_refund_order_ids = refundable_orders + extra_refund_ids

    refund_reasons = ["damaged", "not_as_described", "wrong_item", "changed_mind", "defective"]
    refund_rows = []
    for j, oid in enumerate(all_refund_order_ids):
        matching = orders_df.loc[orders_df["order_id"] == oid, "total_amount"]
        if matching.empty:
            continue
        max_refund = float(matching.iloc[0])
        refund_amt = round(rng.uniform(0.10, 1.0) * max_refund, 2)
        # Refund date: 1-14 days after order
        order_date = orders_df.loc[orders_df["order_id"] == oid, "order_date"].iloc[0]
        refund_date = (pd.Timestamp(order_date) + timedelta(days=int(rng.integers(1, 15)))).date()

        refund_rows.append({
            "refund_id":   f"REF-{j + 1:08d}",
            "order_id":    oid,
            "refund_date": refund_date,
            "amount":      refund_amt,
            "reason":      rng.choice(refund_reasons),
            "status":      "completed",
        })

    refunds_df = pd.DataFrame(refund_rows)

    # ── Shipments ─────────────────────────────────────────────────────────────
    shippable = orders_df[orders_df["order_status"].isin(["completed", "shipped", "refunded"])]
    shipment_rows = []
    for j, (_, row) in enumerate(shippable.iterrows()):
        warehouse = rng.choice(WAREHOUSES)
        carrier = rng.choice(CARRIERS)
        shipped_offset = int(rng.integers(1, 4))
        transit_days = int(rng.integers(2, 10))
        shipped_date = (pd.Timestamp(row["order_date"]) + timedelta(days=shipped_offset)).date()
        est_delivery = (pd.Timestamp(shipped_date) + timedelta(days=transit_days)).date()

        # 5 % late, 3 % lost/delayed
        actual_delta = int(rng.integers(-1, transit_days + 5))
        delivered_date = (pd.Timestamp(shipped_date) + timedelta(days=max(1, actual_delta))).date()
        if str(delivered_date) > str(cfg.end_date):
            delivered_date = None
            ship_status = "in_transit"
        elif actual_delta > transit_days + 2:
            ship_status = "delivered_late"
        else:
            ship_status = "delivered"

        shipment_rows.append({
            "shipment_id":              f"SHIP-{j + 1:08d}",
            "order_id":                 row["order_id"],
            "warehouse_id":             WAREHOUSE_IDS[warehouse],
            "warehouse":                warehouse,
            "carrier":                  carrier,
            "shipped_date":             shipped_date,
            "estimated_delivery_date":  est_delivery,
            "delivered_date":           delivered_date,
            "shipment_status":          ship_status,
        })

    shipments_df = pd.DataFrame(shipment_rows)

    return {
        "orders":      orders_df,
        "order_items": items_df,
        "payments":    payments_df,
        "refunds":     refunds_df,
        "shipments":   shipments_df,
    }
