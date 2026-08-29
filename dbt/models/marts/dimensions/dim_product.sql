-- Dimension: product
-- Grain: one row per product_id

with products as (
    select * from {{ ref('stg_products') }}
),

sales as (
    select * from {{ ref('int_product_sales') }}
)

select
    p.product_id,
    p.sku,
    p.product_name,
    p.category,
    p.subcategory,
    p.brand,
    p.supplier,
    p.unit_cost,
    p.list_price,

    -- Derived
    p.list_price - p.unit_cost                              as standard_margin,
    case when p.list_price > 0
         then (p.list_price - p.unit_cost) / p.list_price
         else null end                                      as standard_margin_pct,

    -- Sales performance
    coalesce(s.units_sold,        0)                        as units_sold,
    coalesce(s.gross_revenue,     0)                        as gross_revenue,
    coalesce(s.total_gross_profit, 0)                       as total_gross_profit,
    coalesce(s.gross_margin_pct,  0)                        as realised_margin_pct,

    -- Category group for Power BI hierarchy
    p.category || ' > ' || p.subcategory                   as category_path

from products p
left join sales s on p.product_id = s.product_id
