# Proyecto 1 - Pipeline incremental y calidad de datos

> Demostración de portafolio con transacciones 100% sintéticas. No es una implementación productiva.

## Problema y alcance

El proyecto integra lotes CSV, conserva una copia raw, valida estructura y reglas, separa registros rechazados, promueve datos confiables a curated y concilia conteos e importes. Incluye altas, modificaciones, reintentos e idempotencia.

No implementa eliminaciones lógicas o físicas de negocio. La clave natural es `transaction_id`; `source_updated_at` decide si una versión puede reemplazar a la actual.

## Flujo

```mermaid
sequenceDiagram
    participant S as CSV sintético
    participant R as raw
    participant V as staging/quality
    participant C as curated
    participant K as control
    S->>K: registrar lote, checksum e intento
    S->>R: insertar por batch_id + row_number
    R->>V: tipar y aplicar reglas
    V-->>K: aceptados, rechazados y motivos
    V->>C: INSERT o UPDATE por transaction_id
    C-->>K: conciliación y watermark
    Note over R,K: En falla, raw y bitácora permanecen; promoción se revierte
```

## Reglas implementadas

- Esquema exacto de siete columnas.
- Campos obligatorios en todos los atributos.
- `amount` decimal y mayor que cero.
- `currency` en `MXN` o `USD`.
- `status` en `COMPLETED`, `PENDING` o `REFUNDED`.
- Fechas ISO válidas y `transaction_at <= source_updated_at`.
- Duplicados intralote: se acepta la primera aparición y se rechazan las siguientes con `DUPLICATE_IN_BATCH`.
- Versiones: una fecha de actualización mayor modifica; una menor se rechaza con `LATE_STALE_VERSION`; una versión idéntica queda sin cambio.
- El mismo `batch_id` con checksum diferente se bloquea. Un lote completado con el mismo checksum se marca `SKIPPED_ALREADY_COMPLETED`.

## Capas y decisiones

- **raw:** texto original más lote, fila, hora de ingesta y hash. Clave `(batch_id, row_number)`.
- **staging:** tipos convertidos, bandera de aceptación y lista de errores.
- **curated:** última versión válida por `transaction_id`; conserva primer y último lote.
- **quality:** fila rechazada, importe parseable y códigos de razón.
- **control:** intentos, estados, watermark y conciliación.

`source_updated_at` es la marca de versión; el watermark informativo es su máximo por lote. Un evento antiguo que llega tarde se acepta si su versión es más reciente; una versión obsoleta no sobrescribe curated. La promoción se ejecuta en una transacción. La carga raw se confirma antes: así una falla simulada deja evidencia recuperable, mientras staging/curated se revierten.

La conciliación exige `origen = aceptados + rechazados` y compara los importes parseables. Un importe no parseable aporta cero en ambos lados monetarios, pero siempre participa en la conciliación de filas.

## Ejecutar

Desde la raíz, después de instalar `requirements.txt`:

```powershell
$env:PYTHONPATH="$PWD\src"
.\.venv\Scripts\python.exe -m portfolio_pipeline generate
.\.venv\Scripts\python.exe -m portfolio_pipeline demo
.\.venv\Scripts\python.exe -m portfolio_pipeline inspect
```

Para un solo archivo:

```powershell
.\.venv\Scripts\python.exe -m portfolio_pipeline run projects\pipeline\data\generated\batch_001.csv
```

## Pruebas

```powershell
$env:PYTHONPATH="$PWD\src"
.\.venv\Scripts\python.exe -m pytest tests -q
```

Los casos cubren carga normal, errores, falla parcial y recuperación, reproceso idempotente, versión tardía y sintaxis del DAG. Consulta [la evidencia fechada](../../evidence/validation_summary.md).

## Airflow

El DAG está en [`airflow/dags/portfolio_transactions.py`](airflow/dags/portfolio_transactions.py). Define generación, proceso con reintentos y verificación, con una sola ejecución activa. Se comprobó su sintaxis mediante AST, pero **Airflow no se instaló ni se levantó** en esta validación; por tanto no se afirma una ejecución del scheduler.

## Limitaciones

- Ejecución local y monoproceso; DuckDB no sustituye un servicio transaccional multiusuario.
- Sin eliminaciones, CDC real, cifrado, catálogo empresarial ni observabilidad externa.
- El generador usa pocos registros para que cada caso pueda explicarse y auditarse.
- Las monedas no se convierten; los importes solo se suman dentro de su moneda en el modelo analítico.
