-- Row count validation across all mart tables
-- Run after each pipeline execution to detect unexpected drops

SELECT 'dim_date'        AS table_name, COUNT(*) AS row_count FROM main_marts.dim_date
UNION ALL
SELECT 'dim_customer',    COUNT(*) FROM main_marts.dim_customer
UNION ALL
SELECT 'dim_product',     COUNT(*) FROM main_marts.dim_product
UNION ALL
SELECT 'dim_channel',     COUNT(*) FROM main_marts.dim_channel
UNION ALL
SELECT 'dim_warehouse',   COUNT(*) FROM main_marts.dim_warehouse
UNION ALL
SELECT 'fct_orders',      COUNT(*) FROM main_marts.fct_orders
UNION ALL
SELECT 'fct_order_items', COUNT(*) FROM main_marts.fct_order_items
UNION ALL
SELECT 'fct_payments',    COUNT(*) FROM main_marts.fct_payments
UNION ALL
SELECT 'fct_refunds',     COUNT(*) FROM main_marts.fct_refunds
UNION ALL
SELECT 'fct_inventory',   COUNT(*) FROM main_marts.fct_inventory
UNION ALL
SELECT 'fct_shipments',   COUNT(*) FROM main_marts.fct_shipments
UNION ALL
SELECT 'fct_ad_spend',    COUNT(*) FROM main_marts.fct_ad_spend
UNION ALL
SELECT 'fct_payouts',     COUNT(*) FROM main_marts.fct_payouts
UNION ALL
SELECT 'mart_sales',      COUNT(*) FROM main_marts.mart_sales
UNION ALL
SELECT 'mart_customer',   COUNT(*) FROM main_marts.mart_customer
UNION ALL
SELECT 'mart_marketing',  COUNT(*) FROM main_marts.mart_marketing
UNION ALL
SELECT 'mart_inventory',  COUNT(*) FROM main_marts.mart_inventory
UNION ALL
SELECT 'mart_finance',    COUNT(*) FROM main_marts.mart_finance
ORDER BY table_name;
