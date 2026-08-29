"""Unit tests for the synthetic data generator."""

from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure repo root is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_generator.config import GeneratorConfig
from data_generator.generators import customers, products, orders, inventory, advertising, payouts
from data_generator.corruption import apply as apply_corruption


@pytest.fixture(scope="module")
def cfg():
    return GeneratorConfig(seed=42, customers=500, products=100, orders=1000)


@pytest.fixture(scope="module")
def customers_df(cfg):
    return customers.generate(cfg)


@pytest.fixture(scope="module")
def products_df(cfg):
    return products.generate(cfg)


@pytest.fixture(scope="module")
def order_datasets(cfg, customers_df, products_df):
    return orders.generate(cfg, customers_df, products_df)


# ── Customers ─────────────────────────────────────────────────────────────────

class TestCustomers:
    def test_row_count(self, cfg, customers_df):
        assert len(customers_df) == cfg.customers

    def test_unique_customer_ids(self, customers_df):
        assert customers_df["customer_id"].is_unique

    def test_required_columns(self, customers_df):
        required = ["customer_id", "first_name", "last_name", "email",
                    "signup_date", "country", "state", "customer_segment", "acquisition_channel"]
        for col in required:
            assert col in customers_df.columns, f"Missing column: {col}"

    def test_valid_segments(self, customers_df):
        valid = {"Champions", "Loyal", "At-Risk", "Promising", "New"}
        assert set(customers_df["customer_segment"].unique()).issubset(valid)

    def test_country_us(self, customers_df):
        assert (customers_df["country"] == "US").all()

    def test_deterministic(self, cfg):
        df1 = customers.generate(cfg)
        df2 = customers.generate(cfg)
        assert df1["customer_id"].tolist() == df2["customer_id"].tolist()


# ── Products ──────────────────────────────────────────────────────────────────

class TestProducts:
    def test_row_count(self, cfg, products_df):
        assert len(products_df) == cfg.products

    def test_unique_product_ids(self, products_df):
        assert products_df["product_id"].is_unique

    def test_positive_prices(self, products_df):
        assert (products_df["list_price"] > 0).all()
        assert (products_df["unit_cost"] > 0).all()

    def test_cost_below_price(self, products_df):
        assert (products_df["unit_cost"] < products_df["list_price"]).all()

    def test_valid_categories(self, products_df):
        from data_generator.config import CATEGORIES
        assert set(products_df["category"].unique()).issubset(set(CATEGORIES.keys()))


# ── Orders ────────────────────────────────────────────────────────────────────

class TestOrders:
    def test_order_row_count(self, cfg, order_datasets):
        # orders may be slightly above n_orders due to rounding
        assert len(order_datasets["orders"]) >= cfg.orders

    def test_unique_order_ids_in_clean(self, order_datasets):
        # Before corruption, order_ids must be unique
        assert order_datasets["orders"]["order_id"].is_unique

    def test_order_items_reference_orders(self, order_datasets):
        order_ids = set(order_datasets["orders"]["order_id"])
        item_order_ids = set(order_datasets["order_items"]["order_id"])
        assert item_order_ids.issubset(order_ids)

    def test_positive_totals(self, order_datasets):
        assert (order_datasets["orders"]["total_amount"] >= 0).all()

    def test_payments_count(self, cfg, order_datasets):
        assert len(order_datasets["payments"]) == cfg.orders

    def test_refunds_count(self, cfg, order_datasets):
        # Refunds come from "refunded" status orders plus extra completed orders.
        # Allow up to 2× the target (small datasets amplify variance).
        assert len(order_datasets["refunds"]) <= cfg.refunds * 2

    def test_refunds_reference_real_orders(self, order_datasets):
        order_ids = set(order_datasets["orders"]["order_id"])
        refund_order_ids = set(order_datasets["refunds"]["order_id"])
        assert refund_order_ids.issubset(order_ids)


# ── Corruption ────────────────────────────────────────────────────────────────

class TestCorruption:
    def test_defect_types(self, cfg, customers_df, products_df, order_datasets):
        inventory_df = inventory.generate(cfg, products_df)
        advertising_df = advertising.generate(cfg)
        payouts_df = payouts.generate(cfg, order_datasets["orders"], order_datasets["refunds"])

        all_ds = {
            "customers": customers_df, "products": products_df,
            **order_datasets,
            "inventory": inventory_df, "advertising": advertising_df, "payouts": payouts_df,
        }
        corrupted, report = apply_corruption(all_ds, cfg)
        assert len(report.defects) == 11
        assert report.total_records_affected > 0

    def test_corruption_is_deterministic(self, cfg, customers_df, products_df, order_datasets):
        inventory_df = inventory.generate(cfg, products_df)
        advertising_df = advertising.generate(cfg)
        payouts_df = payouts.generate(cfg, order_datasets["orders"], order_datasets["refunds"])

        base = {
            "customers": customers_df, "products": products_df,
            **order_datasets,
            "inventory": inventory_df, "advertising": advertising_df, "payouts": payouts_df,
        }
        _, r1 = apply_corruption(base, cfg)
        _, r2 = apply_corruption(base, cfg)
        assert r1.total_records_affected == r2.total_records_affected

    def test_duplicate_orders_injected(self, cfg, customers_df, products_df, order_datasets):
        inventory_df = inventory.generate(cfg, products_df)
        advertising_df = advertising.generate(cfg)
        payouts_df = payouts.generate(cfg, order_datasets["orders"], order_datasets["refunds"])

        base = {
            "customers": customers_df, "products": products_df,
            **order_datasets,
            "inventory": inventory_df, "advertising": advertising_df, "payouts": payouts_df,
        }
        corrupted, _ = apply_corruption(base, cfg)
        # After corruption, order_ids should NOT be unique
        assert not corrupted["orders"]["order_id"].is_unique

    def test_null_emails_injected(self, cfg, customers_df, products_df, order_datasets):
        inventory_df = inventory.generate(cfg, products_df)
        advertising_df = advertising.generate(cfg)
        payouts_df = payouts.generate(cfg, order_datasets["orders"], order_datasets["refunds"])

        base = {
            "customers": customers_df, "products": products_df,
            **order_datasets,
            "inventory": inventory_df, "advertising": advertising_df, "payouts": payouts_df,
        }
        corrupted, _ = apply_corruption(base, cfg)
        assert corrupted["customers"]["email"].isna().sum() > 0


# ── Advertising ───────────────────────────────────────────────────────────────

class TestAdvertising:
    def test_positive_spend(self, cfg):
        df = advertising.generate(cfg)
        assert (df["spend"] >= 0).all()

    def test_clicks_le_impressions(self, cfg):
        df = advertising.generate(cfg)
        assert (df["clicks"] <= df["impressions"]).all()

    def test_conversions_le_clicks(self, cfg):
        df = advertising.generate(cfg)
        assert (df["conversions"] <= df["clicks"]).all()
