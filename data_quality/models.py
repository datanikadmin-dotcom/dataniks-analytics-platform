"""Data quality result data structures."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING  = "WARNING"
    INFO     = "INFO"


class CheckStatus(str, Enum):
    PASS    = "PASS"
    FAIL    = "FAIL"
    WARN    = "WARN"
    SKIPPED = "SKIPPED"
    ERROR   = "ERROR"


@dataclass
class CheckResult:
    check_id:        str
    check_name:      str
    dataset:         str
    severity:        Severity
    status:          CheckStatus
    records_checked: int
    records_failed:  int
    message:         str
    execution_time:  str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata:        dict[str, Any] = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        if self.records_checked == 0:
            return 1.0
        return 1.0 - (self.records_failed / self.records_checked)

    def to_dict(self) -> dict:
        return {
            "check_id":        self.check_id,
            "check_name":      self.check_name,
            "dataset":         self.dataset,
            "severity":        self.severity.value,
            "status":          self.status.value,
            "records_checked": self.records_checked,
            "records_failed":  self.records_failed,
            "pass_rate":       round(self.pass_rate, 4),
            "message":         self.message,
            "execution_time":  self.execution_time,
        }
