"""Write generated datasets to disk as Parquet or CSV."""

from __future__ import annotations
import logging
import os
from pathlib import Path

import pandas as pd

from data_generator.config import GeneratorConfig

logger = logging.getLogger(__name__)


def write(
    datasets: dict[str, pd.DataFrame],
    cfg: GeneratorConfig,
    subdir: str = "",
) -> dict[str, Path]:
    out_dir = Path(cfg.output_dir) / subdir if subdir else Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for name, df in datasets.items():
        if df.empty:
            logger.warning("  [writer] %s is empty — skipping", name)
            continue

        if cfg.format == "parquet":
            path = out_dir / f"{name}.parquet"
            df.to_parquet(path, index=False, engine="pyarrow")
        else:
            path = out_dir / f"{name}.csv"
            df.to_csv(path, index=False)

        written[name] = path
        logger.info("  [writer] %-20s  rows=%d  → %s", name, len(df), path)

    return written
