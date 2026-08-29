-- Staging: order_items
-- Removes orphan records whose order_id doesn't exist in stg_orders.

with source as (
    select * from {{ source('raw', 'raw_order_items') }}
),

valid_orders as (
    select order_id from {{ ref('stg_orders') }}
),

deduped as (
    select *,
           row_number() over (
               partition by order_item_id
               order by _ingested_at desc
           ) as _row_num
    from source
    where order_item_id is not null
),

cleaned as (
    select
        oi.order_item_id,
        oi.order_id,
        oi.product_id,
        cast(oi.quantity     as integer)    as quantity,
        cast(oi.unit_price   as double)     as unit_price,
        cast(oi.discount     as double)     as discount,
        cast(oi.cost         as double)     as cost,
        cast(oi.revenue      as double)     as revenue,
        cast(oi.gross_profit as double)     as gross_profit,

        oi._ingested_at,
        oi._source,
        oi._batch_id
    from deduped oi
    inner join valid_orders vo on oi.order_id = vo.order_id
    where oi._row_num = 1
      and oi.quantity > 0
      and oi.unit_price > 0
)

select * from cleaned
