-- Fact: shipments
-- Grain: one row per shipment_id

select
    s.shipment_id,
    s.order_id,
    s.warehouse_id,
    s.shipped_date                          as date_id,
    s.carrier,
    s.shipment_status,
    s.is_on_time,

    s.estimated_delivery_date,
    s.delivered_date,

    -- Days in transit
    case when s.delivered_date is not null
         then datediff('day', s.shipped_date, s.delivered_date)
         else null end                      as transit_days,

    -- Days late (positive = late)
    case when s.delivered_date is not null and s.estimated_delivery_date is not null
         then datediff('day', s.estimated_delivery_date, s.delivered_date)
         else null end                      as days_late

from {{ ref('stg_shipments') }} s
