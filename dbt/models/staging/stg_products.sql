-- Staging: products
-- Enforces positive prices, non-null SKUs.

with source as (
    select * from {{ source('raw', 'raw_products') }}
),

cleaned as (
    select
        product_id,
        sku,
        trim(product_name)          as product_name,
        category,
        subcategory,
        brand,
        cast(unit_cost   as double) as unit_cost,
        cast(list_price  as double) as list_price,
        supplier,

        _ingested_at,
        _source,
        _batch_id
    from source
    where product_id  is not null
      and sku         is not null   -- remove corrupted null-SKU rows
      and list_price  > 0
      and unit_cost   > 0
      and unit_cost   < list_price
)

select * from cleaned
