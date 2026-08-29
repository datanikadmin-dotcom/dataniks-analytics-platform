"""Uniqueness checks — detect duplicate primary keys."""

from __future__ import annotations
from data_quality.checks.base import BaseCheck
from data_quality.models import Severity


class UniqueOrderIds(BaseCheck):
    check_id   = "uniq_001"
    check_name = "Unique Order IDs in staging"
    dataset    = "main_staging.stg_orders"
    severity   = Severity.CRITICAL

    def _execute(self):
        df = self.db.execute(
            "SELECT COUNT(*) AS total, COUNT(DISTINCT order_id) AS unique_ids "
            "FROM main_staging.stg_orders"
        )
        total = int(df["total"].iloc[0])
        unique = int(df["unique_ids"].iloc[0])
        dupes = total - unique
        return self._result(total, dupes, f"{dupes:,} duplicate order_ids detected")


class UniqueCustomerIds(BaseCheck):
    check_id   = "uniq_002"
    check_name = "Unique Customer IDs in staging"
    dataset    = "main_staging.stg_customers"
    severity   = Severity.CRITICAL

    def _execute(self):
        df = self.db.execute(
            "SELECT COUNT(*) AS total, COUNT(DISTINCT customer_id) AS unique_ids "
            "FROM main_staging.stg_customers"
        )
        total  = int(df["total"].iloc[0])
        unique = int(df["unique_ids"].iloc[0])
        dupes  = total - unique
        return self._result(total, dupes, f"{dupes:,} duplicate customer_ids detected")


class UniquePaymentIds(BaseCheck):
    check_id   = "uniq_003"
    check_name = "Unique Payment IDs (duplicate payment detection)"
    dataset    = "main_staging.stg_payments"
    severity   = Severity.CRITICAL

    def _execute(self):
        df = self.db.execute(
            "SELECT COUNT(*) AS total, COUNT(DISTINCT payment_id) AS unique_ids "
            "FROM main_staging.stg_payments"
        )
        total  = int(df["total"].iloc[0])
        unique = int(df["unique_ids"].iloc[0])
        dupes  = total - unique
        return self._result(total, dupes, f"{dupes:,} duplicate payment_ids detected")


class UniqueProductIds(BaseCheck):
    check_id   = "uniq_004"
    check_name = "Unique Product IDs in staging"
    dataset    = "main_staging.stg_products"
    severity   = Severity.CRITICAL

    def _execute(self):
        df = self.db.execute(
            "SELECT COUNT(*) AS total, COUNT(DISTINCT product_id) AS unique_ids "
            "FROM main_staging.stg_products"
        )
        total  = int(df["total"].iloc[0])
        unique = int(df["unique_ids"].iloc[0])
        dupes  = total - unique
        return self._result(total, dupes, f"{dupes:,} duplicate product_ids detected")
