
  
    
    

    create  table
      "warehouse"."main_marts"."fct_orders__dbt_tmp"
  
    as (
      -- Fact: orders
-- Grain: one row per order_id
-- Metrics: revenue, profit, refunds, order counts

select
    o.order_id,
    o.customer_id,
    o.order_date                            as date_id,
    o.channel_id,
    o.order_status,

    o.gross_revenue,
    o.total_discount,
    o.total_refunds,
    o.net_revenue,
    o.total_cost,
    o.gross_profit,

    case when o.net_revenue > 0
         then o.gross_profit / o.net_revenue
         else null end                      as gross_margin_pct,

    o.item_count,
    o.unit_count,
    o.refund_count,
    o.subtotal,
    o.order_discount,
    o.tax,
    o.shipping,
    o.total_amount,

    -- Order-level flags
    case when o.order_status = 'refunded' or o.refund_count > 0
         then true else false end           as has_refund,

    case when o.refund_count > 1
         then true else false end           as has_multiple_refunds

from "warehouse"."main_intermediate"."int_order_revenue" o
    );
  
  