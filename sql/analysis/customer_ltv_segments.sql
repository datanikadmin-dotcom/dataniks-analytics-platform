-- Customer lifetime value by segment and cohort
SELECT
    segment,
    value_tier,
    DATE_TRUNC('month', signup_date)        AS signup_cohort,
    COUNT(customer_id)                       AS customer_count,
    ROUND(AVG(lifetime_revenue), 2)          AS avg_ltv,
    ROUND(AVG(order_count), 1)               AS avg_orders,
    COUNT(CASE WHEN is_repeat_customer THEN 1 END) AS repeat_customers,
    ROUND(
        COUNT(CASE WHEN is_repeat_customer THEN 1 END) * 100.0 / COUNT(customer_id), 1
    )                                        AS repeat_rate_pct
FROM main_marts.dim_customer
WHERE lifetime_revenue > 0
GROUP BY segment, value_tier, DATE_TRUNC('month', signup_date)
ORDER BY signup_cohort, avg_ltv DESC;
