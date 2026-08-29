"""
DuckDB raw-layer loader.

In development this replaces BigQuery as the warehouse.
Schema: raw_<entity> tables mirror the BigQuery raw dataset.
"""

from __future__ import annotations
import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)

_DEFAULT_DB = os.getenv("DUCKDB_PATH", "data/warehouse.duckdb")


@contextmanager
def _conn(db_path: str) -> Iterator[duckdb.DuckDBPyConnection]:
    con = duckdb.connect(db_path)
    try:
        yield con
    finally:
        con.close()


class DuckDBLoader:
    """Loads DataFrames into DuckDB raw schema tables."""

    def __init__(self, db_path: str = _DEFAULT_DB) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def load(self, df: pd.DataFrame, table: str, schema: str = "raw") -> int:
        """
        Append a DataFrame to raw.<table>.
        Creates the table on first load via CREATE TABLE IF NOT EXISTS.
        Returns the number of rows written.
        """
        full_table = f"{schema}.{table}"
        with _conn(self.db_path) as con:
            con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            # DuckDB can infer schema from DataFrame
            con.execute(f"CREATE TABLE IF NOT EXISTS {full_table} AS SELECT * FROM df WHERE 1=0")
            con.execute(f"INSERT INTO {full_table} SELECT * FROM df")
            count = con.execute(f"SELECT COUNT(*) FROM {full_table}").fetchone()[0]
        logger.debug("[duckdb] loaded %d rows → %s", len(df), full_table)
        return len(df)

    def table_count(self, table: str, schema: str = "raw") -> int:
        with _conn(self.db_path) as con:
            result = con.execute(
                f"SELECT COUNT(*) FROM information_schema.tables "
                f"WHERE table_schema='{schema}' AND table_name='{table}'"
            ).fetchone()
            if not result or result[0] == 0:
                return 0
            return con.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]

    def drop_schema(self, schema: str = "raw") -> None:
        """Drop and recreate schema — use for full reloads."""
        with _conn(self.db_path) as con:
            con.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
            con.execute(f"CREATE SCHEMA {schema}")
        logger.info("[duckdb] schema '%s' reset", schema)

    def execute(self, sql: str) -> pd.DataFrame:
        """Run arbitrary read-only SQL and return results as DataFrame."""
        with _conn(self.db_path) as con:
            return con.execute(sql).df()
