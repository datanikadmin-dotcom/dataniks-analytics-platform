-- Financial integrity checks across the mart layer

-- 1. Over-refunds (refund > original payment)
SELECT 'over_refunds' AS check_name, COUNT(*) AS failed_records
FROM main_marts.fct_refunds
WHERE is_over_refund = TRUE

UNION ALL

-- 2. Negative net revenue orders
SELECT 'negative_net_revenue', COUNT(*)
FROM main_marts.fct_orders
WHERE net_revenue < 0

UNION ALL

-- 3. Payment exceptions
SELECT 'payment_exceptions', COUNT(*)
FROM main_marts.fct_payments
WHERE reconciliation_status = 'EXCEPTION'

UNION ALL

-- 4. Payout exceptions
SELECT 'payout_exceptions', COUNT(*)
FROM main_marts.fct_payouts
WHERE reconciliation_status = 'EXCEPTION'

UNION ALL

-- 5. Orders where gross_profit < -1000 (likely data error)
SELECT 'large_negative_profit', COUNT(*)
FROM main_marts.fct_orders
WHERE gross_profit < -1000;
