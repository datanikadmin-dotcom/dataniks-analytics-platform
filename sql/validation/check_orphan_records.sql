-- Detect orphan order items (no matching order in fct_orders)
SELECT
    'orphan_order_items' AS check_name,
    COUNT(*) AS failed_records
FROM main_marts.fct_order_items i
LEFT JOIN main_marts.fct_orders o ON i.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL

-- Orphan payments
SELECT
    'orphan_payments',
    COUNT(*)
FROM main_marts.fct_payments p
LEFT JOIN main_marts.fct_orders o ON p.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL

-- Orphan refunds
SELECT
    'orphan_refunds',
    COUNT(*)
FROM main_marts.fct_refunds r
LEFT JOIN main_marts.fct_orders o ON r.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL

-- Orphan shipments
SELECT
    'orphan_shipments',
    COUNT(*)
FROM main_marts.fct_shipments s
LEFT JOIN main_marts.fct_orders o ON s.order_id = o.order_id
WHERE o.order_id IS NULL;
