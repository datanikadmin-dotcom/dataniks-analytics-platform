# Deployment Guide

## Local / Demo Setup

### Prerequisites
- Python 3.9+ (tested on 3.9.6)
- pip

### Install
```bash
cd /Users/dataniks/dataniks-analytics-platform
python3 -m pip install -r requirements.txt
cp .env.example .env          # fill in values as needed
```

### Generate synthetic data
```bash
python3 -m data_generator.main
# Output: data/synthetic/{customers,products,orders,...}.parquet
```

### Run ingestion (loads into DuckDB)
```bash
python3 -m ingestion.pipeline
# Output: data/warehouse.duckdb (raw schema populated)
```

### Run dbt (transforms raw → marts)
```bash
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
cd dbt
dbt deps
dbt run --profiles-dir .
dbt test --profiles-dir .
```

### Run data quality checks
```bash
python3 -m data_quality.engine
# Output: data/quality_reports/report_YYYYMMDD_HHMMSS.json
```

### Launch AI analyst (interactive)
```bash
python3 -m ai.assistant
# Flags: --question "..." for single-shot, --provider mock|anthropic|openai
```

### Run test suite
```bash
python3 -m pytest tests/ -v
```

### Start webhook server (optional)
```bash
uvicorn ingestion.webhooks.server:app --port 8080 --reload
```

---

## Docker / Airflow

```bash
docker-compose up -d
# Services:
#   airflow-web  → http://localhost:8081  (admin / admin)
#   airflow-sched
#   webhook      → http://localhost:8080/webhook
```

On first run, `airflow-init` creates the DB and admin user.
DAGs: `novacommerce_daily_pipeline`, `novacommerce_quality_checks`.

---

## Production (BigQuery)

### 1. GCP setup
```
gcloud projects create <project-id>
gcloud iam service-accounts create dap-sa
gcloud projects add-iam-policy-binding <project-id> \
  --member serviceAccount:dap-sa@<project-id>.iam.gserviceaccount.com \
  --role roles/bigquery.dataEditor
gcloud iam service-accounts keys create sa.json \
  --iam-account dap-sa@<project-id>.iam.gserviceaccount.com
```

### 2. .env
```
GCP_PROJECT_ID=<project-id>
BQ_DATASET_RAW=novacommerce_raw
BQ_DATASET_STAGING=novacommerce_staging
BQ_DATASET_MARTS=novacommerce_marts
GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
```

### 3. Swap loaders
In `config/client.yaml`:
```yaml
warehouse:
  type: bigquery
```

In `config/sources.yaml` change `provider: mock` → `provider: shopify` etc.

### 4. dbt profiles
`dbt/profiles.yml` already has the `prod` target. Run:
```bash
dbt run --profiles-dir . --target prod
```

### 5. Real Airflow
Deploy DAG files to Cloud Composer or MWAA. Set the above env vars as Airflow Variables or use Secret Manager.

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| GCP_PROJECT_ID | Prod only | GCP project |
| BQ_DATASET_RAW | Prod only | BigQuery raw dataset |
| BQ_DATASET_STAGING | Prod only | BigQuery staging dataset |
| BQ_DATASET_MARTS | Prod only | BigQuery marts dataset |
| DUCKDB_PATH | Dev | Path to .duckdb file |
| AI_PROVIDER | No | mock / anthropic / openai (default: mock) |
| ANTHROPIC_API_KEY | If AI_PROVIDER=anthropic | |
| OPENAI_API_KEY | If AI_PROVIDER=openai | |
| WEBHOOK_SECRET | Webhook server | HMAC-SHA256 signing key |
| SYNTHETIC_SEED | No | Random seed for data generator (default: 42) |
| RECON_WARNING_THRESHOLD | No | $ amount for WARNING (default: 1) |
| RECON_EXCEPTION_THRESHOLD | No | $ amount for EXCEPTION (default: 100) |
