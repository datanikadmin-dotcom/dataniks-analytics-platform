"""Tests for the ingestion connector framework."""

from __future__ import annotations
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingestion.base import BaseConnector
from ingestion.extractors.mock import MockConnector
from ingestion import get_connector


_DATA_DIR = "data/synthetic"


@pytest.fixture
def mock_connector():
    return MockConnector(source="test", config={"data_dir": _DATA_DIR, "batch_size": 100})


class TestBaseConnector:
    def test_abstract_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseConnector({})  # abstract class

    def test_ingestion_metadata_columns(self):
        df = pd.DataFrame({"id": [1, 2], "val": ["a", "b"]})
        result = BaseConnector.add_ingestion_metadata(df, "test_source", "BATCH001")
        assert "_ingested_at" in result.columns
        assert "_source" in result.columns
        assert "_batch_id" in result.columns
        assert "_record_hash" in result.columns
        assert (result["_source"] == "test_source").all()
        assert (result["_batch_id"] == "BATCH001").all()

    def test_record_hash_is_unique(self):
        df = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})
        result = BaseConnector.add_ingestion_metadata(df, "src", "b1")
        assert result["_record_hash"].is_unique


class TestMockConnector:
    def test_health_check_true(self, mock_connector):
        mock_connector.authenticate()
        assert mock_connector.health_check() is True

    def test_health_check_false_bad_dir(self):
        c = MockConnector(source="test", config={"data_dir": "/nonexistent/path"})
        assert c.health_check() is False

    def test_authenticate_fails_bad_dir(self):
        from ingestion.base import ConnectorError
        c = MockConnector(source="test", config={"data_dir": "/nonexistent"})
        with pytest.raises(ConnectorError):
            c.authenticate()

    def test_get_customers_returns_batches(self, mock_connector):
        mock_connector.authenticate()
        batches = list(mock_connector.get_customers())
        assert len(batches) > 0
        df = pd.concat(batches, ignore_index=True)
        assert "customer_id" in df.columns
        assert "_ingested_at" in df.columns
        assert len(df) == 20_000

    def test_get_products_batch_size_respected(self, mock_connector):
        mock_connector.authenticate()
        for batch in mock_connector.get_products():
            assert len(batch) <= mock_connector._batch_size

    def test_get_orders_returns_metadata(self, mock_connector):
        mock_connector.authenticate()
        first_batch = next(mock_connector.get_orders())
        assert "_source" in first_batch.columns
        assert "_batch_id" in first_batch.columns

    def test_all_entities_accessible(self, mock_connector):
        mock_connector.authenticate()
        entities = [
            mock_connector.get_customers,
            mock_connector.get_products,
            mock_connector.get_orders,
            mock_connector.get_payments,
            mock_connector.get_refunds,
            mock_connector.get_inventory,
            mock_connector.get_shipments,
            mock_connector.get_ad_spend,
            mock_connector.get_payouts,
        ]
        for method in entities:
            batch = next(method())
            assert isinstance(batch, pd.DataFrame)
            assert not batch.empty


class TestConnectorFactory:
    def test_get_mock_connector(self):
        c = get_connector("commerce", "mock", {"data_dir": _DATA_DIR})
        assert isinstance(c, MockConnector)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_connector("commerce", "unknown_xyz", {})

    def test_shopify_not_implemented(self):
        with pytest.raises(NotImplementedError):
            get_connector("commerce", "shopify", {})
