select
    cast(transaction_id as varchar) as transaction_id,
    cast(customer_id as varchar) as customer_id,
    cast(amount as decimal(18, 2)) as amount,
    upper(cast(currency as varchar)) as currency,
    upper(cast(status as varchar)) as status,
    cast(transaction_at as timestamp) as transaction_at,
    cast(source_updated_at as timestamp) as source_updated_at,
    cast(first_batch_id as varchar) as first_batch_id,
    cast(last_batch_id as varchar) as last_batch_id
from {{ source('curated', 'transactions') }}
