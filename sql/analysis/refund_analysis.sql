-- Refund rate trends and over-refund detection
SELECT
    d.year,
    d.month_name,
    COUNT(r.refund_id)                                              AS refund_count,
    ROUND(SUM(r.amount), 2)                                         AS total_refunds,
    ROUND(SUM(o.gross_revenue), 2)                                  AS gross_revenue,
    ROUND(SUM(r.amount) / NULLIF(SUM(o.gross_revenue), 0) * 100, 2) AS refund_rate_pct,
    COUNT(CASE WHEN r.is_over_refund THEN 1 END)                    AS over_refund_count
FROM main_marts.fct_refunds r
JOIN main_marts.fct_orders o ON r.order_id = o.order_id
JOIN main_marts.dim_date d ON r.date_id = d.date_id
GROUP BY d.year, d.month_number, d.month_name
ORDER BY d.year, d.month_number;
