-- Dimension: customer
-- Grain: one row per customer_id (SCD Type 1)

with customers as (
    select * from "warehouse"."main_staging"."stg_customers"
),

customer_stats as (
    select * from "warehouse"."main_intermediate"."int_customer_orders"
)

select
    c.customer_id,
    c.first_name,
    c.last_name,
    c.first_name || ' ' || c.last_name     as full_name,
    c.email,
    c.signup_date,
    c.country,
    c.state,
    c.city,
    c.customer_segment,
    c.acquisition_channel,

    -- Order stats
    coalesce(s.order_count, 0)             as order_count,
    s.first_order_date,
    s.last_order_date,
    coalesce(s.lifetime_revenue,  0)       as lifetime_revenue,
    coalesce(s.lifetime_gross_profit, 0)   as lifetime_gross_profit,
    coalesce(s.avg_order_value, 0)         as avg_order_value,
    coalesce(s.is_repeat_customer, false)  as is_repeat_customer,

    -- Customer value tier
    case
        when coalesce(s.lifetime_revenue, 0) >= 1000 then 'High'
        when coalesce(s.lifetime_revenue, 0) >= 300  then 'Medium'
        else                                               'Low'
    end                                    as value_tier

from customers c
left join customer_stats s on c.customer_id = s.customer_id