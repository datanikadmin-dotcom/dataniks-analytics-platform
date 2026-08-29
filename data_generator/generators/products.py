"""Generate realistic NovaCommerce product catalog."""

from __future__ import annotations
import numpy as np
import pandas as pd
from faker import Faker

from data_generator.config import GeneratorConfig, CATEGORIES, SUBCATEGORIES


_BRANDS = [
    "NovaTech", "PrimePick", "EcoLine", "LuxeCore", "SwiftBrand",
    "TrueValue", "ApexGoods", "ZenithCo", "BoldMark", "PureForm",
    "UrbanEdge", "NovaPeak", "ClearPath", "StellarGoods", "TerraWave",
]

_SUPPLIERS = [
    "GlobalSource Ltd", "FastTrade Co", "OceanBridge Supply", "PrimeMfg Inc",
    "SunriseGoods Corp", "AlphaSupply LLC", "MeridianGoods", "TradePath Inc",
]


def generate(cfg: GeneratorConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed + 1)
    fake = Faker("en_US")
    fake.seed_instance(cfg.seed + 1)

    n = cfg.products
    category_names = list(CATEGORIES.keys())
    cat_weights = [CATEGORIES[c]["weight"] for c in category_names]

    categories = rng.choice(category_names, size=n, p=cat_weights)

    records = []
    for i, cat in enumerate(categories):
        cat_cfg = CATEGORIES[cat]
        subcats = SUBCATEGORIES[cat]
        subcat = subcats[rng.integers(0, len(subcats))]

        lo, hi = cat_cfg["price_range"]
        list_price = round(float(rng.uniform(lo, hi)), 2)

        # Margin varies ±10 pp around the category baseline
        margin = float(np.clip(rng.normal(cat_cfg["margin"], 0.10), 0.05, 0.80))
        unit_cost = round(list_price * (1 - margin), 2)

        brand = _BRANDS[rng.integers(0, len(_BRANDS))]
        supplier = _SUPPLIERS[rng.integers(0, len(_SUPPLIERS))]

        records.append({
            "product_id":   f"PROD-{i + 1:06d}",
            "sku":          f"SKU-{cat[:3].upper()}-{i + 1:06d}",
            "product_name": f"{brand} {subcat} {fake.word().capitalize()} {rng.integers(100, 9999)}",
            "category":     cat,
            "subcategory":  subcat,
            "brand":        brand,
            "unit_cost":    unit_cost,
            "list_price":   list_price,
            "supplier":     supplier,
        })

    return pd.DataFrame(records)
