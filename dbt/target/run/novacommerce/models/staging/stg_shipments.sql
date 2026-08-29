
  
  create view "warehouse"."main_staging"."stg_shipments__dbt_tmp" as (
    -- Staging: shipments

with source as (
    select * from "warehouse"."raw"."raw_shipments"
),

cleaned as (
    select
        shipment_id,
        order_id,
        cast(warehouse_id as integer)         as warehouse_id,
        warehouse,
        carrier,
        cast(shipped_date           as date)  as shipped_date,
        cast(estimated_delivery_date as date) as estimated_delivery_date,
        cast(delivered_date          as date) as delivered_date,

        case
            when lower(shipment_status) in (
                'delivered','delivered_late','in_transit','lost','returned'
            ) then lower(shipment_status)
            else 'unknown'
        end                                   as shipment_status,

        -- Derived flag: did we deliver on time?
        case
            when delivered_date is not null
             and delivered_date <= estimated_delivery_date
            then true
            else false
        end                                   as is_on_time,

        _ingested_at,
        _source,
        _batch_id
    from source
    where shipment_id is not null
      and order_id    is not null
)

select * from cleaned
  );
