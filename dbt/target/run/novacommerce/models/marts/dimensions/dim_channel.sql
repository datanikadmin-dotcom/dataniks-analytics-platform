
  
    
    

    create  table
      "warehouse"."main_marts"."dim_channel__dbt_tmp"
  
    as (
      -- Dimension: channel (static seed-like table)
-- Grain: one row per channel_id

select * from (values
    (1, 'organic_search', 'Organic',  'Search'),
    (2, 'paid_search',    'Paid',     'Search'),
    (3, 'social_media',   'Paid',     'Social'),
    (4, 'email',          'Owned',    'Email'),
    (5, 'direct',         'Organic',  'Direct'),
    (6, 'affiliate',      'Paid',     'Affiliate'),
    (7, 'referral',       'Organic',  'Referral')
) as t(channel_id, channel_name, channel_type, channel_group)
    );
  
  