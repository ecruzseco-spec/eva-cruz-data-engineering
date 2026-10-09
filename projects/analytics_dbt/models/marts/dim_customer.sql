select
    md5(customer_id) as customer_key,
    customer_id,
    min(transaction_at) as first_transaction_at,
    max(transaction_at) as latest_transaction_at,
    count(*) as lifetime_transaction_count
from {{ ref('stg_transactions') }}
group by customer_id
