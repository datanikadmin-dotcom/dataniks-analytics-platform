-- Fact: payouts + reconciliation
-- Grain: one row per payout_id

with payouts as (
    select * from {{ ref('stg_payouts') }}
),

-- Aggregate order revenue per period + platform (approximation using all platforms equally)
period_revenue as (
    select
        date_trunc('month', order_date)  as period_month,
        sum(net_revenue)                 as total_net_revenue,
        sum(total_refunds)               as total_refunds
    from {{ ref('int_order_revenue') }}
    where order_status not in ('cancelled', 'unknown')
    group by date_trunc('month', order_date)
)

select
    p.payout_id,
    p.payout_date                           as date_id,
    p.platform,
    p.period_start,
    p.period_end,
    p.gross_sales,
    p.fees,
    p.refunds,
    p.adjustments,
    p.net_payout,

    -- Expected payout approximation
    coalesce(r.total_net_revenue, 0)        as period_gross_revenue,
    coalesce(r.total_refunds,     0)        as period_refunds,

    -- Variance: positive = over-paid, negative = under-paid
    p.net_payout - (coalesce(r.total_net_revenue, 0) - p.fees - coalesce(r.total_refunds, 0))
                                            as payout_variance,

    case
        when abs(p.net_payout - (coalesce(r.total_net_revenue, 0) - p.fees - coalesce(r.total_refunds, 0))) <= 1.0
        then 'MATCHED'
        when abs(p.net_payout - (coalesce(r.total_net_revenue, 0) - p.fees - coalesce(r.total_refunds, 0))) <= 100.0
        then 'WARNING'
        else 'EXCEPTION'
    end                                     as reconciliation_status

from payouts p
left join period_revenue r
    on date_trunc('month', p.period_start) = r.period_month
