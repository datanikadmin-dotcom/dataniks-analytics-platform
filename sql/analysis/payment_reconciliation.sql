-- Payment reconciliation exceptions and warnings
SELECT
    p.payment_id,
    p.order_id,
    d.full_date                         AS payment_date,
    p.amount                            AS payment_amount,
    o.net_revenue                       AS order_net_revenue,
    ROUND(ABS(p.amount - o.net_revenue), 2) AS variance,
    p.reconciliation_status,
    p.method
FROM main_marts.fct_payments p
JOIN main_marts.fct_orders o ON p.order_id = o.order_id
JOIN main_marts.dim_date d ON p.date_id = d.date_id
WHERE p.reconciliation_status IN ('EXCEPTION', 'WARNING')
ORDER BY p.reconciliation_status, variance DESC;
