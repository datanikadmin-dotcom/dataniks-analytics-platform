# Data Lineage

## Raw → Staging

| Raw table | Staging model | Key transforms |
|---|---|---|
| raw.raw_customers | stg_customers | dedup by customer_id (latest _ingested_at), filter null email |
| raw.raw_products | stg_products | filter null SKU, price > 0, cost < price |
| raw.raw_orders | stg_orders | dedup, normalise status (unknown for invalid values) |
| raw.raw_order_items | stg_order_items | INNER JOIN to valid orders (removes orphans) |
| raw.raw_payments | stg_payments | dedup, filter duplicates |
| raw.raw_refunds | stg_refunds | pass-through with type casts |
| raw.raw_inventory | stg_inventory | clamp closing_qty ≥ 0 |
| raw.raw_shipments | stg_shipments | derive is_on_time |
| raw.raw_advertising | stg_ad_spend | derive roas, ctr |
| raw.raw_payouts | stg_payouts | pass-through with type casts |

## Staging → Intermediate

| Intermediate model | Source staging tables | Key logic |
|---|---|---|
| int_order_revenue | stg_order_items, stg_refunds | order-level: gross_revenue, net_revenue, gross_profit |
| int_customer_orders | stg_orders, int_order_revenue | LTV, order_count, first/last order, repeat flag |
| int_payment_reconciliation | stg_payments, int_order_revenue | MATCHED/WARNING/EXCEPTION per order |
| int_campaign_performance | stg_ad_spend | monthly ROAS, CTR, CVR, cost_per_conversion |
| int_inventory_movements | stg_inventory | latest snapshot per product×warehouse |
| int_product_sales | stg_order_items, stg_orders | product-level units sold, revenue, margin |

## Intermediate → Dimensions

| Dimension | Source models | Key joins |
|---|---|---|
| dim_date | generate_series (DuckDB) | No dependencies |
| dim_customer | stg_customers + int_customer_orders | customer_id |
| dim_product | stg_products + int_product_sales | product_id |
| dim_channel | static VALUES | No dependencies |
| dim_warehouse | static VALUES | No dependencies |

## Intermediate → Facts

| Fact table | Source models | Key joins |
|---|---|---|
| fct_orders | int_order_revenue | date_id, customer_id, channel_id |
| fct_order_items | stg_order_items, fct_orders, dim_product | order_id, product_id |
| fct_payments | stg_payments, int_payment_reconciliation | order_id |
| fct_refunds | stg_refunds, fct_orders, fct_payments | order_id, payment_id, customer_id |
| fct_inventory | stg_inventory, dim_product, dim_warehouse | product_id, warehouse_id |
| fct_shipments | stg_shipments, dim_warehouse | order_id, warehouse_id |
| fct_ad_spend | stg_ad_spend, dim_channel | channel_id |
| fct_payouts | stg_payouts + period_revenue | date_id, platform |

## Facts → Mart Summaries

| Mart table | Source fact tables | Grain change |
|---|---|---|
| mart_sales | fct_orders, fct_order_items | order → month × channel |
| mart_customer | fct_orders, dim_customer | already customer grain |
| mart_marketing | fct_ad_spend | campaign × date → campaign × month |
| mart_inventory | fct_inventory | product × warehouse × month → latest snapshot |
| mart_finance | fct_payouts, fct_orders | payout → month × platform |

## Ingestion Metadata Propagation

All raw tables carry four metadata columns added by `BaseConnector.add_ingestion_metadata()`:
- `_ingested_at` — UTC timestamp of extraction
- `_source` — connector name (e.g. "mock_commerce")
- `_batch_id` — UUID per pipeline run
- `_record_hash` — MD5 of the row payload (for change detection)

These columns are stripped in staging models (not propagated to marts).

## Data Quality Gate

```
raw schema
   │
   ▼ (severity: warn — raw has known intentional defects)
stg_ models
   │
   ▼ (severity: error — staging should be clean)
int_ / dim_ / fct_ models
   │
   ▼
data_quality/engine.py (18 checks on marts)
   │
   ├── CRITICAL failure → Airflow alerts + halts downstream
   └── WARNING/INFO → logged, pipeline continues
```
