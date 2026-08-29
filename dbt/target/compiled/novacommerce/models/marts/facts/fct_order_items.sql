-- Fact: order_items
-- Grain: one row per order_item_id

with items as (
    select * from "warehouse"."main_staging"."stg_order_items"
),

orders as (
    select order_id, order_date, channel_id, customer_id, order_status
    from "warehouse"."main_staging"."stg_orders"
),

products as (
    select product_id, category, subcategory, brand
    from "warehouse"."main_staging"."stg_products"
)

select
    i.order_item_id,
    i.order_id,
    i.product_id,
    o.customer_id,
    o.order_date                        as date_id,
    o.channel_id,
    p.category,
    p.subcategory,
    p.brand,

    i.quantity,
    i.unit_price,
    i.discount,
    i.cost,
    i.revenue,
    i.gross_profit,

    case when i.revenue > 0
         then i.gross_profit / i.revenue
         else null end                  as item_margin_pct,

    -- Effective price per unit after discount
    case when i.quantity > 0
         then (i.revenue) / i.quantity
         else null end                  as effective_unit_price

from items i
inner join orders   o on i.order_id   = o.order_id
left  join products p on i.product_id = p.product_id