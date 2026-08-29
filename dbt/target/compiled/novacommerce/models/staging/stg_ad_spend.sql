-- Staging: ad spend (merged from all advertising connectors)

with source as (
    select * from "warehouse"."raw"."raw_ad_spend"
),

deduped as (
    select *,
           row_number() over (
               partition by ad_record_id
               order by _ingested_at desc
           ) as _row_num
    from source
    where ad_record_id is not null
),

cleaned as (
    select
        ad_record_id,
        cast(date           as date)    as date,
        cast(campaign_id    as integer) as campaign_id,
        campaign_name,
        cast(channel_id     as integer) as channel_id,
        channel,
        cast(impressions        as integer) as impressions,
        cast(clicks             as integer) as clicks,
        cast(conversions        as integer) as conversions,
        cast(spend              as double)  as spend,
        cast(attributed_revenue as double)  as attributed_revenue,

        -- Derived: ROAS
        case
            when spend > 0
            then attributed_revenue / spend
            else null
        end                             as roas,

        -- Derived: CTR
        case
            when impressions > 0
            then cast(clicks as double) / impressions
            else null
        end                             as ctr,

        _ingested_at,
        _source,
        _batch_id
    from deduped
    where _row_num    = 1
      and spend       >= 0
      and impressions >= 0
      and clicks      <= impressions
)

select * from cleaned