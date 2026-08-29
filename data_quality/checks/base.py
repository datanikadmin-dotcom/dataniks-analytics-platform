"""Abstract base class for all data quality checks."""

from __future__ import annotations
import abc
import logging
from typing import Any

from data_quality.models import CheckResult, CheckStatus, Severity

logger = logging.getLogger(__name__)


class BaseCheck(abc.ABC):
    check_id:   str = "base"
    check_name: str = "Base Check"
    dataset:    str = ""
    severity:   Severity = Severity.WARNING

    def __init__(self, db: Any, config: dict | None = None) -> None:
        self.db = db            # DuckDBLoader or BigQueryLoader
        self.config = config or {}

    def run(self) -> CheckResult:
        try:
            return self._execute()
        except Exception as exc:
            logger.error("[DQ] %s failed with exception: %s", self.check_id, exc)
            return CheckResult(
                check_id=self.check_id,
                check_name=self.check_name,
                dataset=self.dataset,
                severity=self.severity,
                status=CheckStatus.ERROR,
                records_checked=0,
                records_failed=0,
                message=f"Check raised exception: {exc}",
            )

    @abc.abstractmethod
    def _execute(self) -> CheckResult: ...

    def _result(
        self,
        records_checked: int,
        records_failed: int,
        message: str = "",
        metadata: dict | None = None,
    ) -> CheckResult:
        if records_checked == 0:
            status = CheckStatus.SKIPPED
        elif records_failed == 0:
            status = CheckStatus.PASS
        elif self.severity == Severity.WARNING:
            status = CheckStatus.WARN
        else:
            status = CheckStatus.FAIL

        return CheckResult(
            check_id=self.check_id,
            check_name=self.check_name,
            dataset=self.dataset,
            severity=self.severity,
            status=status,
            records_checked=records_checked,
            records_failed=records_failed,
            message=message or f"{records_failed:,} of {records_checked:,} records failed",
            metadata=metadata or {},
        )
