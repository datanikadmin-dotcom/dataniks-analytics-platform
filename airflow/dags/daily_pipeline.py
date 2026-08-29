"""
DataNiks Daily Pipeline DAG
============================
Orchestrates the full ELT pipeline on a daily schedule.

Execution order:
  1. Extract from all source connectors in parallel
  2. Load raw → DuckDB / BigQuery
  3. dbt staging (views)
  4. dbt intermediate (views)
  5. dbt marts (tables)
  6. Data quality checks
  7. On failure → alert; on success → notify

Idempotent: each run drops and reloads raw tables, making it safe to re-run.
Backfill: set `start_date` and trigger with `--reset-dagruns` for historical loads.
"""

from __future__ import annotations
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

# Make the repo root importable inside the Airflow worker
_PLATFORM_ROOT = os.getenv("PLATFORM_ROOT", "/opt/platform")
sys.path.insert(0, _PLATFORM_ROOT)

# ── Default args ───────────────────────────────────────────────────────────────

default_args = {
    "owner":            "dataniks",
    "depends_on_past":  False,
    "email_on_failure": False,
    "email_on_retry":   False,
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
}

# ── Python callables ───────────────────────────────────────────────────────────

def _extract_and_load(**ctx):
    """Run the full ingestion pipeline for the execution date."""
    from ingestion.pipeline import run_full_pipeline
    totals = run_full_pipeline(drop_first=True)
    ctx["ti"].xcom_push(key="ingestion_totals", value=totals)
    return totals


def _run_dbt_staging(**ctx):
    import subprocess
    dbt_dir = Path(_PLATFORM_ROOT) / "dbt"
    result = subprocess.run(
        ["dbt", "run", "--select", "staging", "--profiles-dir", "."],
        cwd=dbt_dir, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"dbt staging failed:\n{result.stdout}\n{result.stderr}")
    return result.stdout


def _run_dbt_intermediate(**ctx):
    import subprocess
    dbt_dir = Path(_PLATFORM_ROOT) / "dbt"
    result = subprocess.run(
        ["dbt", "run", "--select", "intermediate", "--profiles-dir", "."],
        cwd=dbt_dir, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"dbt intermediate failed:\n{result.stdout}\n{result.stderr}")
    return result.stdout


def _run_dbt_marts(**ctx):
    import subprocess
    dbt_dir = Path(_PLATFORM_ROOT) / "dbt"
    result = subprocess.run(
        ["dbt", "run", "--select", "marts", "--profiles-dir", "."],
        cwd=dbt_dir, capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"dbt marts failed:\n{result.stdout}\n{result.stderr}")
    return result.stdout


def _run_dbt_tests(**ctx):
    import subprocess
    dbt_dir = Path(_PLATFORM_ROOT) / "dbt"
    result = subprocess.run(
        ["dbt", "test", "--profiles-dir", "."],
        cwd=dbt_dir, capture_output=True, text=True,
    )
    # dbt test warns are OK; errors fail the task
    if result.returncode != 0 and "ERROR" in result.stdout:
        raise RuntimeError(f"dbt tests failed:\n{result.stdout}")
    return result.stdout


def _run_data_quality(**ctx):
    from ingestion.loaders.duckdb_loader import DuckDBLoader
    from data_quality.engine import DataQualityEngine

    db_path = os.getenv("DUCKDB_PATH", "data/warehouse.duckdb")
    loader = DuckDBLoader(db_path=db_path)
    engine = DataQualityEngine(db=loader)
    results = engine.run_all()
    report_path = engine.save_report(results)
    ctx["ti"].xcom_push(key="dq_report", value=str(report_path))
    ctx["ti"].xcom_push(key="has_critical", value=engine.has_critical_failures(results))
    return str(report_path)


def _branch_on_quality(**ctx):
    has_critical = ctx["ti"].xcom_pull(task_ids="data_quality", key="has_critical")
    if has_critical:
        return "alert_critical_failure"
    return "pipeline_success"


def _alert_critical_failure(**ctx):
    report = ctx["ti"].xcom_pull(task_ids="data_quality", key="dq_report")
    # In production: send Slack/email notification
    print(f"[ALERT] Critical data quality failures detected. Report: {report}")
    # Raise to fail the DAG so oncall is paged
    raise RuntimeError("Critical data quality failures — pipeline blocked")


# ── DAG definition ─────────────────────────────────────────────────────────────

with DAG(
    dag_id="novacommerce_daily_pipeline",
    description="NovaCommerce: daily ELT pipeline — ingest, transform, quality",
    default_args=default_args,
    schedule_interval="0 6 * * *",     # 06:00 UTC daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["dataniks", "novacommerce", "elt"],
) as dag:

    start = EmptyOperator(task_id="start")

    extract_and_load = PythonOperator(
        task_id="extract_and_load",
        python_callable=_extract_and_load,
    )

    dbt_staging = PythonOperator(
        task_id="dbt_staging",
        python_callable=_run_dbt_staging,
    )

    dbt_intermediate = PythonOperator(
        task_id="dbt_intermediate",
        python_callable=_run_dbt_intermediate,
    )

    dbt_marts = PythonOperator(
        task_id="dbt_marts",
        python_callable=_run_dbt_marts,
    )

    dbt_tests = PythonOperator(
        task_id="dbt_tests",
        python_callable=_run_dbt_tests,
    )

    data_quality = PythonOperator(
        task_id="data_quality",
        python_callable=_run_data_quality,
    )

    branch = BranchPythonOperator(
        task_id="branch_on_quality",
        python_callable=_branch_on_quality,
    )

    pipeline_success = EmptyOperator(task_id="pipeline_success")

    alert = PythonOperator(
        task_id="alert_critical_failure",
        python_callable=_alert_critical_failure,
        trigger_rule=TriggerRule.ONE_SUCCESS,
    )

    end = EmptyOperator(
        task_id="end",
        trigger_rule=TriggerRule.ONE_SUCCESS,
    )

    # ── Dependencies ───────────────────────────────────────────────────────────
    (
        start
        >> extract_and_load
        >> dbt_staging
        >> dbt_intermediate
        >> dbt_marts
        >> dbt_tests
        >> data_quality
        >> branch
        >> [pipeline_success, alert]
    )
    pipeline_success >> end
    alert            >> end
