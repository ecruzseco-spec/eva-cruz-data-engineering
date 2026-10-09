# Diccionario de datos

Todos los campos y valores descritos son sintéticos.

## Pipeline

| Capa.tabla | Grano / clave | Campos principales | Propósito |
|---|---|---|---|
| `raw.transactions` | una fila física por `(batch_id, row_number)` | valores de origen como texto, `record_hash`, `ingested_at` | trazabilidad inmutable del lote |
| `staging.validated_transactions` | una fila por fila raw | tipos convertidos, `is_accepted`, `validation_errors` | decisión de calidad auditable |
| `curated.transactions` | una fila por `transaction_id` | cliente, importe, moneda, estado, fechas, lotes | última versión válida |
| `quality.rejected_transactions` | una fila rechazada por lote/fila | id, importe parseable, `reason_codes` | cuarentena y explicación |
| `control.batch_runs` | una fila por intento (`run_id`) | estado, tiempos, conteos, error | bitácora operativa |
| `control.batch_registry` | una fila por `batch_id` | checksum, estado, watermark | idempotencia y avance |
| `control.reconciliation` | una fila por ejecución exitosa | conteos, importes, diferencias | prueba de conservación |

### Campos de negocio

| Campo | Tipo lógico | Regla |
|---|---|---|
| `transaction_id` | texto | obligatorio; clave natural sintética |
| `customer_id` | texto | obligatorio; identificador sintético |
| `amount` | decimal(18,2) | obligatorio y mayor que cero |
| `currency` | texto | `MXN` o `USD` |
| `status` | texto | `COMPLETED`, `PENDING` o `REFUNDED` |
| `transaction_at` | timestamp | fecha ISO del evento; no posterior a la actualización |
| `source_updated_at` | timestamp | versión de origen usada para upsert y watermark |
| `first_batch_id` | texto | primer lote que insertó la transacción |
| `last_batch_id` | texto | último lote que cambió la transacción |

## Modelo dbt

| Modelo | Grano | Claves / medidas |
|---|---|---|
| `stg_transactions` | transacción | `transaction_id`; tipos normalizados |
| `dim_customer` | cliente | `customer_key` (MD5 del id sintético), `customer_id` |
| `dim_date` | fecha observada | `date_key` AAAAMMDD, `full_date` |
| `fct_transactions` | transacción | FK a cliente y fecha; `amount`, moneda, estado |
| `daily_transaction_metrics` | fecha + moneda + estado | conteo, suma y promedio |
