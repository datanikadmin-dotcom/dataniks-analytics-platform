"""DataNiks ingestion layer — connector factory and public API."""

from __future__ import annotations
from typing import Any

from ingestion.base import BaseConnector


def get_connector(source: str, provider: str, config: dict[str, Any]) -> BaseConnector:
    """
    Factory function — return the correct connector for a source/provider pair.

    Adding a new real connector requires only:
      1. Creating ingestion/extractors/<provider>.py
      2. Adding the import below.
    """
    provider = provider.lower()

    if provider == "mock":
        from ingestion.extractors.mock import MockConnector
        return MockConnector(source=source, config=config)

    # ── Real connectors (not yet implemented — document the extension point) ──
    if provider == "shopify":
        raise NotImplementedError(
            "Shopify connector not yet implemented. "
            "Create ingestion/extractors/shopify.py implementing BaseConnector."
        )
    if provider == "stripe":
        raise NotImplementedError("Stripe connector not yet implemented.")
    if provider == "hubspot":
        raise NotImplementedError("HubSpot connector not yet implemented.")
    if provider == "google_ads":
        raise NotImplementedError("Google Ads connector not yet implemented.")
    if provider == "meta_ads":
        raise NotImplementedError("Meta Ads connector not yet implemented.")

    raise ValueError(f"Unknown provider '{provider}' for source '{source}'")
