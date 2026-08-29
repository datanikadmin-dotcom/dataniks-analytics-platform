-- Intermediate: customer-level order history
-- Grain: one row per customer_id

with order_revenue as (
    select * from "warehouse"."main_intermediate"."int_order_revenue"
    where order_status not in ('cancelled', 'unknown')
),

customers as (
    select * from "warehouse"."main_staging"."stg_customers"
)

select
    c.customer_id,
    c.customer_segment,
    c.acquisition_channel,
    c.signup_date,
    c.country,
    c.state,

    count(distinct o.order_id)              as order_count,
    min(o.order_date)                       as first_order_date,
    max(o.order_date)                       as last_order_date,
    sum(o.net_revenue)                      as lifetime_revenue,
    sum(o.gross_profit)                     as lifetime_gross_profit,
    sum(o.total_refunds)                    as lifetime_refunds,
    avg(o.net_revenue)                      as avg_order_value,

    -- Repeat purchase flag
    case when count(distinct o.order_id) > 1 then true else false end as is_repeat_customer,

    -- Days between first and last order
    case
        when count(distinct o.order_id) > 1
        then datediff('day', min(o.order_date), max(o.order_date))
        else 0
    end                                     as active_days

from customers c
left join order_revenue o on c.customer_id = o.customer_id
group by
    c.customer_id, c.customer_segment, c.acquisition_channel,
    c.signup_date, c.country, c.state