-- Intermediate: campaign performance aggregated to campaign × month
-- Grain: one row per campaign_id + channel + year_month

with ad_spend as (
    select * from {{ ref('stg_ad_spend') }}
)

select
    campaign_id,
    campaign_name,
    channel_id,
    channel,
    date_trunc('month', date)       as year_month,

    sum(impressions)                as total_impressions,
    sum(clicks)                     as total_clicks,
    sum(conversions)                as total_conversions,
    sum(spend)                      as total_spend,
    sum(attributed_revenue)         as total_attributed_revenue,

    -- Derived metrics
    case when sum(spend) > 0
         then sum(attributed_revenue) / sum(spend)
         else null end              as roas,

    case when sum(impressions) > 0
         then cast(sum(clicks) as double) / sum(impressions)
         else null end              as avg_ctr,

    case when sum(clicks) > 0
         then cast(sum(conversions) as double) / sum(clicks)
         else null end              as avg_cvr,

    case when sum(conversions) > 0
         then sum(spend) / sum(conversions)
         else null end              as cost_per_conversion

from ad_spend
group by campaign_id, campaign_name, channel_id, channel, date_trunc('month', date)
