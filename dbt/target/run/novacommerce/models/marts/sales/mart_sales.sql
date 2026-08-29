
  
    
    

    create  table
      "warehouse"."main_marts"."mart_sales__dbt_tmp"
  
    as (
      -- Mart: sales
-- Monthly sales summary by channel
-- Grain: year_month × channel_id

with orders as (
    select * from "warehouse"."main_marts"."fct_orders"
    where order_status not in ('cancelled', 'unknown')
),

channels as (
    select * from "warehouse"."main_marts"."dim_channel"
)

select
    date_trunc('month', o.date_id)          as year_month,
    o.channel_id,
    c.channel_name,
    c.channel_type,
    c.channel_group,

    count(distinct o.order_id)              as order_count,
    sum(o.gross_revenue)                    as gross_revenue,
    sum(o.total_discount)                   as total_discounts,
    sum(o.total_refunds)                    as total_refunds,
    sum(o.net_revenue)                      as net_revenue,
    sum(o.total_cost)                       as total_cost,
    sum(o.gross_profit)                     as gross_profit,

    case when sum(o.net_revenue) > 0
         then sum(o.gross_profit) / sum(o.net_revenue)
         else null end                      as gross_margin_pct,

    case when count(distinct o.order_id) > 0
         then sum(o.net_revenue) / count(distinct o.order_id)
         else null end                      as aov,

    sum(o.unit_count)                       as units_sold,
    sum(o.has_refund::int)                  as refund_order_count

from orders o
left join channels c on o.channel_id = c.channel_id
group by
    date_trunc('month', o.date_id),
    o.channel_id, c.channel_name, c.channel_type, c.channel_group
    );
  
  