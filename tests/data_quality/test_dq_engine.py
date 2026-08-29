"""Tests for the data quality framework."""

from __future__ import annotations
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ingestion.loaders.duckdb_loader import DuckDBLoader
from data_quality.engine import DataQualityEngine
from data_quality.models import CheckStatus, Severity


_DB = "data/warehouse.duckdb"


@pytest.fixture(scope="module")
def loader():
    return DuckDBLoader(db_path=_DB)


@pytest.fixture(scope="module")
def engine(loader):
    return DataQualityEngine(db=loader)


@pytest.fixture(scope="module")
def results(engine):
    return engine.run_all()


class TestDQEngine:
    def test_runs_all_checks(self, results):
        assert len(results) == 18  # total registered checks

    def test_no_error_status(self, results):
        errored = [r for r in results if r.status == CheckStatus.ERROR]
        assert errored == [], f"Checks errored: {[r.check_id for r in errored]}"

    def test_pass_rate_in_range(self, results):
        for r in results:
            assert 0.0 <= r.pass_rate <= 1.0

    def test_known_passes(self, results):
        # Staging deduplication should produce unique IDs
        check = next(r for r in results if r.check_id == "uniq_001")
        assert check.status == CheckStatus.PASS
        assert check.records_failed == 0

    def test_known_fails(self, results):
        # Corruption injected over-refunds — this MUST fail
        check = next(r for r in results if r.check_id == "fin_002")
        assert check.status in (CheckStatus.FAIL, CheckStatus.WARN)
        assert check.records_failed > 0

    def test_known_warns(self, results):
        # Orphan payments from corruption — WARN severity
        check = next(r for r in results if r.check_id == "ref_002")
        assert check.status in (CheckStatus.WARN, CheckStatus.FAIL)
        assert check.records_failed > 0

    def test_has_critical_failures(self, engine, results):
        # Over-refunds and recon exceptions are CRITICAL — must be detected
        assert engine.has_critical_failures(results) is True

    def test_report_written(self, engine, results, tmp_path):
        report_path = engine.save_report(results, output_dir=str(tmp_path))
        assert report_path.exists()
        import json
        report = json.loads(report_path.read_text())
        assert "summary" not in report   # flat structure, not nested
        assert "checks" in report
        assert len(report["checks"]) == len(results)

    def test_check_result_to_dict(self, results):
        for r in results:
            d = r.to_dict()
            assert "check_id" in d
            assert "status" in d
            assert "records_failed" in d
            assert "pass_rate" in d


class TestIndividualChecks:
    def test_unique_order_ids_passes(self, loader):
        from data_quality.checks.uniqueness import UniqueOrderIds
        check = UniqueOrderIds(db=loader)
        result = check.run()
        assert result.status == CheckStatus.PASS

    def test_refund_exceed_check_detects_corruption(self, loader):
        from data_quality.checks.financial import RefundsNotExceedPayments
        check = RefundsNotExceedPayments(db=loader)
        result = check.run()
        assert result.records_failed > 0

    def test_negative_inventory_detected(self, loader):
        from data_quality.checks.financial import NoNegativeInventory
        check = NoNegativeInventory(db=loader)
        result = check.run()
        assert result.records_failed > 0

    def test_staging_email_completeness_passes(self, loader):
        # Staging model filters out null emails
        from data_quality.checks.completeness import CustomerEmailCompleteness
        check = CustomerEmailCompleteness(db=loader)
        result = check.run()
        assert result.records_failed == 0
