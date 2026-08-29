"""Generate ad-spend records across Google and Meta campaigns."""

from __future__ import annotations
import numpy as np
import pandas as pd

from data_generator.config import GeneratorConfig, CHANNEL_IDS, is_holiday


_CAMPAIGNS = {
    "google_ads": [
        "Brand Search", "Non-Brand Search", "Shopping - Electronics",
        "Shopping - Apparel", "Display Retargeting", "YouTube Awareness",
    ],
    "meta_ads": [
        "Prospecting - Broad", "Lookalike - Purchasers", "Retargeting - Cart",
        "Brand Awareness", "Seasonal Sale", "Product Carousel",
    ],
}

# Performance tiers — campaigns have different baseline ROAS
_CAMPAIGN_TIERS = {
    "Brand Search":            {"cpc": 0.80, "cvr": 0.12, "roas": 8.0},
    "Non-Brand Search":        {"cpc": 1.80, "cvr": 0.04, "roas": 3.5},
    "Shopping - Electronics":  {"cpc": 0.90, "cvr": 0.06, "roas": 4.5},
    "Shopping - Apparel":      {"cpc": 0.70, "cvr": 0.05, "roas": 4.0},
    "Display Retargeting":     {"cpc": 0.40, "cvr": 0.03, "roas": 5.0},
    "YouTube Awareness":       {"cpc": 0.05, "cvr": 0.01, "roas": 1.5},
    "Prospecting - Broad":     {"cpc": 1.20, "cvr": 0.02, "roas": 2.0},
    "Lookalike - Purchasers":  {"cpc": 1.10, "cvr": 0.04, "roas": 3.8},
    "Retargeting - Cart":      {"cpc": 0.90, "cvr": 0.06, "roas": 6.0},
    "Brand Awareness":         {"cpc": 0.06, "cvr": 0.01, "roas": 1.2},
    "Seasonal Sale":           {"cpc": 1.40, "cvr": 0.05, "roas": 4.2},
    "Product Carousel":        {"cpc": 1.00, "cvr": 0.03, "roas": 3.0},
}


def generate(cfg: GeneratorConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed + 4)
    date_range = pd.date_range(cfg.start_date, cfg.end_date)

    rows = []
    rec_id = 1
    campaign_id = 1
    campaign_id_map: dict[str, int] = {}

    for channel, campaigns in _CAMPAIGNS.items():
        channel_id = CHANNEL_IDS.get(
            "paid_search" if channel == "google_ads" else "social_media", 2
        )
        for camp_name in campaigns:
            if camp_name not in campaign_id_map:
                campaign_id_map[camp_name] = campaign_id
                campaign_id += 1

            tier = _CAMPAIGN_TIERS.get(camp_name, {"cpc": 1.0, "cvr": 0.03, "roas": 3.0})

            for d in date_range:
                # Not every campaign runs every day
                if rng.random() < 0.05:
                    continue

                pd_date = d.date()
                # Seasonal budget multiplier
                q = (pd_date.month - 1) // 3 + 1
                budget_mult = {1: 0.7, 2: 0.85, 3: 1.0, 4: 1.4}[q]
                if pd_date.month in (11, 12):
                    budget_mult *= 1.3
                if is_holiday(pd_date):
                    budget_mult *= 1.5

                impressions = int(rng.integers(500, 50_000) * budget_mult)
                ctr = float(np.clip(rng.normal(0.03, 0.01), 0.005, 0.15))
                clicks = max(1, int(impressions * ctr))
                cpc = tier["cpc"] * float(np.clip(rng.normal(1.0, 0.15), 0.5, 2.0))
                spend = round(clicks * cpc, 2)
                cvr = tier["cvr"] * float(np.clip(rng.normal(1.0, 0.20), 0.3, 2.5))
                conversions = max(0, int(clicks * cvr))
                avg_order_value = float(rng.normal(95, 30))
                attributed_revenue = round(conversions * max(0, avg_order_value), 2)

                rows.append({
                    "ad_record_id":       f"AD-{rec_id:010d}",
                    "date":               pd_date,
                    "campaign_id":        campaign_id_map[camp_name],
                    "campaign_name":      camp_name,
                    "channel_id":         channel_id,
                    "channel":            channel,
                    "impressions":        impressions,
                    "clicks":             clicks,
                    "conversions":        conversions,
                    "spend":              spend,
                    "attributed_revenue": attributed_revenue,
                })
                rec_id += 1

    return pd.DataFrame(rows)
