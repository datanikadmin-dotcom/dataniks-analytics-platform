-- Mart: marketing
-- Campaign performance by month with ROAS, CAC, and attribution

with campaign_perf as (
    select * from "warehouse"."main_intermediate"."int_campaign_performance"
),

-- New customers acquired per month (approximation: first-order customers)
new_customers_by_month as (
    select
        date_trunc('month', first_order_date)   as year_month,
        acquisition_channel,
        count(*)                                as new_customers
    from "warehouse"."main_intermediate"."int_customer_orders"
    where first_order_date is not null
    group by date_trunc('month', first_order_date), acquisition_channel
)

select
    cp.year_month,
    cp.campaign_id,
    cp.campaign_name,
    cp.channel_id,
    cp.channel,

    cp.total_impressions,
    cp.total_clicks,
    cp.total_conversions,
    cp.total_spend,
    cp.total_attributed_revenue,
    cp.roas,
    cp.avg_ctr,
    cp.avg_cvr,
    cp.cost_per_conversion,

    -- Approximate CAC: spend / new customers in that channel that month
    case when coalesce(nc.new_customers, 0) > 0
         then cp.total_spend / nc.new_customers
         else null end                          as approx_cac

from campaign_perf cp
left join new_customers_by_month nc
    on  cp.year_month = nc.year_month
    and lower(cp.channel) = lower(nc.acquisition_channel)