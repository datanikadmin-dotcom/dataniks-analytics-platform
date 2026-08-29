"""Generate daily inventory snapshots per product × warehouse."""

from __future__ import annotations
import numpy as np
import pandas as pd

from data_generator.config import GeneratorConfig, WAREHOUSES, WAREHOUSE_IDS


def generate(cfg: GeneratorConfig, products_df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed + 3)

    # Sample dates — daily is too large; use first-of-month + random dates
    date_range = pd.date_range(cfg.start_date, cfg.end_date, freq="MS")  # month-start
    date_range = date_range.tolist()

    product_ids = products_df["product_id"].values
    unit_costs = products_df["unit_cost"].values

    rows = []
    rec_id = 1
    for d in date_range:
        for wh_idx, wh in enumerate(WAREHOUSES):
            # Sample ~40 % of products per warehouse per month
            n_products = int(len(product_ids) * 0.40)
            chosen_idxs = rng.choice(len(product_ids), size=n_products, replace=False)

            for pidx in chosen_idxs:
                opening = int(rng.integers(0, 500))
                received = int(rng.integers(0, 200)) if rng.random() < 0.6 else 0
                sold = int(rng.integers(0, min(opening + received + 1, 300)))
                adjustment = int(rng.integers(-10, 10)) if rng.random() < 0.1 else 0
                closing = max(0, opening + received - sold + adjustment)

                rows.append({
                    "inventory_id":    f"INV-{rec_id:010d}",
                    "date":            d.date(),
                    "product_id":      product_ids[pidx],
                    "warehouse_id":    WAREHOUSE_IDS[wh],
                    "warehouse":       wh,
                    "opening_qty":     opening,
                    "received_qty":    received,
                    "sold_qty":        sold,
                    "adjustment_qty":  adjustment,
                    "closing_qty":     closing,
                    "unit_cost":       float(unit_costs[pidx]),
                    "inventory_value": round(closing * float(unit_costs[pidx]), 2),
                })
                rec_id += 1

    return pd.DataFrame(rows)
