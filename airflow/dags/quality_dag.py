"""
Standalone data quality DAG — can run independently of the main pipeline.
Useful for ad-hoc validation or running quality checks more frequently.
"""

from __future__ import annotations
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

_PLATFORM_ROOT = os.getenv("PLATFORM_ROOT", "/opt/platform")
sys.path.insert(0, _PLATFORM_ROOT)

default_args = {
    "owner":           "dataniks",
    "retries":         1,
    "retry_delay":     timedelta(minutes=2),
    "email_on_failure": False,
}


def _run_quality_checks(**ctx):
    from ingestion.loaders.duckdb_loader import DuckDBLoader
    from data_quality.engine import DataQualityEngine

    db_path = os.getenv("DUCKDB_PATH", "data/warehouse.duckdb")
    loader  = DuckDBLoader(db_path=db_path)
    engine  = DataQualityEngine(db=loader)
    results = engine.run_all()
    engine.save_report(results)

    summary = {
        "passed":  sum(1 for r in results if r.status.value == "PASS"),
        "warned":  sum(1 for r in results if r.status.value == "WARN"),
        "failed":  sum(1 for r in results if r.status.value == "FAIL"),
        "critical": engine.has_critical_failures(results),
    }
    ctx["ti"].xcom_push(key="summary", value=summary)

    if summary["critical"]:
        raise RuntimeError(f"Critical DQ failures: {summary}")

    return summary


with DAG(
    dag_id="novacommerce_data_quality",
    description="NovaCommerce: standalone data quality check run",
    default_args=default_args,
    schedule_interval="0 */6 * * *",  # every 6 hours
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["dataniks", "data-quality"],
) as dag:

    start     = EmptyOperator(task_id="start")
    run_checks = PythonOperator(task_id="run_quality_checks", python_callable=_run_quality_checks)
    end        = EmptyOperator(task_id="end")

    start >> run_checks >> end
