-- ROAS and CAC by platform and campaign (monthly)
SELECT
    d.year,
    d.month_name,
    a.platform,
    a.campaign_name,
    ROUND(SUM(a.spend), 2)                                          AS total_spend,
    ROUND(SUM(a.attributed_revenue), 2)                             AS attributed_revenue,
    ROUND(SUM(a.attributed_revenue) / NULLIF(SUM(a.spend), 0), 2)  AS roas,
    SUM(a.impressions)                                              AS impressions,
    SUM(a.clicks)                                                   AS clicks,
    SUM(a.conversions)                                              AS conversions,
    ROUND(SUM(a.clicks) * 100.0 / NULLIF(SUM(a.impressions), 0), 2) AS ctr_pct,
    ROUND(SUM(a.spend) / NULLIF(SUM(a.conversions), 0), 2)          AS cost_per_conversion
FROM main_marts.fct_ad_spend a
JOIN main_marts.dim_date d ON a.date_id = d.date_id
GROUP BY d.year, d.month_number, d.month_name, a.platform, a.campaign_name
ORDER BY d.year, d.month_number, roas DESC;
