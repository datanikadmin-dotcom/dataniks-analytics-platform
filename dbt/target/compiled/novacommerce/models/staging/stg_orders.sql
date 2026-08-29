-- Staging: orders
-- Deduplicates, normalises status, enforces non-negative amounts.

with source as (
    select * from "warehouse"."raw"."raw_orders"
),

deduped as (
    select *,
           row_number() over (
               partition by order_id
               order by _ingested_at desc
           ) as _row_num
    from source
    where order_id is not null
),

cleaned as (
    select
        order_id,
        customer_id,
        cast(order_date  as date)                        as order_date,
        cast(channel_id  as integer)                     as channel_id,
        channel,

        case
            when lower(order_status) in (
                'completed','processing','shipped','refunded','cancelled'
            ) then lower(order_status)
            else 'unknown'                               -- absorb invalid statuses
        end                                              as order_status,

        cast(subtotal     as double)                     as subtotal,
        cast(discount     as double)                     as discount,
        cast(tax          as double)                     as tax,
        cast(shipping     as double)                     as shipping,
        cast(total_amount as double)                     as total_amount,

        _ingested_at,
        _source,
        _batch_id
    from deduped
    where _row_num    = 1
      and total_amount >= 0
)

select * from cleaned