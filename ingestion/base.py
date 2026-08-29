"""
Abstract base connector.

Every source connector (mock or real) must implement this interface.
Swap `provider` in sources.yaml and the platform uses a different connector
without touching pipeline or transformation code.
"""

from __future__ import annotations
import abc
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Iterator

import pandas as pd

logger = logging.getLogger(__name__)


class ConnectorError(Exception):
    """Raised when a connector cannot fulfil a request."""


class BaseConnector(abc.ABC):
    """Abstract connector interface for all source systems."""

    source_name: str = "base"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self._authenticated = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def authenticate(self) -> None:
        """Establish authentication with the source system."""
        self._do_authenticate()
        self._authenticated = True
        logger.debug("[%s] authenticated", self.source_name)

    @abc.abstractmethod
    def _do_authenticate(self) -> None: ...

    def health_check(self) -> bool:
        """Return True if the source is reachable and responding."""
        try:
            return self._do_health_check()
        except Exception as exc:
            logger.warning("[%s] health-check failed: %s", self.source_name, exc)
            return False

    @abc.abstractmethod
    def _do_health_check(self) -> bool: ...

    # ── Data access ───────────────────────────────────────────────────────────
    # Connectors implement whichever methods their source exposes.
    # Unimplemented methods raise NotImplementedError — callers check capability.

    def get_customers(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        raise NotImplementedError(f"{self.source_name} does not expose customers")

    def get_products(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        raise NotImplementedError(f"{self.source_name} does not expose products")

    def get_orders(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        raise NotImplementedError(f"{self.source_name} does not expose orders")

    def get_order_items(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        raise NotImplementedError(f"{self.source_name} does not expose order_items")

    def get_payments(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        raise NotImplementedError(f"{self.source_name} does not expose payments")

    def get_refunds(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        raise NotImplementedError(f"{self.source_name} does not expose refunds")

    def get_inventory(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        raise NotImplementedError(f"{self.source_name} does not expose inventory")

    def get_shipments(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        raise NotImplementedError(f"{self.source_name} does not expose shipments")

    def get_ad_spend(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        raise NotImplementedError(f"{self.source_name} does not expose ad_spend")

    def get_payouts(self, since: datetime | None = None, **kw) -> Iterator[pd.DataFrame]:
        raise NotImplementedError(f"{self.source_name} does not expose payouts")

    # ── Metadata helpers ─────────────────────────────────────────────────────

    @staticmethod
    def add_ingestion_metadata(df: pd.DataFrame, source: str, batch_id: str) -> pd.DataFrame:
        """Attach standard ingestion metadata columns."""
        now = datetime.now(timezone.utc).isoformat()
        df = df.copy()
        df["_ingested_at"] = now
        df["_source"] = source
        df["_batch_id"] = batch_id
        df["_record_hash"] = df.apply(
            lambda row: hashlib.md5(
                json.dumps(row.to_dict(), default=str, sort_keys=True).encode()
            ).hexdigest(),
            axis=1,
        )
        return df

    @staticmethod
    def make_batch_id() -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
