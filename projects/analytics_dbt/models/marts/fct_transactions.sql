with valid_transactions as (
    select
        transaction_id,
        md5(customer_id) as customer_key,
        cast(strftime(transaction_at, '%Y%m%d') as integer) as date_key,
        amount,
        currency,
        status,
        transaction_at,
        source_updated_at
    from {{ ref('stg_transactions') }}
)

select * from valid_transactions

{% if var('inject_invalid_relationship', false) %}
union all
select
    'T_INVALID_RELATIONSHIP' as transaction_id,
    md5('C_ORPHAN') as customer_key,
    19000101 as date_key,
    cast(1.00 as decimal(18, 2)) as amount,
    'MXN' as currency,
    'COMPLETED' as status,
    timestamp '1900-01-01 00:00:00' as transaction_at,
    timestamp '1900-01-01 00:00:00' as source_updated_at
{% endif %}
