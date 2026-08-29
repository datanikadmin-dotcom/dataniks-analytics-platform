-- Dimension: date spine
-- Grain: one row per calendar date (2023-01-01 → 2024-12-31)
-- Uses DuckDB native range() — no dbt_utils required.

with date_spine as (
    select unnest(generate_series(
        date '2023-01-01',
        date '2024-12-31',
        interval '1' day
    ))::date as date_day
),

enriched as (
    select
        date_day                                               as date_id,
        date_day                                               as full_date,

        extract('year'    from date_day)::int                  as year,
        extract('quarter' from date_day)::int                  as quarter_number,
        extract('month'   from date_day)::int                  as month_number,
        extract('week'    from date_day)::int                  as week_of_year,
        extract('day'     from date_day)::int                  as day_of_month,
        extract('dow'     from date_day)::int                  as day_of_week,

        'Q' || extract('quarter' from date_day)::varchar       as quarter_label,
        strftime(date_day, '%B')                               as month_name,
        strftime(date_day, '%b')                               as month_abbr,
        strftime(date_day, '%A')                               as day_name,

        case when extract('dow' from date_day) in (0, 6)
             then true else false end                          as is_weekend,

        extract('year'    from date_day)::int                  as fiscal_year,
        extract('quarter' from date_day)::int                  as fiscal_quarter

    from date_spine
)

select * from enriched
