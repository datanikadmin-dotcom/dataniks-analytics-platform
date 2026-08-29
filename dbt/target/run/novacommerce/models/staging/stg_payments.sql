
  
  create view "warehouse"."main_staging"."stg_payments__dbt_tmp" as (
    -- Staging: payments
-- Deduplicates, validates status, enforces positive amounts.

with source as (
    select * from "warehouse"."raw"."raw_payments"
),

deduped as (
    select *,
           row_number() over (
               partition by payment_id
               order by _ingested_at desc
           ) as _row_num
    from source
    where payment_id is not null
),

cleaned as (
    select
        payment_id,
        order_id,
        cast(payment_date as date)     as payment_date,
        payment_method,

        case
            when lower(status) in ('completed','failed','pending','refunded')
            then lower(status)
            else 'unknown'
        end                            as status,

        cast(amount as double)         as amount,

        _ingested_at,
        _source,
        _batch_id
    from deduped
    where _row_num = 1
      and amount > 0
)

select * from cleaned
  );
