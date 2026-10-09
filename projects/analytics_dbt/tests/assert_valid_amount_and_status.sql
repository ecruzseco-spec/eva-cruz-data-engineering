select *
from {{ ref('fct_transactions') }}
where amount <= 0
   or status not in ('COMPLETED', 'PENDING', 'REFUNDED')
