
  
  create view "warehouse"."main_intermediate"."int_inventory_movements__dbt_tmp" as (
    -- Intermediate: inventory health per product × warehouse (latest snapshot)
-- Grain: one row per product_id + warehouse_id

with inv as (
    select
        product_id,
        warehouse_id,
        warehouse,
        date,
        closing_qty,
        unit_cost,
        inventory_value,
        row_number() over (
            partition by product_id, warehouse_id
            order by date desc
        ) as rn
    from "warehouse"."main_staging"."stg_inventory"
)

select
    product_id,
    warehouse_id,
    warehouse,
    date                    as snapshot_date,
    closing_qty             as available_qty,
    unit_cost,
    inventory_value,

    case
        when closing_qty = 0        then 'out_of_stock'
        when closing_qty < 10       then 'low_stock'
        else                             'in_stock'
    end                     as stock_status

from inv
where rn = 1
  );
