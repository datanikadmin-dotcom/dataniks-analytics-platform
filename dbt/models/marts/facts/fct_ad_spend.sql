-- Fact: ad spend
-- Grain: one row per ad_record_id (campaign × channel × date)

select
    ad_record_id,
    date                            as date_id,
    campaign_id,
    campaign_name,
    channel_id,
    channel,
    impressions,
    clicks,
    conversions,
    spend,
    attributed_revenue,
    roas,
    ctr

from {{ ref('stg_ad_spend') }}
