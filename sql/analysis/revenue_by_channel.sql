-- Monthly revenue breakdown by channel
SELECT
    d.year,
    d.month_name,
    c.channel_name,
    COUNT(DISTINCT o.order_id)          AS order_count,
    ROUND(SUM(o.gross_revenue), 2)      AS gross_revenue,
    ROUND(SUM(o.total_discount), 2)     AS total_discounts,
    ROUND(SUM(o.total_refunds), 2)      AS total_refunds,
    ROUND(SUM(o.net_revenue), 2)        AS net_revenue,
    ROUND(SUM(o.gross_profit), 2)       AS gross_profit,
    ROUND(AVG(o.net_revenue), 2)        AS aov,
    ROUND(SUM(o.gross_profit) / NULLIF(SUM(o.net_revenue), 0) * 100, 1) AS gross_margin_pct
FROM main_marts.fct_orders o
JOIN main_marts.dim_date d ON o.date_id = d.date_id
JOIN main_marts.dim_channel c ON o.channel_id = c.channel_id
GROUP BY d.year, d.month_number, d.month_name, c.channel_name
ORDER BY d.year, d.month_number, c.channel_name;
