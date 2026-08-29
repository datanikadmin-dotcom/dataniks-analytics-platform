-- Fact: payments
-- Grain: one row per payment_id

with payments as (
    select * from {{ ref('stg_payments') }}
),

reconciliation as (
    select order_id, reconciliation_status, payment_variance, has_duplicate_payment
    from {{ ref('int_payment_reconciliation') }}
)

select
    p.payment_id,
    p.order_id,
    p.payment_date                          as date_id,
    p.payment_method,
    p.status,
    p.amount,

    coalesce(r.reconciliation_status, 'UNKNOWN')    as reconciliation_status,
    coalesce(r.payment_variance, 0)                 as payment_variance,
    coalesce(r.has_duplicate_payment, false)         as is_duplicate

from payments p
left join reconciliation r on p.order_id = r.order_id
