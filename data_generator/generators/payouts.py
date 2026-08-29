"""Generate platform payout records (monthly reconciliation source)."""

from __future__ import annotations
from datetime import timedelta

import numpy as np
import pandas as pd

from data_generator.config import GeneratorConfig, PLATFORMS


def generate(
    cfg: GeneratorConfig,
    orders_df: pd.DataFrame,
    refunds_df: pd.DataFrame,
) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed + 5)

    rows = []
    payout_id = 1

    # Monthly periods
    periods = pd.period_range(cfg.start_date, cfg.end_date, freq="M")

    for period in periods:
        period_start = period.start_time.date()
        period_end = period.end_time.date()

        period_orders = orders_df[
            (orders_df["order_date"] >= period_start)
            & (orders_df["order_date"] <= period_end)
            & (orders_df["order_status"] == "completed")
        ]
        period_refunds = refunds_df[
            (refunds_df["refund_date"] >= period_start)
            & (refunds_df["refund_date"] <= period_end)
        ]

        gross_sales = float(period_orders["total_amount"].sum())
        total_refunds = float(period_refunds["amount"].sum())
        platform_fee_rate = float(rng.uniform(0.02, 0.05))
        fees = round(gross_sales * platform_fee_rate, 2)
        adjustments = round(float(rng.normal(0, 50)), 2)
        net_payout = round(gross_sales - fees - total_refunds + adjustments, 2)

        for platform in PLATFORMS:
            # Allocate portion to each platform
            platform_share = float(rng.uniform(0.20, 0.60))
            payout_date = period_end + timedelta(days=int(rng.integers(5, 15)))

            rows.append({
                "payout_id":   f"POUT-{payout_id:07d}",
                "payout_date": payout_date,
                "platform":    platform,
                "period_start": period_start,
                "period_end":  period_end,
                "gross_sales": round(gross_sales * platform_share, 2),
                "fees":        round(fees * platform_share, 2),
                "refunds":     round(total_refunds * platform_share, 2),
                "adjustments": round(adjustments * platform_share, 2),
                "net_payout":  round(net_payout * platform_share, 2),
            })
            payout_id += 1

    return pd.DataFrame(rows)
