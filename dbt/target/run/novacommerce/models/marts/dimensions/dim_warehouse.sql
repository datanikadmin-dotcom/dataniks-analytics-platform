
  
    
    

    create  table
      "warehouse"."main_marts"."dim_warehouse__dbt_tmp"
  
    as (
      -- Dimension: warehouse (static)
-- Grain: one row per warehouse_id

select * from (values
    (1, 'WH-EAST',    'East',    'New York',       'NY'),
    (2, 'WH-WEST',    'West',    'Los Angeles',    'CA'),
    (3, 'WH-CENTRAL', 'Central', 'Chicago',        'IL'),
    (4, 'WH-SOUTH',   'South',   'Dallas',         'TX'),
    (5, 'WH-NORTH',   'North',   'Minneapolis',    'MN')
) as t(warehouse_id, warehouse_code, region, city, state)
    );
  
  