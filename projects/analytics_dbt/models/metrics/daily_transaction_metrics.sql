select
    date_key,
    currency,
    status,
    count(*) as transaction_count,
    sum(amount) as gross_amount,
    avg(amount) as average_amount
from {{ ref('fct_transactions') }}
group by date_key, currency, status
