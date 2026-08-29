-- Intermediate: payment vs order reconciliation
-- Grain: one row per order_id

with orders as (
    select order_id, total_amount as order_total
    from "warehouse"."main_staging"."stg_orders"
),

payments as (
    select
        order_id,
        sum(case when status = 'completed' then amount else 0 end) as paid_amount,
        count(*)                                                    as payment_count
    from "warehouse"."main_staging"."stg_payments"
    group by order_id
),

refunds as (
    select
        order_id,
        sum(amount) as refund_amount
    from "warehouse"."main_staging"."stg_refunds"
    where status = 'completed'
    group by order_id
)

select
    o.order_id,
    o.order_total,
    coalesce(p.paid_amount,   0) as paid_amount,
    coalesce(r.refund_amount, 0) as refund_amount,
    coalesce(p.payment_count, 0) as payment_count,

    o.order_total - coalesce(p.paid_amount, 0) as payment_variance,

    case
        when abs(o.order_total - coalesce(p.paid_amount, 0)) <= 1.0
        then 'MATCHED'
        when abs(o.order_total - coalesce(p.paid_amount, 0)) <= 100.0
        then 'WARNING'
        else 'EXCEPTION'
    end                                         as reconciliation_status,

    -- Flag over-refunds
    case
        when coalesce(r.refund_amount, 0) > coalesce(p.paid_amount, 0)
        then true else false
    end                                         as has_over_refund,

    -- Flag duplicate payments
    case
        when coalesce(p.payment_count, 0) > 1
        then true else false
    end                                         as has_duplicate_payment

from orders o
left join payments p on o.order_id = p.order_id
left join refunds  r on o.order_id = r.order_id