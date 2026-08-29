"""CLI entry point: python -m data_quality"""

from __future__ import annotations
import json
import logging
import os
import sys
from pathlib import Path

import click

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from ingestion.loaders.duckdb_loader import DuckDBLoader
from data_quality.engine import DataQualityEngine

logging.basicConfig(
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)


@click.command()
@click.option("--db",       default="data/warehouse.duckdb", show_default=True)
@click.option("--out-dir",  default="data_quality/reports",  show_default=True)
@click.option("--fail-on-critical/--no-fail-on-critical", default=True)
def main(db, out_dir, fail_on_critical):
    """Run all data quality checks and write a JSON report."""
    loader = DuckDBLoader(db_path=db)
    engine = DataQualityEngine(db=loader)

    results = engine.run_all()
    report_path = engine.save_report(results, output_dir=out_dir)

    # Pretty summary table
    click.echo("\n┌─────────────────────────────────────────────────────────────────────┐")
    click.echo("│  DataNiks Data Quality Report                                       │")
    click.echo("├────────────┬──────────────────────────────────────────┬─────────────┤")
    click.echo("│  Status    │  Check                                   │  Failed     │")
    click.echo("├────────────┼──────────────────────────────────────────┼─────────────┤")
    for r in results:
        status_label = f"[{r.status.value:<7}]"
        name = r.check_name[:42].ljust(42)
        fail_info = f"{r.records_failed:>6,}/{r.records_checked:<8,}"
        click.echo(f"│  {status_label}  │  {name}  │  {fail_info}  │")
    click.echo("└────────────┴──────────────────────────────────────────┴─────────────┘")
    click.echo(f"\nReport saved: {report_path}")

    if fail_on_critical and engine.has_critical_failures(results):
        click.echo("\n[CRITICAL] One or more critical checks failed — pipeline blocked.", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
