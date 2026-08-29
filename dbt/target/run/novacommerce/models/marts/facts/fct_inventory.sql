
  
    
    

    create  table
      "warehouse"."main_marts"."fct_inventory__dbt_tmp"
  
    as (
      -- Fact: inventory
-- Grain: one row per inventory_id (product × warehouse × date)

select
    i.inventory_id,
    i.date                          as date_id,
    i.product_id,
    i.warehouse_id,
    i.opening_qty,
    i.received_qty,
    i.sold_qty,
    i.adjustment_qty,
    i.closing_qty,
    i.unit_cost,
    i.inventory_value,

    -- Stock health
    case
        when i.closing_qty = 0  then 'out_of_stock'
        when i.closing_qty < 10 then 'low_stock'
        else                         'in_stock'
    end                             as stock_status,

    -- Days of supply (naive: closing / avg daily sold)
    case
        when i.sold_qty > 0
        then cast(i.closing_qty as double) / (i.sold_qty / 30.0)
        else null
    end                             as days_of_supply

from "warehouse"."main_staging"."stg_inventory" i
    );
  
  