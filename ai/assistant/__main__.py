"""
CLI for the DataNiks AI Analyst.

Usage:
    python -m ai.assistant
    python -m ai.assistant --question "Why did revenue fall last month?"
"""

from __future__ import annotations
import logging
import os
import sys
from pathlib import Path

import click

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from ingestion.loaders.duckdb_loader import DuckDBLoader
from ai.assistant.core import DataNiksAnalyst
from ai.providers.factory import get_provider

logging.basicConfig(level=logging.WARNING)   # quiet in interactive mode


_EXAMPLE_QUESTIONS = [
    "Why did revenue decrease last month?",
    "Which products have the highest gross margin?",
    "Which marketing channel has the best ROAS?",
    "Which customers have the highest lifetime value?",
    "Which products are at risk of going out of stock?",
    "Are payments reconciling with revenue?",
    "Which campaigns generated the most revenue?",
    "What caused the increase in refunds?",
    "Which warehouses have the most shipment delays?",
    "What changed compared with last month?",
]


@click.command()
@click.option("--question", "-q", default=None, help="Ask a single question and exit")
@click.option("--db",       default="data/warehouse.duckdb", show_default=True)
@click.option("--provider", default=None, help="Override AI_PROVIDER env var")
def main(question, db, provider):
    """DataNiks AI Analyst — ask questions about your analytics data."""
    if provider:
        os.environ["AI_PROVIDER"] = provider

    loader   = DuckDBLoader(db_path=db)
    analyst  = DataNiksAnalyst(db=loader)

    click.echo("\n╔══════════════════════════════════════════════════╗")
    click.echo("║    DataNiks AI Analyst  (provider: " + analyst.provider.provider_name.ljust(12) + ")  ║")
    click.echo("╚══════════════════════════════════════════════════╝\n")

    if question:
        _ask_and_print(analyst, question)
        return

    # Interactive REPL
    click.echo("Example questions:")
    for i, q in enumerate(_EXAMPLE_QUESTIONS[:5], 1):
        click.echo(f"  {i}. {q}")
    click.echo("\nType 'quit' or 'exit' to leave.\n")

    while True:
        try:
            q = click.prompt("You")
        except (EOFError, KeyboardInterrupt):
            click.echo("\nGoodbye.")
            break
        if q.lower() in ("quit", "exit", "q"):
            click.echo("Goodbye.")
            break
        _ask_and_print(analyst, q)


def _ask_and_print(analyst: DataNiksAnalyst, question: str) -> None:
    response = analyst.ask(question)

    click.echo(f"\n{'─' * 60}")
    if not response.safe:
        click.echo(f"[BLOCKED] {response.answer}", err=True)
    else:
        click.echo(f"Analyst: {response.answer}")
        if response.sql:
            click.echo(f"\n[SQL]\n{response.sql}")
        if response.row_count:
            click.echo(f"\n[Data: {response.row_count} rows returned]")
    click.echo()


if __name__ == "__main__":
    main()
