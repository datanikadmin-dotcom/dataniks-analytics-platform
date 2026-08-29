"""Referential integrity checks — detect orphan records."""

from __future__ import annotations
from data_quality.checks.base import BaseCheck
from data_quality.models import Severity


class OrderItemsHaveOrders(BaseCheck):
    check_id   = "ref_001"
    check_name = "Order items reference valid orders"
    dataset    = "main_staging.stg_order_items"
    severity   = Severity.CRITICAL

    def _execute(self):
        df = self.db.execute("""
            SELECT
                COUNT(*)                                                  AS total,
                COUNT(*) FILTER (
                    WHERE order_id NOT IN (
                        SELECT order_id FROM main_staging.stg_orders
                    )
                )                                                         AS orphans
            FROM main_staging.stg_order_items
        """)
        total   = int(df["total"].iloc[0])
        orphans = int(df["orphans"].iloc[0])
        return self._result(total, orphans, f"{orphans:,} order items with no matching order")


class PaymentsHaveOrders(BaseCheck):
    check_id   = "ref_002"
    check_name = "Payments reference valid orders"
    dataset    = "main_staging.stg_payments"
    severity   = Severity.WARNING

    def _execute(self):
        df = self.db.execute("""
            SELECT
                COUNT(*)                                                  AS total,
                COUNT(*) FILTER (
                    WHERE order_id NOT IN (
                        SELECT order_id FROM main_staging.stg_orders
                    )
                )                                                         AS orphans
            FROM main_staging.stg_payments
        """)
        total   = int(df["total"].iloc[0])
        orphans = int(df["orphans"].iloc[0])
        return self._result(total, orphans, f"{orphans:,} payments with no matching order")


class RefundsHaveOrders(BaseCheck):
    check_id   = "ref_003"
    check_name = "Refunds reference valid orders"
    dataset    = "main_staging.stg_refunds"
    severity   = Severity.WARNING

    def _execute(self):
        df = self.db.execute("""
            SELECT
                COUNT(*)                                                  AS total,
                COUNT(*) FILTER (
                    WHERE order_id NOT IN (
                        SELECT order_id FROM main_staging.stg_orders
                    )
                )                                                         AS orphans
            FROM main_staging.stg_refunds
        """)
        total   = int(df["total"].iloc[0])
        orphans = int(df["orphans"].iloc[0])
        return self._result(total, orphans, f"{orphans:,} refunds with no matching order")


class ShipmentsHaveOrders(BaseCheck):
    check_id   = "ref_004"
    check_name = "Shipments reference valid orders"
    dataset    = "main_staging.stg_shipments"
    severity   = Severity.WARNING

    def _execute(self):
        df = self.db.execute("""
            SELECT
                COUNT(*)                                                  AS total,
                COUNT(*) FILTER (
                    WHERE order_id NOT IN (
                        SELECT order_id FROM main_staging.stg_orders
                    )
                )                                                         AS orphans
            FROM main_staging.stg_shipments
        """)
        total   = int(df["total"].iloc[0])
        orphans = int(df["orphans"].iloc[0])
        return self._result(total, orphans, f"{orphans:,} shipments with no matching order")
