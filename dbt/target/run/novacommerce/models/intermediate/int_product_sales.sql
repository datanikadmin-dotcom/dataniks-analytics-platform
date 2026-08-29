
  
  create view "warehouse"."main_intermediate"."int_product_sales__dbt_tmp" as (
    -- Intermediate: product sales summary
-- Grain: one row per product_id

with items as (
    select * from "warehouse"."main_staging"."stg_order_items"
),

orders as (
    select order_id, order_date
    from "warehouse"."main_staging"."stg_orders"
    where order_status not in ('cancelled', 'unknown')
)

select
    i.product_id,

    count(distinct o.order_id)  as order_count,
    sum(i.quantity)             as units_sold,
    sum(i.revenue)              as gross_revenue,
    sum(i.discount)             as total_discounts,
    sum(i.cost)                 as total_cost,
    sum(i.gross_profit)         as total_gross_profit,

    avg(i.unit_price)           as avg_selling_price,

    case
        when sum(i.revenue) > 0
        then sum(i.gross_profit) / sum(i.revenue)
        else null
    end                         as gross_margin_pct,

    min(o.order_date)           as first_sold_date,
    max(o.order_date)           as last_sold_date

from items i
inner join orders o on i.order_id = o.order_id
group by i.product_id
  );
