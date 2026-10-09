select distinct
    cast(strftime(transaction_at, '%Y%m%d') as integer) as date_key,
    cast(transaction_at as date) as full_date,
    year(transaction_at) as year_number,
    month(transaction_at) as month_number,
    day(transaction_at) as day_number,
    dayname(transaction_at) as day_name
from {{ ref('stg_transactions') }}
