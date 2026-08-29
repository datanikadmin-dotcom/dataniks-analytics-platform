"""
Data quality engine — discovers and runs all registered checks.
"""

from __future__ import annotations
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from data_quality.models import CheckResult, CheckStatus, Severity
from data_quality.checks.uniqueness import (
    UniqueOrderIds, UniqueCustomerIds, UniquePaymentIds, UniqueProductIds,
)
from data_quality.checks.referential import (
    OrderItemsHaveOrders, PaymentsHaveOrders, RefundsHaveOrders, ShipmentsHaveOrders,
)
from data_quality.checks.financial import (
    NoNegativeInventory, RefundsNotExceedPayments,
    PaymentReconciliationExceptions, PaymentReconciliationWarnings,
    DuplicatePaymentCheck, PayoutReconciliationExceptions,
)
from data_quality.checks.completeness import (
    CustomerEmailCompleteness, ProductSkuCompleteness,
    OrderStatusValidity, MinimumOrderVolume,
)

logger = logging.getLogger(__name__)

_ALL_CHECKS = [
    # Uniqueness
    UniqueOrderIds,
    UniqueCustomerIds,
    UniquePaymentIds,
    UniqueProductIds,
    # Referential integrity
    OrderItemsHaveOrders,
    PaymentsHaveOrders,
    RefundsHaveOrders,
    ShipmentsHaveOrders,
    # Financial
    NoNegativeInventory,
    RefundsNotExceedPayments,
    PaymentReconciliationExceptions,
    PaymentReconciliationWarnings,
    DuplicatePaymentCheck,
    PayoutReconciliationExceptions,
    # Completeness
    CustomerEmailCompleteness,
    ProductSkuCompleteness,
    OrderStatusValidity,
    MinimumOrderVolume,
]


class DataQualityEngine:

    def __init__(self, db: Any) -> None:
        self.db = db

    def run_all(self) -> list[CheckResult]:
        results: list[CheckResult] = []
        logger.info("── Running %d data quality checks ──", len(_ALL_CHECKS))
        t0 = time.perf_counter()

        for check_cls in _ALL_CHECKS:
            check = check_cls(db=self.db)
            result = check.run()
            results.append(result)

            icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠", "SKIPPED": "–", "ERROR": "!"}.get(
                result.status.value, "?"
            )
            logger.info(
                "  [%s] %-45s  failed=%d/%d",
                result.status.value,
                result.check_name[:45],
                result.records_failed,
                result.records_checked,
            )

        elapsed = time.perf_counter() - t0
        passed   = sum(1 for r in results if r.status == CheckStatus.PASS)
        failed   = sum(1 for r in results if r.status == CheckStatus.FAIL)
        warned   = sum(1 for r in results if r.status == CheckStatus.WARN)
        errored  = sum(1 for r in results if r.status == CheckStatus.ERROR)
        critical = sum(
            1 for r in results
            if r.status in (CheckStatus.FAIL, CheckStatus.ERROR)
            and r.severity == Severity.CRITICAL
        )

        logger.info(
            "── Complete in %.2fs — PASS=%d WARN=%d FAIL=%d ERROR=%d CRITICAL=%d ──",
            elapsed, passed, warned, failed, errored, critical,
        )
        return results

    def save_report(self, results: list[CheckResult], output_dir: str = "data_quality/reports") -> Path:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = Path(output_dir) / f"dq_report_{ts}.json"

        summary = {
            "run_at":         ts,
            "total_checks":   len(results),
            "passed":         sum(1 for r in results if r.status == CheckStatus.PASS),
            "warned":         sum(1 for r in results if r.status == CheckStatus.WARN),
            "failed":         sum(1 for r in results if r.status == CheckStatus.FAIL),
            "errored":        sum(1 for r in results if r.status == CheckStatus.ERROR),
            "critical_issues": sum(
                1 for r in results
                if r.status in (CheckStatus.FAIL, CheckStatus.ERROR)
                and r.severity == Severity.CRITICAL
            ),
            "checks": [r.to_dict() for r in results],
        }

        with open(path, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("[DQ] Report written → %s", path)
        return path

    def has_critical_failures(self, results: list[CheckResult]) -> bool:
        return any(
            r.status in (CheckStatus.FAIL, CheckStatus.ERROR)
            and r.severity == Severity.CRITICAL
            for r in results
        )
