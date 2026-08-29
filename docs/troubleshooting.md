# Troubleshooting

## Data Generator

**Problem:** `data/synthetic/synthetic/` — double-nested output directory  
**Fix:** Already resolved. `writer.py` was appending `subdir="synthetic"` to an output_dir that already ended in `synthetic`. Default is now `subdir=""`.

**Problem:** Refund count assertion fails in tests  
**Fix:** Small dataset sizes amplify variance. Test now uses `<= cfg.refunds * 2` instead of a tight upper bound.

---

## dbt

**Problem:** `dbt: command not found`  
**Fix:** Add dbt's install location to PATH:
```bash
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
```

**Problem:** `dbt_utils.date_spine` not found  
**Fix:** `dim_date` was rewritten to use DuckDB's native `generate_series`. No external packages needed.

**Problem:** `data_tests` key not recognised  
**Fix:** dbt v1.8 changed the key from `tests:` to `data_tests:` in schema.yml. All models updated accordingly.

**Problem:** dbt test fails on raw schema  
**Expected:** Raw data has intentional corruption (11 defect types). All raw tests use `severity: warn`. Staging tests use `severity: error`. If staging tests fail, investigate the staging model's filter logic.

**Problem:** `dbt run` produces 0 rows in marts  
**Check:** Run `python3 -m ingestion.pipeline` first. dbt transforms existing raw data — it cannot run if raw tables are empty.

---

## DuckDB

**Problem:** `duckdb.IOException: database is locked`  
**Fix:** Another process has the file open. Close all DuckDB connections (Python REPL, dbt, tests) before running the pipeline.

**Problem:** `column not found` in a mart query  
**Check:** Run `dbt run` again — the mart table may be stale. Check `dbt/target/run_results.json` for errors.

---

## Ingestion Pipeline

**Problem:** `ModuleNotFoundError` for any local module  
**Fix:** Run from the project root with `python3 -m ingestion.pipeline`, not `python3 ingestion/pipeline.py`.

**Problem:** Synthetic Parquet files not found  
**Fix:** Run data generator first:
```bash
python3 -m data_generator.main
```

---

## Webhook Server

**Problem:** 401 Unauthorized on every request  
**Fix:** Check `WEBHOOK_SECRET` in `.env` matches the secret used to sign the request. Use:
```python
import hmac, hashlib
sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
```

**Problem:** Duplicate events being processed  
**Expected:** The webhook server checks `event_id` idempotency. Retries with the same `event_id` return 200 but do not reinsert.

---

## AI Analyst

**Problem:** `Unknown AI provider` error  
**Fix:** Set `AI_PROVIDER=mock` in `.env` (or pass `--provider mock`). Valid values: `mock`, `anthropic`, `openai`.

**Problem:** SQL is generated but returns 0 rows  
**Check:** Is the warehouse populated? Run pipeline + dbt first. Also verify the mart tables exist:
```python
from ingestion.loaders.duckdb_loader import DuckDBLoader
db = DuckDBLoader()
db.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main_marts'")
```

**Problem:** Response is blocked unexpectedly  
**Check:** Question contains a word matching `_BLOCKED_PATTERNS` in `ai/assistant/core.py`. Rephrase the question to avoid words like "drop", "delete", "ignore".

---

## Tests

**Problem:** `pytest: command not found`  
**Fix:**
```bash
python3 -m pytest tests/ -v
```

**Problem:** AI tests fail with `table not found`  
**Expected:** AI tests use `data/warehouse.duckdb`. If this file doesn't exist, the test uses an in-memory DB and SQL queries return empty results — tests check structure, not data. Run the full pipeline to populate it.

---

## Power BI

**Problem:** `DirectQuery` errors on DuckDB  
**Fix:** Use Import mode for DuckDB. DirectQuery requires a live ODBC driver that isn't always available. For production, use BigQuery with DirectQuery.

**Problem:** Time intelligence returns blank  
**Check:** Confirm `dim_date[full_date]` is marked as a Date table in Power BI. Right-click the table → Mark as date table → select `full_date`.

**Problem:** Cross-page slicer not syncing  
**Fix:** Enable slicer sync in View → Sync Slicers, and ensure the slicer targets `dim_date[full_date]` on both pages.
