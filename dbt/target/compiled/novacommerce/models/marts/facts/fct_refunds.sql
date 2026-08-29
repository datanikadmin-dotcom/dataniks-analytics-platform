-- Fact: refunds
-- Grain: one row per refund_id

with refunds as (
    select * from "warehouse"."main_staging"."stg_refunds"
),

orders as (
    select order_id, customer_id, channel_id, order_date
    from "warehouse"."main_staging"."stg_orders"
),

payments as (
    select order_id, sum(amount) as total_paid
    from "warehouse"."main_staging"."stg_payments"
    where status = 'completed'
    group by order_id
)

select
    r.refund_id,
    r.order_id,
    o.customer_id,
    o.channel_id,
    r.refund_date                           as date_id,
    r.reason,
    r.status,
    r.amount,

    coalesce(p.total_paid, 0)               as order_paid_amount,

    -- Flag refunds that exceed what was paid
    case when r.amount > coalesce(p.total_paid, 0)
         then true else false end           as is_over_refund

from refunds r
left join orders   o on r.order_id = o.order_id
left join payments p on r.order_id = p.order_id