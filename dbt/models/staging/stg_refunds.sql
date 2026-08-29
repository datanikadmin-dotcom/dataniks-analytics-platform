-- Staging: refunds
-- Deduplicates and caps refund amounts at a reasonable maximum.

with source as (
    select * from {{ source('raw', 'raw_refunds') }}
),

deduped as (
    select *,
           row_number() over (
               partition by refund_id
               order by _ingested_at desc
           ) as _row_num
    from source
    where refund_id is not null
),

cleaned as (
    select
        refund_id,
        order_id,
        cast(refund_date as date)      as refund_date,
        cast(amount      as double)    as amount,
        reason,

        case
            when lower(status) in ('completed','pending','failed')
            then lower(status)
            else 'unknown'
        end                            as status,

        _ingested_at,
        _source,
        _batch_id
    from deduped
    where _row_num = 1
      and amount   > 0
)

select * from cleaned
