# DataNiks Unified Analytics Platform

A production-quality, end-to-end analytics platform demonstrating the full modern data stack — built by DataNiks around the fictional e-commerce brand **NovaCommerce**. Reusable for any real client by changing one config file.

---

## What This Is

| Layer | Technology | Purpose |
|---|---|---|
| Source connectors | Python + `BaseConnector` | API/webhook ingestion, swap mock → real without code changes |
| Storage (dev) | DuckDB | Local BigQuery substitute — zero config |
| Storage (prod) | BigQuery | Cloud-scale warehouse |
| Transformation | dbt + dbt-duckdb | 3-layer medallion: staging → intermediate → marts |
| Data Quality | Custom Python engine | 18 automated checks, 4 severities |
| BI Reporting | Power BI | 5-page star-schema report |
| AI Assistant | LLM + SQL validator | NL → SQL → narrative, read-only, safety-gated |
| Orchestration | Apache Airflow | Daily + hourly quality DAGs |
| Real-time | FastAPI webhook server | HMAC-signed event ingestion |

---

## Quick Start

```bash
cd /Users/dataniks/dataniks-analytics-platform
python3 -m pip install -r requirements.txt
cp .env.example .env

# 1. Generate synthetic data (2 years, 100K orders)
python3 -m data_generator.main

# 2. Load into DuckDB
python3 -m ingestion.pipeline

# 3. Transform with dbt
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
cd dbt && dbt run --profiles-dir . && dbt test --profiles-dir . && cd ..

# 4. Run quality checks
python3 -m data_quality.engine

# 5. Ask the AI analyst
python3 -m ai.assistant
```

Run all 83 tests:
```bash
python3 -m pytest tests/ -v
```

---

## Project Structure

```
dataniks-analytics-platform/
├── config/
│   ├── client.yaml          # client name, warehouse, AI, reconciliation config
│   ├── sources.yaml         # source connectors — change provider: mock → shopify here
│   └── metrics.yaml         # 13 business metric definitions
│
├── data_generator/          # synthetic NovaCommerce data (Faker + seed=42)
│   ├── config.py            # GeneratorConfig dataclass
│   ├── generators/          # customers, products, orders, inventory, advertising
│   └── corruption.py        # 11 intentional defect types for DQ demonstration
│
├── ingestion/
│   ├── base.py              # BaseConnector abstract interface
│   ├── extractors/
│   │   └── mock.py          # MockConnector — reads synthetic Parquet
│   ├── loaders/
│   │   ├── duckdb_loader.py # DuckDBLoader (dev)
│   │   └── bigquery_loader.py # BigQueryLoader (prod stub)
│   ├── webhooks/
│   │   └── server.py        # FastAPI — HMAC-verified, idempotent event ingestion
│   └── pipeline.py          # run_full_pipeline()
│
├── dbt/
│   ├── models/
│   │   ├── staging/         # 10 staging models — dedup, null-filter, normalise
│   │   ├── intermediate/    # 6 intermediate models — order revenue, LTV, reconciliation
│   │   └── marts/           # 5 dims + 8 facts + 5 mart summaries
│   ├── dbt_project.yml
│   └── profiles.yml         # dev: duckdb | prod: bigquery
│
├── data_quality/
│   ├── models.py            # CheckResult, Severity, CheckStatus dataclasses
│   ├── engine.py            # DataQualityEngine — runs all 18 checks
│   └── checks/
│       ├── uniqueness.py    # 4 checks — order/customer/payment/product IDs
│       ├── referential.py   # 4 checks — orphan items/payments/refunds/shipments
│       ├── financial.py     # 6 checks — negative inventory, over-refunds, recon
│       └── completeness.py  # 4 checks — email/SKU, status validity, volume anomaly
│
├── airflow/
│   └── dags/
│       ├── daily_pipeline.py    # 06:00 UTC — extract → dbt → quality → alert
│       └── quality_dag.py       # every 6h — quality checks only
│
├── ai/
│   ├── providers/
│   │   ├── base.py          # BaseLLMProvider, LLMResponse
│   │   ├── mock.py          # MockProvider — keyword-matched, no API key needed
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   └── factory.py       # get_provider() — reads AI_PROVIDER env var
│   ├── queries/
│   │   └── validator.py     # SQL safety validator — SELECT-only enforcement
│   ├── metrics/
│   │   └── catalog.py       # MetricCatalog — loads metrics.yaml, keyword detection
│   ├── prompts/
│   │   └── system.py        # ANALYST_SYSTEM_PROMPT, SQL_GENERATION_SYSTEM_PROMPT
│   └── assistant/
│       ├── core.py          # DataNiksAnalyst — NL → SQL → execute → explain
│       └── __main__.py      # CLI: python3 -m ai.assistant
│
├── powerbi/
│   ├── dax/
│   │   └── measures.md      # Full DAX measure library (revenue, margin, time-intel)
│   └── documentation/
│       ├── model.md         # Star schema relationships + cardinalities
│       └── pages.md         # 5-page report specification
│
├── docs/
│   ├── architecture.md      # System diagram + layer responsibilities
│   ├── data_dictionary.md   # All columns in all mart/fact/dim tables
│   ├── data_lineage.md      # raw → staging → intermediate → marts flow
│   ├── deployment.md        # Local + Docker + BigQuery prod setup
│   ├── client_onboarding.md # 17-question questionnaire + onboarding checklist
│   ├── security.md          # Secrets, webhook auth, AI safety, access control
│   ├── troubleshooting.md   # Known issues + fixes
│   ├── api_contracts.md     # Webhook API, BaseConnector, BaseLLMProvider specs
│   └── demo_script.md       # 9-scene 30-minute client demo
│
└── tests/
    ├── data_generator/      # test_config.py, test_generators.py, test_corruption.py
    ├── ingestion/           # test_pipeline.py (runs full pipeline on temp DuckDB)
    ├── dbt/                 # test_dbt_models.py (runs dbt + validates mart tables)
    ├── data_quality/        # test_quality_engine.py (all 18 checks)
    └── ai/                  # test_ai_assistant.py (validator, catalog, analyst)
```

---

## Key Design Decisions

### Configuration-first
Switch any source from mock to real by changing one line in `config/sources.yaml`:
```yaml
commerce:
  provider: mock   # → shopify
```
No code changes. The connector interface is identical.

### DuckDB as local BigQuery
`dbt/profiles.yml` has two targets: `dev` (duckdb) and `prod` (bigquery). Same SQL runs on both. CI never needs cloud credentials.

### Two-layer AI safety
1. **Block-list** in `ai/assistant/core.py` — rejects prompt injection before any LLM call
2. **SQL validator** in `ai/queries/validator.py` — rejects any non-SELECT query before execution

### Deterministic corruption
`data_generator/corruption.py` injects exactly the same 11 defect types on every run (seed=42), enabling reproducible data quality testing and reliable demo storytelling.

---

## Synthetic Data Volumes

| Entity | Count | Notes |
|---|---|---|
| Customers | 20,000 | 4 segments, realistic US demographics |
| Products | 2,000 | 8 categories, power-law price distribution |
| Orders | ~101,000 | 2 years, seasonal + holiday + weekend patterns |
| Order items | ~134,000 | |
| Payments | ~100,000 | 2% failure rate |
| Refunds | ~12,000 | |
| Shipments | ~75,000 | 5 carriers |
| Inventory snapshots | ~96,000 | product × warehouse × month |
| Ad spend records | ~8,300 | Google + Meta, 10 campaigns each |
| Payouts | ~72 | monthly per platform |

---

## Business Metrics Defined

All 13 metrics are defined in `config/metrics.yaml` with formula, grain, source tables, unit, format, and known limitations.

| Metric | Formula |
|---|---|
| gross_revenue | SUM(quantity × unit_price) |
| net_revenue | gross_revenue - discounts - refunds |
| cogs | SUM(quantity × unit_cost) |
| gross_profit | net_revenue - cogs |
| gross_margin_pct | gross_profit / net_revenue |
| order_count | COUNT(DISTINCT order_id) |
| aov | net_revenue / order_count |
| new_customers | customers with first order in period |
| cac | ad_spend / new_customers |
| roas | attributed_revenue / ad_spend |
| refund_rate | total_refunds / gross_revenue |
| inventory_turnover | cogs / avg_inventory_value |
| ltv | SUM(net_revenue) per customer |

---

## AI Analyst — Example Questions

```
Why did revenue decrease last month?
Which products have the highest gross margin?
Which marketing channel has the best ROAS?
Which customers have the highest lifetime value?
Which products are at risk of going out of stock?
Are payments reconciling with revenue?
Which campaigns generated the most revenue?
What caused the increase in refunds?
Which warehouses have the most shipment delays?
What changed compared with last month?
```

---

## Switching to Production (BigQuery + Real APIs)

1. Fill in `.env`: `GCP_PROJECT_ID`, `BQ_DATASET_*`, `GOOGLE_APPLICATION_CREDENTIALS`
2. In `config/client.yaml`: set `warehouse.type: bigquery`
3. In `config/sources.yaml`: change `provider: mock` → `provider: shopify` (etc.)
4. Run `dbt run --profiles-dir . --target prod`
5. Deploy Airflow DAGs to Cloud Composer or MWAA
6. Connect Power BI to BigQuery via ODBC gateway
7. Set `AI_PROVIDER=anthropic` and add `ANTHROPIC_API_KEY`

Full instructions: [`docs/deployment.md`](docs/deployment.md)

---

## Built by DataNiks

DataNiks LLC — Excel & Power BI analytics consulting.
Contact: datanikadmin@gmail.com
