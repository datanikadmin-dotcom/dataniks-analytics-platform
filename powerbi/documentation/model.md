# NovaCommerce Power BI — Star Schema Model

## Relationships (all single-direction, many → one)

```
fct_order_items ──── dim_product    (product_id)
fct_order_items ──── dim_date       (date_id)
fct_order_items ──┐
                  └──── fct_orders  (order_id)
fct_orders      ──── dim_customer   (customer_id)
fct_orders      ──── dim_channel    (channel_id)
fct_orders      ──── dim_date       (date_id)
fct_payments    ──── dim_date       (date_id)
fct_refunds     ──── dim_date       (date_id)
fct_refunds     ──── dim_customer   (customer_id)
fct_ad_spend    ──── dim_date       (date_id)
fct_ad_spend    ──── dim_channel    (channel_id)
fct_inventory   ──── dim_product    (product_id)
fct_inventory   ──── dim_warehouse  (warehouse_id)
fct_inventory   ──── dim_date       (date_id)
fct_shipments   ──── dim_warehouse  (warehouse_id)
fct_shipments   ──── dim_date       (date_id)
fct_payouts     ──── dim_date       (date_id)
```

## Dimension Cardinalities

| Dimension | Rows | Key |
|---|---|---|
| dim_date | 731 | date_id (date) |
| dim_customer | ~20,000 | customer_id |
| dim_product | ~2,000 | product_id |
| dim_channel | 7 | channel_id |
| dim_warehouse | 5 | warehouse_id |

## Fact Cardinalities

| Fact | Rows | Grain |
|---|---|---|
| fct_orders | ~101,000 | order |
| fct_order_items | ~134,000 | order item |
| fct_payments | ~100,000 | payment |
| fct_refunds | ~12,000 | refund |
| fct_ad_spend | ~8,300 | campaign × date |
| fct_inventory | ~96,000 | product × warehouse × month |
| fct_shipments | ~75,000 | shipment |
| fct_payouts | ~72 | payout |

## Import vs DirectQuery

| Mode | When to use |
|---|---|
| Import (recommended) | < 100M rows, refresh ≤ hourly |
| DirectQuery | Real-time requirement or data > 1B rows |
| Composite | Mix: dimensions imported, large facts direct |

For NovaCommerce demo: **Import** all tables. Refresh after each pipeline run.

## Refresh Configuration

In production (BigQuery):
1. Create a gateway connection using service-account JSON.
2. Set scheduled refresh to match Airflow pipeline completion (e.g., 07:00 UTC).
3. Enable incremental refresh on fct_orders and fct_order_items using order_date.

## Row-Level Security (optional)

Apply RLS via dim_customer[customer_segment] or dim_channel[channel_name]
if different users should see different subsets of data.
