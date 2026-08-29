-- Mart: finance reconciliation
-- Monthly revenue → payments → refunds → payout reconciliation
-- Grain: year_month × platform

with payouts as (
    select * from "warehouse"."main_marts"."fct_payouts"
),

-- Monthly order revenue
monthly_revenue as (
    select
        date_trunc('month', date_id)            as year_month,
        sum(gross_revenue)                      as gross_revenue,
        sum(total_discount)                     as total_discounts,
        sum(total_refunds)                      as total_refunds,
        sum(net_revenue)                        as net_revenue,
        count(distinct order_id)                as order_count
    from "warehouse"."main_marts"."fct_orders"
    where order_status not in ('cancelled', 'unknown')
    group by date_trunc('month', date_id)
),

-- Monthly payment totals
monthly_payments as (
    select
        date_trunc('month', date_id)            as year_month,
        sum(amount)                             as total_collected,
        sum(case when status = 'failed' then 1 else 0 end) as failed_payments,
        count(*)                                as payment_count
    from "warehouse"."main_marts"."fct_payments"
    group by date_trunc('month', date_id)
)

select
    date_trunc('month', p.period_start)         as year_month,
    p.platform,

    -- Revenue side
    coalesce(r.gross_revenue, 0)                as gross_revenue,
    coalesce(r.total_discounts, 0)              as total_discounts,
    coalesce(r.total_refunds, 0)                as total_refunds,
    coalesce(r.net_revenue, 0)                  as net_revenue,
    coalesce(r.order_count, 0)                  as order_count,

    -- Payment side
    coalesce(py.total_collected, 0)             as total_collected,
    coalesce(py.failed_payments, 0)             as failed_payments,
    coalesce(py.payment_count, 0)               as payment_count,

    -- Payout
    p.gross_sales,
    p.fees,
    p.refunds                                   as payout_refunds,
    p.adjustments,
    p.net_payout,

    -- Reconciliation
    p.payout_variance,
    p.reconciliation_status,

    -- Revenue vs payment gap
    coalesce(r.net_revenue, 0) - coalesce(py.total_collected, 0)
                                                as revenue_payment_gap

from payouts p
left join monthly_revenue  r  on date_trunc('month', p.period_start) = r.year_month
left join monthly_payments py on date_trunc('month', p.period_start) = py.year_month