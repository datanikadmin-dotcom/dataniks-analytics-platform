
  
  create view "warehouse"."main_staging"."stg_payouts__dbt_tmp" as (
    -- Staging: platform payouts

with source as (
    select * from "warehouse"."raw"."raw_payouts"
),

cleaned as (
    select
        payout_id,
        cast(payout_date  as date)   as payout_date,
        platform,
        cast(period_start as date)   as period_start,
        cast(period_end   as date)   as period_end,
        cast(gross_sales  as double) as gross_sales,
        cast(fees         as double) as fees,
        cast(refunds      as double) as refunds,
        cast(adjustments  as double) as adjustments,
        cast(net_payout   as double) as net_payout,

        _ingested_at,
        _source,
        _batch_id
    from source
    where payout_id is not null
)

select * from cleaned
  );
