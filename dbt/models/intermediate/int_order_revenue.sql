-- Intermediate: order-level revenue summary
-- Grain: one row per order_id

with orders as (
    select * from {{ ref('stg_orders') }}
),

items as (
    select
        order_id,
        sum(revenue)      as gross_revenue,
        sum(discount)     as total_discount,
        sum(cost)         as total_cost,
        sum(gross_profit) as total_gross_profit,
        count(*)          as item_count,
        sum(quantity)     as unit_count
    from {{ ref('stg_order_items') }}
    group by order_id
),

refunds as (
    select
        order_id,
        sum(amount) as total_refund_amount,
        count(*)    as refund_count
    from {{ ref('stg_refunds') }}
    where status = 'completed'
    group by order_id
)

select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.channel_id,
    o.channel,
    o.order_status,

    coalesce(i.gross_revenue,      0.0) as gross_revenue,
    coalesce(i.total_discount,     0.0) as total_discount,
    coalesce(r.total_refund_amount, 0.0) as total_refunds,

    coalesce(i.gross_revenue, 0.0)
        - coalesce(i.total_discount, 0.0)
        - coalesce(r.total_refund_amount, 0.0) as net_revenue,

    coalesce(i.total_cost,         0.0) as total_cost,

    coalesce(i.gross_revenue, 0.0)
        - coalesce(i.total_discount, 0.0)
        - coalesce(r.total_refund_amount, 0.0)
        - coalesce(i.total_cost, 0.0)          as gross_profit,

    coalesce(i.item_count, 0)  as item_count,
    coalesce(i.unit_count, 0)  as unit_count,
    coalesce(r.refund_count, 0) as refund_count,

    o.subtotal,
    o.discount as order_discount,
    o.tax,
    o.shipping,
    o.total_amount

from orders o
left join items   i on o.order_id = i.order_id
left join refunds r on o.order_id = r.order_id
