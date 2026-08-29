"""Generator configuration — drives record counts, seed, and date range."""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from datetime import date


@dataclass
class GeneratorConfig:
    seed: int = 42
    customers: int = 20_000
    products: int = 2_000
    orders: int = 100_000
    corruption_pct: float = 0.02

    # Derived targets (approximate)
    @property
    def order_items(self) -> int:
        return int(self.orders * 2.5)

    @property
    def payments(self) -> int:
        return self.orders

    @property
    def refunds(self) -> int:
        return int(self.orders * 0.08)

    @property
    def inventory_records(self) -> int:
        return self.products * 5 * 10  # products × warehouses × sampled_days

    @property
    def shipments(self) -> int:
        return self.orders

    @property
    def ad_records(self) -> int:
        return 50_000

    @property
    def payouts(self) -> int:
        return 5_000

    # Date range for generated data (last 2 full years + YTD)
    start_date: date = field(default_factory=lambda: date(2023, 1, 1))
    end_date: date = field(default_factory=lambda: date(2024, 12, 31))

    output_dir: str = "data/synthetic"
    format: str = "parquet"   # parquet | csv

    @classmethod
    def from_env(cls) -> "GeneratorConfig":
        return cls(
            seed=int(os.getenv("SYNTHETIC_SEED", "42")),
            customers=int(os.getenv("SYNTHETIC_CUSTOMERS", "20000")),
            products=int(os.getenv("SYNTHETIC_PRODUCTS", "2000")),
            orders=int(os.getenv("SYNTHETIC_ORDERS", "100000")),
            corruption_pct=float(os.getenv("SYNTHETIC_CORRUPTION_PCT", "0.02")),
        )


# US holidays (simplified) used for sales lift
US_HOLIDAYS = {
    # month, day
    (1, 1), (2, 14), (5, 27), (7, 4), (9, 2),
    (10, 31), (11, 28), (11, 29), (12, 24), (12, 25), (12, 31),
}


def is_holiday(d: date) -> bool:
    return (d.month, d.day) in US_HOLIDAYS


# Product categories with base margins
CATEGORIES = {
    "Electronics":    {"margin": 0.22, "price_range": (49, 1299), "weight": 0.18},
    "Apparel":        {"margin": 0.55, "price_range": (19, 299),  "weight": 0.20},
    "Home & Garden":  {"margin": 0.40, "price_range": (15, 499),  "weight": 0.15},
    "Sports":         {"margin": 0.38, "price_range": (25, 599),  "weight": 0.12},
    "Beauty":         {"margin": 0.62, "price_range": (12, 199),  "weight": 0.10},
    "Books":          {"margin": 0.30, "price_range": (8,  75),   "weight": 0.08},
    "Toys":           {"margin": 0.45, "price_range": (10, 149),  "weight": 0.09},
    "Food & Grocery": {"margin": 0.28, "price_range": (5,  89),   "weight": 0.08},
}

SUBCATEGORIES = {
    "Electronics":    ["Smartphones", "Laptops", "Tablets", "Headphones", "Cameras", "Accessories"],
    "Apparel":        ["Men's", "Women's", "Kids'", "Footwear", "Accessories"],
    "Home & Garden":  ["Furniture", "Décor", "Kitchen", "Garden", "Lighting"],
    "Sports":         ["Fitness", "Outdoor", "Team Sports", "Water Sports"],
    "Beauty":         ["Skincare", "Makeup", "Hair Care", "Fragrance"],
    "Books":          ["Fiction", "Non-Fiction", "Educational", "Comics"],
    "Toys":           ["Action Figures", "Board Games", "Educational", "Outdoor"],
    "Food & Grocery": ["Snacks", "Beverages", "Organic", "International"],
}

CHANNELS = ["organic_search", "paid_search", "social_media", "email", "direct", "affiliate", "referral"]
CHANNEL_IDS = {ch: i + 1 for i, ch in enumerate(CHANNELS)}

SEGMENTS = ["Champions", "Loyal", "At-Risk", "Promising", "New"]
SEGMENT_REPEAT_PROB = {
    "Champions": 0.85,
    "Loyal":     0.70,
    "At-Risk":   0.30,
    "Promising": 0.50,
    "New":       0.15,
}

WAREHOUSES = ["WH-EAST", "WH-WEST", "WH-CENTRAL", "WH-SOUTH", "WH-NORTH"]
WAREHOUSE_IDS = {wh: i + 1 for i, wh in enumerate(WAREHOUSES)}

CARRIERS = ["UPS", "FedEx", "USPS", "DHL", "OnTrac"]
PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "apple_pay", "google_pay", "bank_transfer"]
PLATFORMS = ["novacommerce_direct", "amazon_marketplace", "ebay"]
