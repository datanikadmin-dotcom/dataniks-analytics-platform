"""Completeness checks — required fields, volumes, freshness."""

from __future__ import annotations
from data_quality.checks.base import BaseCheck
from data_quality.models import Severity


class CustomerEmailCompleteness(BaseCheck):
    check_id   = "comp_001"
    check_name = "Customer emails present (staging — after null removal)"
    dataset    = "main_staging.stg_customers"
    severity   = Severity.WARNING

    def _execute(self):
        df = self.db.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE email IS NULL) AS nulls "
            "FROM main_staging.stg_customers"
        )
        total = int(df["total"].iloc[0])
        nulls = int(df["nulls"].iloc[0])
        return self._result(total, nulls, f"{nulls:,} customers still have null email after staging")


class ProductSkuCompleteness(BaseCheck):
    check_id   = "comp_002"
    check_name = "Product SKUs are present"
    dataset    = "main_staging.stg_products"
    severity   = Severity.WARNING

    def _execute(self):
        df = self.db.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE sku IS NULL OR trim(sku) = '') AS nulls "
            "FROM main_staging.stg_products"
        )
        total = int(df["total"].iloc[0])
        nulls = int(df["nulls"].iloc[0])
        return self._result(total, nulls, f"{nulls:,} products missing SKU")


class OrderStatusValidity(BaseCheck):
    check_id   = "comp_003"
    check_name = "Orders with invalid status absorbed as 'unknown'"
    dataset    = "main_staging.stg_orders"
    severity   = Severity.INFO

    def _execute(self):
        df = self.db.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE order_status = 'unknown') AS unknowns "
            "FROM main_staging.stg_orders"
        )
        total    = int(df["total"].iloc[0])
        unknowns = int(df["unknowns"].iloc[0])
        return self._result(
            total, unknowns,
            f"{unknowns:,} orders have status='unknown' (normalised from invalid raw values)"
        )


class MinimumOrderVolume(BaseCheck):
    """Alert if daily orders are significantly below average — may indicate ingestion failure."""
    check_id   = "comp_004"
    check_name = "Minimum daily order volume (anomaly detection)"
    dataset    = "main_staging.stg_orders"
    severity   = Severity.WARNING
    threshold_pct: float = 0.30   # alert if a day is >30% below avg

    def _execute(self):
        df = self.db.execute("""
            WITH daily AS (
                SELECT order_date, COUNT(*) AS n
                FROM main_staging.stg_orders
                GROUP BY order_date
            ),
            stats AS (
                SELECT AVG(n) AS avg_n, STDDEV(n) AS std_n FROM daily
            )
            SELECT
                COUNT(*)                                        AS total_days,
                COUNT(*) FILTER (
                    WHERE n < (SELECT avg_n * 0.70 FROM stats)
                )                                               AS low_days,
                (SELECT avg_n FROM stats)                       AS avg_daily_orders
            FROM daily
        """)
        total    = int(df["total_days"].iloc[0])
        low_days = int(df["low_days"].iloc[0])
        avg      = float(df["avg_daily_orders"].iloc[0] or 0)
        return self._result(
            total, low_days,
            f"{low_days:,} days >30% below average daily orders ({avg:.0f})"
        )
