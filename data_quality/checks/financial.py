"""Financial data quality checks — reconciliation and amount validation."""

from __future__ import annotations
from data_quality.checks.base import BaseCheck
from data_quality.models import Severity


class NoNegativeInventory(BaseCheck):
    check_id   = "fin_001"
    check_name = "No negative inventory closing_qty in raw"
    dataset    = "raw.raw_inventory"
    severity   = Severity.WARNING

    def _execute(self):
        df = self.db.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE closing_qty < 0) AS negatives "
            "FROM raw.raw_inventory"
        )
        total    = int(df["total"].iloc[0])
        negatives = int(df["negatives"].iloc[0])
        return self._result(total, negatives, f"{negatives:,} records with closing_qty < 0")


class RefundsNotExceedPayments(BaseCheck):
    check_id   = "fin_002"
    check_name = "Refunds do not exceed payments per order"
    dataset    = "main_marts.fct_refunds"
    severity   = Severity.CRITICAL

    def _execute(self):
        df = self.db.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE is_over_refund = true) AS over_refunds "
            "FROM main_marts.fct_refunds"
        )
        total       = int(df["total"].iloc[0])
        over_refunds = int(df["over_refunds"].iloc[0])
        return self._result(
            total, over_refunds,
            f"{over_refunds:,} refunds exceed total payment for that order"
        )


class PaymentReconciliationExceptions(BaseCheck):
    check_id   = "fin_003"
    check_name = "Payment reconciliation exceptions (|variance| > $100)"
    dataset    = "main_marts.fct_payments"
    severity   = Severity.CRITICAL

    def _execute(self):
        df = self.db.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE reconciliation_status = 'EXCEPTION') AS exceptions "
            "FROM main_marts.fct_payments"
        )
        total      = int(df["total"].iloc[0])
        exceptions = int(df["exceptions"].iloc[0])
        return self._result(
            total, exceptions,
            f"{exceptions:,} payments with reconciliation EXCEPTION (|variance| > $100)"
        )


class PaymentReconciliationWarnings(BaseCheck):
    check_id   = "fin_004"
    check_name = "Payment reconciliation warnings (|variance| $1-$100)"
    dataset    = "main_marts.fct_payments"
    severity   = Severity.WARNING

    def _execute(self):
        df = self.db.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE reconciliation_status = 'WARNING') AS warnings "
            "FROM main_marts.fct_payments"
        )
        total    = int(df["total"].iloc[0])
        warnings = int(df["warnings"].iloc[0])
        return self._result(
            total, warnings,
            f"{warnings:,} payments with reconciliation WARNING ($1–$100 variance)"
        )


class DuplicatePaymentCheck(BaseCheck):
    check_id   = "fin_005"
    check_name = "Orders with more than one completed payment"
    dataset    = "main_staging.stg_payments"
    severity   = Severity.CRITICAL

    def _execute(self):
        df = self.db.execute("""
            SELECT
                COUNT(DISTINCT order_id)                            AS total_orders,
                COUNT(DISTINCT order_id) FILTER (
                    WHERE cnt > 1
                )                                                   AS dup_orders
            FROM (
                SELECT order_id, COUNT(*) AS cnt
                FROM main_staging.stg_payments
                WHERE status = 'completed'
                GROUP BY order_id
            ) t
        """)
        total = int(df["total_orders"].iloc[0])
        dups  = int(df["dup_orders"].iloc[0])
        return self._result(total, dups, f"{dups:,} orders have duplicate completed payments")


class PayoutReconciliationExceptions(BaseCheck):
    check_id   = "fin_006"
    check_name = "Payout reconciliation exceptions"
    dataset    = "main_marts.fct_payouts"
    severity   = Severity.CRITICAL

    def _execute(self):
        df = self.db.execute(
            "SELECT COUNT(*) AS total, "
            "COUNT(*) FILTER (WHERE reconciliation_status = 'EXCEPTION') AS exceptions "
            "FROM main_marts.fct_payouts"
        )
        total      = int(df["total"].iloc[0])
        exceptions = int(df["exceptions"].iloc[0])
        return self._result(
            total, exceptions,
            f"{exceptions:,} payouts with EXCEPTION status"
        )
