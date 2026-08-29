-- Staging: inventory
-- Enforces non-negative closing qty, standardises warehouse references.

with source as (
    select * from "warehouse"."raw"."raw_inventory"
),

cleaned as (
    select
        inventory_id,
        cast(date           as date)    as date,
        product_id,
        cast(warehouse_id   as integer) as warehouse_id,
        warehouse,
        cast(opening_qty    as integer) as opening_qty,
        cast(received_qty   as integer) as received_qty,
        cast(sold_qty       as integer) as sold_qty,
        cast(adjustment_qty as integer) as adjustment_qty,

        -- Clamp negative closing qty to 0 (flag as data-quality issue elsewhere)
        greatest(cast(closing_qty as integer), 0) as closing_qty,

        cast(unit_cost        as double) as unit_cost,
        cast(inventory_value  as double) as inventory_value,

        _ingested_at,
        _source,
        _batch_id
    from source
    where inventory_id is not null
      and product_id   is not null
      and date         is not null
)

select * from cleaned