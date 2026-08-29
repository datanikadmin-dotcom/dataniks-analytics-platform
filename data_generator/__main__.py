"""
Entry point:  python -m data_generator  [OPTIONS]

Generates the full NovaCommerce synthetic dataset and writes it to
data/synthetic/ (Parquet by default).
"""

from __future__ import annotations
import logging
import sys
import time
from pathlib import Path

import click

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from data_generator.config import GeneratorConfig
from data_generator.generators import customers, products, orders, inventory, advertising, payouts
from data_generator.corruption import apply as apply_corruption
from data_generator.writer import write


logging.basicConfig(
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--seed",              default=42,      show_default=True)
@click.option("--n-customers",       default=20_000,  show_default=True)
@click.option("--n-products",        default=2_000,   show_default=True)
@click.option("--n-orders",          default=100_000, show_default=True)
@click.option("--corrupt/--no-corrupt", default=True, show_default=True)
@click.option("--corruption-pct",    default=0.02,    show_default=True)
@click.option("--format", "fmt",     default="parquet",
              type=click.Choice(["parquet", "csv"]))
@click.option("--output-dir",        default="data/synthetic")
def generate(seed, n_customers, n_products, n_orders, corrupt, corruption_pct, fmt, output_dir):
    """Generate the NovaCommerce synthetic dataset."""
    t0 = time.perf_counter()

    cfg = GeneratorConfig(
        seed=seed,
        customers=n_customers,
        products=n_products,
        orders=n_orders,
        corruption_pct=corruption_pct,
        output_dir=output_dir,
        format=fmt,
    )

    logger.info("━━ DataNiks Synthetic Generator ━━")
    logger.info("  seed=%d  customers=%d  products=%d  orders=%d",
                seed, n_customers, n_products, n_orders)

    logger.info("── Generating customers …")
    customers_df = customers.generate(cfg)

    logger.info("── Generating products …")
    products_df = products.generate(cfg)

    logger.info("── Generating orders, payments, refunds, shipments …")
    order_datasets = orders.generate(cfg, customers_df, products_df)

    logger.info("── Generating inventory …")
    inventory_df = inventory.generate(cfg, products_df)

    logger.info("── Generating advertising …")
    advertising_df = advertising.generate(cfg)

    logger.info("── Generating payouts …")
    payouts_df = payouts.generate(cfg, order_datasets["orders"], order_datasets["refunds"])

    all_datasets = {
        "customers":   customers_df,
        "products":    products_df,
        **order_datasets,
        "inventory":   inventory_df,
        "advertising": advertising_df,
        "payouts":     payouts_df,
    }

    if corrupt:
        logger.info("── Applying data-quality corruption (%.1f %%) …", corruption_pct * 100)
        all_datasets, report = apply_corruption(all_datasets, cfg)
        logger.info(
            "   Corruption complete — %d records affected across %d defect types",
            report.total_records_affected, len(report.defects),
        )
    else:
        logger.info("── Corruption skipped (--no-corrupt)")

    logger.info("── Writing datasets …")
    write(all_datasets, cfg)

    elapsed = time.perf_counter() - t0
    logger.info("━━ Done in %.1f s ━━", elapsed)

    click.echo("\nDataset Summary:")
    click.echo(f"{'Dataset':<20} {'Rows':>10}")
    click.echo("─" * 32)
    for name, df in all_datasets.items():
        click.echo(f"{name:<20} {len(df):>10,}")


if __name__ == "__main__":
    generate()
