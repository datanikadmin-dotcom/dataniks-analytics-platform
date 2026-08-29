"""
SQL safety validator — enforces read-only queries.

The AI assistant MUST NOT execute destructive SQL under any circumstances,
including attempts embedded in user questions ("ignore previous instructions").
"""

from __future__ import annotations
import re
from dataclasses import dataclass


# Any of these keywords at the statement level are forbidden
_FORBIDDEN_PATTERNS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bREPLACE\b",
    r"\bMERGE\b",
    r"\bCALL\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bATTACH\b",
    r"\bDETACH\b",
    r"\bCOPY\b",
    r"\bEXPORT\b",
    r"\bIMPORT\b",
]

_FORBIDDEN_RE = re.compile(
    "|".join(_FORBIDDEN_PATTERNS),
    re.IGNORECASE,
)


@dataclass
class ValidationResult:
    is_safe:  bool
    reason:   str = ""
    sql:      str = ""


def validate_sql(sql: str) -> ValidationResult:
    """
    Check that SQL is safe to execute (SELECT-only).

    Returns ValidationResult with is_safe=False and a reason if rejected.
    """
    if not sql or not sql.strip():
        return ValidationResult(is_safe=False, reason="Empty SQL statement", sql=sql)

    cleaned = sql.strip()

    # Must start with SELECT (after optional WITH for CTEs)
    first_keyword = re.match(r"^\s*(WITH|SELECT)\b", cleaned, re.IGNORECASE)
    if not first_keyword:
        return ValidationResult(
            is_safe=False,
            reason=(
                f"SQL must begin with SELECT (or WITH for CTEs). "
                f"Got: '{cleaned[:40]}…'"
            ),
            sql=sql,
        )

    # Scan for any forbidden operation anywhere in the statement
    match = _FORBIDDEN_RE.search(cleaned)
    if match:
        return ValidationResult(
            is_safe=False,
            reason=f"Forbidden operation detected: '{match.group()}' at position {match.start()}",
            sql=sql,
        )

    return ValidationResult(is_safe=True, sql=cleaned)
