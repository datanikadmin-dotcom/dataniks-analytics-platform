"""
BigQuery raw-layer loader — production replacement for DuckDBLoader.

Requires:
  pip install google-cloud-bigquery db-dtypes
  GOOGLE_APPLICATION_CREDENTIALS or Workload Identity configured.

Usage:
  Swap DuckDBLoader for BigQueryLoader in the pipeline when warehouse.provider = bigquery.
"""

from __future__ import annotations
import logging
import os
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BigQueryLoader:
    """Loads DataFrames into BigQuery raw dataset tables."""

    def __init__(
        self,
        project: str | None = None,
        dataset: str | None = None,
        location: str = "US",
    ) -> None:
        self.project = project or os.environ["GCP_PROJECT_ID"]
        self.dataset = dataset or os.environ["BQ_DATASET_RAW"]
        self.location = location
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                from google.cloud import bigquery  # noqa: PLC0415
                self._client = bigquery.Client(project=self.project)
            except ImportError:
                raise RuntimeError(
                    "google-cloud-bigquery is not installed. "
                    "Run: pip install google-cloud-bigquery db-dtypes"
                )
        return self._client

    def load(self, df: pd.DataFrame, table: str, schema: str = "raw") -> int:
        """Append DataFrame to BigQuery <dataset>.<table>."""
        from google.cloud.bigquery import WriteDisposition, LoadJobConfig  # noqa: PLC0415

        dataset_ref = f"{self.project}.{self.dataset}"
        table_ref = f"{dataset_ref}.{table}"

        job_config = LoadJobConfig(write_disposition=WriteDisposition.WRITE_APPEND)
        job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        job.result()  # blocks until complete

        logger.info("[bigquery] loaded %d rows → %s", len(df), table_ref)
        return len(df)

    def table_count(self, table: str, schema: str = "raw") -> int:
        dataset_ref = f"{self.project}.{self.dataset}"
        query = f"SELECT COUNT(*) as n FROM `{dataset_ref}.{table}`"
        result = self.client.query(query).result()
        return list(result)[0].n

    def execute(self, sql: str) -> pd.DataFrame:
        return self.client.query(sql).to_dataframe()
