# Platform Architecture

## Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                     SOURCE SYSTEMS                                   │
│  Shopify · Stripe · Google Ads · Meta Ads · WMS · Shiprocket         │
│  (dev: MockConnector reads synthetic Parquet)                        │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
              ┌─────────────▼─────────────┐
              │   INGESTION LAYER         │
              │  ingestion/pipeline.py    │
              │  BaseConnector → Mock /   │
              │  ShopifyConnector         │
              │  Webhook (FastAPI)         │
              └─────────────┬─────────────┘
                            │  Parquet / JSON rows
              ┌─────────────▼─────────────┐
              │   STORAGE (RAW)           │
              │  DuckDB raw schema (dev)  │
              │  BigQuery raw dataset (prod)│
              └─────────────┬─────────────┘
                            │
              ┌─────────────▼─────────────┐
              │   TRANSFORMATION (dbt)    │
              │  staging → intermediate   │
              │  → dims → facts → marts   │
              └─────────────┬─────────────┘
                            │
         ┌──────────────────┼─────────────────────┐
         │                  │                     │
┌────────▼───────┐ ┌────────▼───────┐  ┌──────────▼──────────┐
│  DATA QUALITY  │ │  POWER BI      │  │  AI ANALYST         │
│  18 checks     │ │  5-page report │  │  NL → SQL → answer  │
│  4 severities  │ │  star schema   │  │  Mock/Anthropic/OAI │
└────────────────┘ └────────────────┘  └─────────────────────┘
                            │
              ┌─────────────▼─────────────┐
              │   ORCHESTRATION (Airflow) │
              │  daily_pipeline DAG       │
              │  quality_checks DAG       │
              └───────────────────────────┘
```

## Layer Responsibilities

### Source Systems
Real APIs (Shopify, Stripe, Google Ads, etc.) or MockConnector for dev/demo.
Each source is defined in `config/sources.yaml`; switching `provider: mock` → `provider: shopify` requires no code changes.

### Ingestion Layer
`BaseConnector` defines the interface. Implementations paginate responses, attach ingestion metadata (`_ingested_at`, `_source`, `_batch_id`, `_record_hash`), and support incremental loads via `since` datetime.

`ingestion/webhooks/server.py` (FastAPI) accepts real-time events, validates HMAC-SHA256 signatures, and writes to `raw.webhook_events`.

### Storage
- **Dev/CI:** DuckDB file (`data/warehouse.duckdb`) — zero config, no cloud credentials
- **Prod:** BigQuery — schemas mirror DuckDB, loader swapped via `config/client.yaml`

### Transformation (dbt)
Three-layer medallion:
1. **Staging** — dedup, null-filter, type cast, status normalise
2. **Intermediate** — business metrics (order revenue, customer LTV, payment reconciliation)
3. **Marts** — dims + facts + mart summary tables ready for BI

### Data Quality
`DataQualityEngine` runs 18 checks across uniqueness, referential integrity, financial logic, and completeness. Results saved as timestamped JSON. Airflow branches on `has_critical_failures()`.

### Power BI
5-page report over star schema. DAX measures add time intelligence (MTD/QTD/YTD/PM/PY/MoM/YoY). Business logic stays in dbt — DAX aggregates only.

### AI Analytics Assistant
`DataNiksAnalyst` pipeline: question → block-list check → SQL generation (LLM) → SQL safety validation → DuckDB execution → narrative explanation (LLM) → `AnalystResponse`.

Providers: `MockProvider` (no API key) → `AnthropicProvider` → `OpenAIProvider`, all behind `BaseLLMProvider`.

### Orchestration (Airflow)
`novacommerce_daily_pipeline`: runs at 06:00 UTC, extract → load → dbt staging/intermediate/marts → dbt tests → quality checks → branch on quality.

## Configuration-First Design

```
config/
  client.yaml     # warehouse/BI/AI provider, reconciliation thresholds
  sources.yaml    # connector per source, switch mock ↔ real here
  metrics.yaml    # 13 metric definitions, loaded by AI catalog
```

Environment variables in `.env` (never committed); `config/client.yaml` uses `${ENV_VAR}` substitution.

## Dev vs Prod Differences

| Aspect | Dev | Prod |
|---|---|---|
| Data | Synthetic (Faker + seed=42) | Live API |
| Storage | DuckDB file | BigQuery |
| dbt adapter | dbt-duckdb | dbt-bigquery |
| AI provider | MockProvider | Anthropic / OpenAI |
| Airflow | Local / docker-compose | Cloud Composer / MWAA |
| Webhooks | localhost:8080 | Public URL + TLS |
