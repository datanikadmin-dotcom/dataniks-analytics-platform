"""
DataNiks AI Analyst — core orchestration.

Flow for each user question:
  1. Detect intent (analytical / SQL / unknown)
  2. Check metric catalog relevance
  3. Generate SQL (via LLM with safety validation)
  4. Execute SQL against DuckDB
  5. Generate natural-language explanation (via LLM)
  6. Return structured AnalystResponse
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from ai.providers.base import BaseLLMProvider
from ai.providers.factory import get_provider
from ai.metrics.catalog import MetricCatalog
from ai.queries.validator import validate_sql, ValidationResult
from ai.prompts.system import (
    ANALYST_SYSTEM_PROMPT,
    SQL_GENERATION_SYSTEM_PROMPT,
    CANNOT_ANSWER_RESPONSE,
)

logger = logging.getLogger(__name__)


@dataclass
class AnalystResponse:
    question:    str
    answer:      str
    sql:         str          = ""
    data:        Any          = None   # pandas DataFrame or None
    row_count:   int          = 0
    tokens_used: int          = 0
    safe:        bool         = True
    error:       str          = ""
    metrics_detected: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "question":        self.question,
            "answer":          self.answer,
            "sql":             self.sql,
            "row_count":       self.row_count,
            "tokens_used":     self.tokens_used,
            "safe":            self.safe,
            "error":           self.error,
            "metrics_detected": self.metrics_detected,
        }


# Questions the assistant refuses regardless of intent
_BLOCKED_PATTERNS = [
    "drop table", "delete from", "truncate", "insert into",
    "update set", "alter table", "grant ", "revoke ",
    "ignore previous", "disregard your instructions",
    "you are now", "pretend you are", "act as",
]


class DataNiksAnalyst:
    """
    Orchestrates the full question → answer pipeline.

    Parameters
    ----------
    db       : DuckDBLoader (or BigQueryLoader in production)
    provider : BaseLLMProvider (default: auto-selected from env)
    catalog  : MetricCatalog (default: loaded from config/metrics.yaml)
    """

    def __init__(
        self,
        db: Any,
        provider: BaseLLMProvider | None = None,
        catalog: MetricCatalog | None = None,
    ) -> None:
        self.db       = db
        self.provider = provider or get_provider()
        self.catalog  = catalog  or MetricCatalog()
        logger.info(
            "[AI] Analyst initialised — provider=%s  model=%s",
            self.provider.provider_name, self.provider.model,
        )

    # ── Public entry point ────────────────────────────────────────────────────

    def ask(self, question: str) -> AnalystResponse:
        """Answer an analytical question end-to-end."""
        question = question.strip()
        logger.info("[AI] Question: %s", question)

        # ── Safety gate ───────────────────────────────────────────────────────
        if self._is_blocked(question):
            logger.warning("[AI] Blocked question: %s", question)
            return AnalystResponse(
                question=question,
                answer=(
                    "I cannot answer this question. It appears to contain instructions "
                    "that conflict with my operational guidelines. "
                    "Please ask a valid analytics question."
                ),
                safe=False,
            )

        # ── Metric detection ──────────────────────────────────────────────────
        relevant_metrics = self.catalog.detect_relevant(question)
        logger.info("[AI] Detected metrics: %s", relevant_metrics)

        # ── SQL generation ────────────────────────────────────────────────────
        sql, validation = self._generate_sql(question)
        df: pd.DataFrame | None = None
        row_count = 0

        if sql and validation.is_safe:
            try:
                df = self.db.execute(sql)
                row_count = len(df)
                logger.info("[AI] SQL returned %d rows", row_count)
            except Exception as exc:
                logger.error("[AI] SQL execution failed: %s", exc)
                df = None

        # ── Explanation generation ────────────────────────────────────────────
        answer, tokens = self._explain(question, sql, df, relevant_metrics)

        return AnalystResponse(
            question=question,
            answer=answer,
            sql=sql,
            data=df,
            row_count=row_count,
            tokens_used=tokens,
            safe=True,
            metrics_detected=relevant_metrics,
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _is_blocked(self, question: str) -> bool:
        q = question.lower()
        return any(pattern in q for pattern in _BLOCKED_PATTERNS)

    def _generate_sql(self, question: str) -> tuple[str, ValidationResult]:
        """Ask the LLM to generate SQL, then validate it."""
        try:
            response = self.provider.complete(
                system_prompt=SQL_GENERATION_SYSTEM_PROMPT,
                user_message=question,
                max_tokens=512,
                temperature=0.0,
            )
            raw_sql = response.content.strip().strip("`").strip()
            validation = validate_sql(raw_sql)
            if not validation.is_safe:
                logger.warning("[AI] SQL rejected: %s", validation.reason)
                return "", validation
            return raw_sql, validation
        except Exception as exc:
            logger.error("[AI] SQL generation failed: %s", exc)
            return "", ValidationResult(is_safe=False, reason=str(exc))

    def _explain(
        self,
        question: str,
        sql: str,
        df: pd.DataFrame | None,
        metrics: list[str],
    ) -> tuple[str, int]:
        """Ask the LLM to explain the results in business language."""
        # Build context for the explanation prompt
        data_summary = ""
        if df is not None and not df.empty:
            data_summary = f"\n\nQuery results (first 5 rows):\n{df.head(5).to_string(index=False)}"
            if len(df) > 5:
                data_summary += f"\n... ({len(df)} total rows)"

        user_msg = question
        if data_summary:
            user_msg += data_summary

        metric_catalog_text = self.catalog.summary_text()
        system = ANALYST_SYSTEM_PROMPT.format(metric_catalog=metric_catalog_text)

        try:
            response = self.provider.complete(
                system_prompt=system,
                user_message=user_msg,
                max_tokens=1024,
                temperature=0.0,
            )
            return response.content, response.tokens_in + response.tokens_out
        except Exception as exc:
            logger.error("[AI] Explanation generation failed: %s", exc)
            return CANNOT_ANSWER_RESPONSE, 0
