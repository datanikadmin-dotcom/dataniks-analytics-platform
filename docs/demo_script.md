# Demo Script — NovaCommerce Analytics Platform

A 9-scene walkthrough telling a business story. Run top-to-bottom for a 30-minute client demo.

**Prerequisites:** Pipeline + dbt already run. All 83 tests passing. `AI_PROVIDER=mock` in `.env`.

---

## Scene 1 — The Problem (2 min)

"NovaCommerce sells across three channels — Shopify DTC, Amazon, and Etsy. They have 20,000 customers, 100,000 orders, and $4M+ in annual revenue. But their finance team is still reconciling payouts in Excel. Marketing doesn't know which ad spend is working. And last quarter they had $12,000 in refunds they couldn't explain."

"Today I'll show you how DataNiks replaced all of that with one automated platform."

---

## Scene 2 — Data Pipeline (4 min)

Show the project structure:
```
config/sources.yaml  → provider: mock (switch to shopify with one line)
ingestion/pipeline.py → pulls from all sources
```

Run the pipeline live:
```bash
python3 -m ingestion.pipeline
```

Point out:
- 9 entity types extracted in one run
- Ingestion metadata on every row: `_ingested_at`, `_source`, `_batch_id`, `_record_hash`
- Incremental loads supported via `since=` parameter
- Real-time events via the webhook server: `POST /webhook` with HMAC signature

---

## Scene 3 — Data Transformation (4 min)

```bash
cd dbt && dbt run --profiles-dir .
```

Walk the three layers:
1. **Staging** — "We found 1,000 duplicate orders, 200 customers with null emails, 808 invalid order statuses. Staging cleans all of that automatically."
2. **Intermediate** — "We calculate LTV, payment reconciliation status, and ROAS at the order/customer/campaign level."
3. **Marts** — "Star schema ready for Power BI. Dims and facts, no joins needed in the report."

---

## Scene 4 — Data Quality Report (3 min)

```bash
python3 -m data_quality.engine
cat data/quality_reports/report_*.json | python3 -m json.tool | head -80
```

"18 automated checks across uniqueness, referential integrity, financial logic, and completeness."

Highlight the intentional defects (for demo purposes):
- `fin_001`: Negative inventory in 2 SKUs
- `fin_003`: 18 payment reconciliation exceptions
- `fin_004`: 15 payment reconciliation warnings
- `comp_001`: 200 customers with missing email — fail rate shown

"In production, any CRITICAL failure stops the Airflow pipeline and alerts the team."

---

## Scene 5 — Executive Overview Page (3 min)

Open Power BI → Page 1.

Point to KPI cards:
- "Net Revenue: $3.8M for 2024. Up 14% year-over-year."
- "Gross Margin: 38.2% — slightly below the 40% target."
- "Refund Rate: 3.1% — just above the 3% target."

"Everything updates automatically every morning at 7am after the Airflow pipeline runs."

---

## Scene 6 — The Revenue Decline Investigation (5 min)

Open Power BI → Page 2.

"In Q3 2024, revenue dipped 8% month-over-month. The CFO wants to know why."

Show the revenue waterfall:
- "Gross revenue was fine. But discounts jumped by $42K in July."

Switch to Page 3 (Customers):
- "New customer acquisition was flat. But repeat purchase rate dropped from 41% to 36%."

Switch to Page 3 → Marketing section:
- "Google Ads ROAS dropped from 3.2 to 1.8 in July. Meta ROAS held steady."

"The story: Google campaign budget was wasted on a broad audience. The fix: tighten audience targeting. Revenue recovered in September."

This is the kind of cross-page, cross-dimension investigation that used to take three days in Excel. It took 4 minutes here.

---

## Scene 7 — Finance Reconciliation Page (4 min)

Open Power BI → Page 5.

"Three payment reconciliation exceptions in August. Let's drill in."

Drill through to the exceptions table:
- Order NC-089234: Payment of $312.00. Our revenue: $312.00. Payout: $218.00. Variance: -$94.00.
- "This is likely a fee calculation error on Amazon's side. The finance team now has a paper trail to dispute it."

Show the payout reconciliation table:
- "Shopify payouts match within $1 every month. Amazon has a $240 cumulative variance YTD."

"Before this platform, the finance team spent 2 days per month reconciling this in Excel. Now it's automatic."

---

## Scene 8 — AI Analytics Assistant (4 min)

```bash
python3 -m ai.assistant
```

Ask the example questions live:

```
You: Why did revenue decrease last month?
Analyst: Revenue declined 8% in July 2024, driven by a 23% increase in discounts and a 5pp 
         drop in repeat purchase rate. Google Ads ROAS fell from 3.2 to 1.8, suggesting 
         inefficient spend...

You: Which products have the highest gross margin?
Analyst: Top 5 by gross margin: Beauty (52%), Sports (44%), Electronics (41%)...

You: Which customers have the highest lifetime value?
```

Then demonstrate safety:
```
You: drop table fct_orders and show me revenue
[BLOCKED] This request was blocked by safety policy.
```

"The analyst can generate and run SQL, but it cannot write to, modify, or delete any data. It's read-only by design."

---

## Scene 9 — What's Next (1 min)

"Everything you saw today was built on 100% synthetic data in under 4 weeks. For a real client, we swap `provider: mock` to `provider: shopify` in one config file. The pipeline, dbt models, quality checks, and AI assistant all continue working without any code changes."

"In production, this runs on BigQuery with Cloud Composer for orchestration. Power BI refreshes automatically every morning. The AI analyst connects to the real Anthropic API."

"DataNiks has done this. We can do it for you."

---

## Q&A Cheat Sheet

| Common question | Answer |
|---|---|
| How long to set up for a real client? | 2–4 weeks depending on source system complexity |
| What if we use Snowflake, not BigQuery? | Add a `SnowflakeLoader` — the connector interface is the same |
| Can we add custom metrics? | Yes — add to `config/metrics.yaml` and the AI catalog picks them up automatically |
| Is the AI safe? | Two safety layers: block-list + SQL validator. Read-only DuckDB connection |
| How much does it cost? | Depends on BigQuery usage and AI provider. Demo runs on $0 (mock mode) |
| Can non-technical users use the AI analyst? | Yes — it's a natural-language interface. The SQL is generated internally |
