# Client Onboarding Guide

## Overview

This document covers how to onboard a new client onto the DataNiks Analytics Platform — replacing NovaCommerce (demo) with the client's real data sources.

Typical onboarding takes 2–4 weeks:
- Week 1: Discovery + credentials
- Week 2: Data validation + dbt adjustments
- Week 3: Power BI buildout
- Week 4: UAT + handoff

---

## Client Questionnaire

Answer before the first technical call.

### Business
1. What is the primary business model? (D2C ecommerce / marketplace / SaaS / brick-and-mortar + online)
2. What is the main sales platform? (Shopify / WooCommerce / Magento / custom)
3. What payment processors do you use? (Stripe / Braintree / PayPal / Square)
4. How many orders per month on average?
5. How many active SKUs?
6. Do you sell on marketplaces? (Amazon / Etsy / eBay) — which ones?
7. What advertising platforms? (Google Ads / Meta / TikTok / Pinterest / other)
8. What WMS / 3PL do you use for fulfillment?
9. What is your fiscal year end month?
10. What are the 3 KPIs your CEO looks at first every Monday?

### Technical
11. Do you have a data warehouse? (BigQuery / Snowflake / Redshift / none)
12. What BI tool do you currently use, if any?
13. Do you have any existing ETL pipelines?
14. Who will be the technical point of contact?
15. What is your data retention requirement? (12 months / 24 months / unlimited)
16. Do you have any data privacy or compliance requirements? (GDPR / CCPA / PCI)
17. Can you provide read-only API credentials for all source systems?

---

## Onboarding Checklist

### Phase 1 — Discovery
- [ ] Complete client questionnaire above
- [ ] Identify all source systems and their API documentation
- [ ] Confirm data volumes (orders/month, SKU count, customer count)
- [ ] Determine whether DuckDB (dev/small) or BigQuery (prod/scale) is appropriate
- [ ] Confirm fiscal year for `dim_date` configuration
- [ ] Map client's status values to platform standard (placed/fulfilled/cancelled/returned)

### Phase 2 — Credentials & Infrastructure
- [ ] Receive API credentials for each source (read-only scopes only)
- [ ] Set up `.env` file with all client secrets
- [ ] Provision BigQuery project + service account (if production)
- [ ] Test connectivity: `connector.health_check()` for each source
- [ ] Configure webhook endpoint URL and rotate `WEBHOOK_SECRET`

### Phase 3 — Data Validation
- [ ] Run `python3 -m data_generator.main` to establish baseline (dev only)
- [ ] Run `python3 -m ingestion.pipeline` for first full load
- [ ] Run `dbt run` + `dbt test`; resolve any test failures
- [ ] Run data quality checks; review report JSON
- [ ] Validate row counts vs client's source reports (±5% acceptable)
- [ ] Validate key metrics (revenue, order count) vs client's existing dashboard

### Phase 4 — Power BI Setup
- [ ] Connect Power BI to DuckDB / BigQuery
- [ ] Load all mart tables
- [ ] Build star schema relationships (per `powerbi/documentation/model.md`)
- [ ] Import DAX measures from `powerbi/dax/measures.md`
- [ ] Build all 5 report pages (per `powerbi/documentation/pages.md`)
- [ ] Set up scheduled refresh
- [ ] Configure Row-Level Security if required

### Phase 5 — AI Analyst
- [ ] Set `AI_PROVIDER=anthropic` (or openai) in `.env`
- [ ] Test with the 10 example questions in `ai/assistant/__main__.py`
- [ ] Verify SQL safety validator blocks destructive queries
- [ ] Verify SQL executes and returns sensible results

### Phase 6 — UAT & Handoff
- [ ] Walk client through all 5 Power BI pages
- [ ] Run 9-scene demo script (`docs/demo_script.md`)
- [ ] Train client on AI Analyst CLI / integration
- [ ] Hand over `docs/` folder + Power BI `.pbix` file
- [ ] Document any client-specific customisations
- [ ] Schedule recurring check-in (monthly recommended)

---

## Config Changes Per Client

`config/client.yaml` — update these sections:
```yaml
client:
  name: "Client Name LLC"
  industry: "Fashion"          # context for AI prompts
  fiscal_year_start_month: 2   # February fiscal year

reconciliation:
  warning_threshold: 5         # adjust to client's fee structure
  exception_threshold: 500
```

`config/sources.yaml` — swap `provider: mock` → `provider: shopify` etc. and add credentials.

`config/metrics.yaml` — add or rename metrics if client uses different terminology (e.g. "contribution margin" instead of "gross profit").

---

## Connector Implementation Guide

To implement a real connector (e.g. Shopify):

1. Create `ingestion/extractors/shopify.py`
2. Subclass `BaseConnector`
3. Implement all abstract methods: `authenticate`, `health_check`, `get_customers`, `get_products`, `get_orders`, `get_order_items`, `get_payments`, `get_refunds`, `get_inventory`, `get_shipments`, `get_ad_spend`, `get_payouts`
4. Each getter must yield `pd.DataFrame` batches via `_paginate()`
5. Call `self.add_ingestion_metadata(df, source, batch_id)` before yielding
6. Set `provider: shopify` in `config/sources.yaml`
7. Write tests in `tests/ingestion/test_shopify_connector.py`
