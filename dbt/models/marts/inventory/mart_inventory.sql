-- Mart: inventory
-- Product × warehouse stock health (latest snapshot)

with inv as (
    select * from {{ ref('int_inventory_movements') }}
),

products as (
    select product_id, product_name, category, subcategory, brand
    from {{ ref('dim_product') }}
),

warehouses as (
    select warehouse_id, warehouse_code, region
    from {{ ref('dim_warehouse') }}
)

select
    i.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    p.brand,
    i.warehouse_id,
    w.warehouse_code,
    w.region,
    i.snapshot_date,
    i.available_qty,
    i.unit_cost,
    i.inventory_value,
    i.stock_status

from inv i
left join products   p on i.product_id   = p.product_id
left join warehouses w on i.warehouse_id = w.warehouse_id
