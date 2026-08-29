-- Mart: customer
-- One row per customer with full lifetime metrics + cohort info

with customers as (
    select * from {{ ref('dim_customer') }}
)

select
    customer_id,
    full_name,
    email,
    signup_date,
    country,
    state,
    city,
    customer_segment,
    acquisition_channel,
    value_tier,

    order_count,
    first_order_date,
    last_order_date,
    lifetime_revenue,
    lifetime_gross_profit,
    avg_order_value,
    is_repeat_customer,

    -- Cohort month (based on signup)
    date_trunc('month', signup_date)        as signup_cohort,

    -- Days since last order (as of end of data range)
    case when last_order_date is not null
         then datediff('day', last_order_date, date '2024-12-31')
         else null end                      as days_since_last_order,

    -- RFM-style recency flag
    case
        when last_order_date >= date '2024-10-01' then 'Active'
        when last_order_date >= date '2024-01-01' then 'Lapsing'
        else                                           'Churned'
    end                                     as recency_status

from customers
