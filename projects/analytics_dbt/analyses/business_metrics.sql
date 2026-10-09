-- Definiciones de negocio demostrativas; todos los datos son sintéticos.
select
    currency,
    count(*) filter (where status = 'COMPLETED') as completed_transactions,
    sum(amount) filter (where status = 'COMPLETED') as completed_amount,
    count(*) filter (where status = 'REFUNDED') as refunded_transactions,
    sum(amount) filter (where status = 'REFUNDED') as refunded_amount
from {{ ref('fct_transactions') }}
group by currency
order by currency
