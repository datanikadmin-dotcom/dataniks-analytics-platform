
  
  create view "warehouse"."main_staging"."stg_customers__dbt_tmp" as (
    -- Staging: customers
-- Deduplicates raw feed, normalises types, standardises nulls.

with source as (
    select * from "warehouse"."raw"."raw_customers"
),

deduped as (
    select *,
           row_number() over (
               partition by customer_id
               order by _ingested_at desc
           ) as _row_num
    from source
    where customer_id is not null
),

cleaned as (
    select
        customer_id,
        trim(first_name)                           as first_name,
        trim(last_name)                            as last_name,
        lower(trim(email))                         as email,
        cast(signup_date as date)                  as signup_date,
        upper(trim(country))                       as country,
        upper(trim(state))                         as state,
        trim(city)                                 as city,
        customer_segment,
        acquisition_channel,

        -- audit columns
        _ingested_at,
        _source,
        _batch_id
    from deduped
    where _row_num = 1
      and email is not null          -- remove corrupted null-email rows
)

select * from cleaned
  );
