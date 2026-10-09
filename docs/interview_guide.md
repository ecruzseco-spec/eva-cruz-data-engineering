# Guía de preparación para entrevista

No memorices el texto. Ejecuta los proyectos, cambia un caso y explica con tus palabras qué observaste. La construcción inicial recibió asistencia de IA; antes de atribuirte el trabajo debes revisar cada archivo y poder defenderlo.

## Proyecto 1 - Pipeline incremental y calidad

### Explicación de un minuto

> Construí una demostración local de un pipeline de transacciones sintéticas con Python, SQL y DuckDB. Separé el flujo en raw, staging y curated, y añadí tablas de control y cuarentena. Cada lote tiene checksum, estado, conteos y watermark. Las reglas validan campos, tipos, fechas, duplicados y valores permitidos. Los registros inválidos conservan su trazabilidad y motivo. La carga es incremental por transaction_id y source_updated_at. Probé una falla después de validar: la promoción se revirtió, raw permaneció y el reintento terminó sin duplicados. También reprocesé un lote ya completado y el pipeline lo omitió. Finalmente concilié filas e importes entre origen, aceptados y rechazados.

### Explicación técnica de cinco minutos

1. El generador produce tres CSV deterministas: normal, errores/actualización y recuperación.
2. Antes de procesar valido el contrato de columnas y calculo SHA-256 del archivo. `batch_id + checksum` protege contra reutilizar un id con contenido distinto.
3. Raw usa `(batch_id, row_number)`; así un reintento no duplica la ingesta física. El hash de fila apoya auditoría.
4. Staging convierte decimal y timestamps, acumula códigos de error y decide aceptación. La primera aparición de una clave en el lote puede pasar; duplicados posteriores se rechazan.
5. Curated tiene una fila por `transaction_id`. Una versión con `source_updated_at` mayor actualiza; una menor se manda a rechazo para impedir regresiones. No implementé deletes y lo declaro.
6. Raw y el inicio de bitácora se confirman antes de promover. Staging, quality, curated y conciliación están en una transacción. La falla simulada ocurre después de validar; el rollback evita una publicación parcial y el reintento reutiliza raw.
7. La conciliación verifica conteos y la suma de importes parseables. El pipeline falla si queda diferencia.
8. Un reporte HTML y las tablas de control muestran lotes, motivos y balances. pytest automatiza los escenarios.
9. El DAG de Airflow está preparado con generación, procesamiento con reintentos y verificación; solo se validó sintaxis porque Airflow no está instalado.
10. En Azure trasladaría raw/curated a Delta, el procesamiento a PySpark/Databricks y la orquestación a ADF, conservando las claves de idempotencia.

### Preguntas probables

**1. ¿Por qué `transaction_id` y no el hash como clave?**
`transaction_id` representa la identidad del evento y permite modificaciones. El hash identifica una versión exacta; usarlo como clave crearía otra fila por cada cambio.

**2. ¿Cómo garantizas idempotencia?**
Con checksum por lote, clave raw `(batch_id,row_number)`, estado del registro de lotes y upsert condicionado por `source_updated_at`. Un lote completado e idéntico se omite.

**3. ¿Qué sucede con un registro tardío?**
Distingo fecha de evento de versión. Un evento viejo con actualización nueva puede entrar. Una versión anterior a la vigente se rechaza como `LATE_STALE_VERSION`. En producción evaluaría una ventana de lateness y CDC.

**4. ¿Por qué conservar los rechazos?**
Para no perder evidencia: negocio y soporte pueden reconciliar el origen, entender la regla y corregir/reprocesar. El rechazo conserva lote y fila.

**5. ¿Qué cambiarías para producción?**
Contratos versionados, almacenamiento Delta, gestión de secretos, observabilidad, alertas, pruebas de carga, concurrencia, SLA, catálogo/linaje y una política acordada de deletes y PII.

### Errores y limitaciones que debes contar

- Durante el desarrollo, DuckDB 1.5 no aceptó `current_timestamp` dentro de un `ON CONFLICT` como estaba escrito; las pruebas lo detectaron y se cambió a `now()`.
- El sandbox bloqueó temporales y multiprocessing; se distinguió ese fallo ambiental de un fallo de código y se repitió fuera del sandbox.
- El volumen es pequeño y no demuestra escalabilidad. Airflow y Azure no se ejecutaron.
- La conciliación monetaria excluye de ambos lados los importes que no pueden tiparse, pero esos registros sí concilian en conteo.

### Práctica personal

- Ejecuta el demo y consulta las cinco tablas principales con SQL.
- Agrega un cuarto lote con una actualización y una versión tardía.
- Provoca un checksum distinto con el mismo `batch_id` y explica el bloqueo.
- Explica dónde ocurre el commit de raw, dónde comienza la transacción y por qué.
- Lee el DAG y describe cómo parametrizarías una fecha de negocio.

## Proyecto 2 - Modelado analítico con dbt

### Explicación de un minuto

> Sobre la capa curated construí un proyecto dbt-duckdb con staging, dimensión cliente, dimensión fecha, tabla de hechos y métricas diarias. Documenté la granularidad y las métricas, y añadí pruebas de unicidad, no nulos, valores permitidos, relaciones e importes/estados válidos. El build normal pasó 39 nodos. Para probar que el control realmente funciona, activé una variable que introduce una fila sintética con claves huérfanas: dbt falló en las dos relaciones esperadas. Después ejecuté el build normal para restaurar el estado. También documenté cómo migraría el patrón a Databricks, Synapse y ADF, sin afirmar que fue desplegado.

### Explicación técnica de cinco minutos

1. La source apunta a `curated.transactions`; las pruebas de source verifican el contrato antes de modelar.
2. `stg_transactions` conserva el grano de transacción y normaliza tipos, moneda y estado.
3. `dim_customer` genera una clave sustituta estable con MD5 del identificador sintético y agrega fechas de actividad. Es una dimensión tipo 1 simplificada.
4. `dim_date` contiene las fechas observadas y una clave AAAAMMDD. En producción probablemente usaría un calendario completo.
5. `fct_transactions` conserva una fila por transacción y referencia ambas dimensiones.
6. La vista de métricas agrega por fecha, moneda y estado. No mezcla monedas mediante una suma global.
7. `schema.yml` define pruebas genéricas; una prueba singular impide importes no positivos o estados desconocidos.
8. `ref()` y `source()` hacen explícito el linaje y permiten `dbt docs generate`.
9. La variable negativa agrega una fila huérfana únicamente cuando se solicita. El código de salida no cero y las dos pruebas `relationships` prueban la capacidad de detección.
10. En Azure elegiría el adapter y materialización según el destino: Databricks/Delta para transformación distribuida y Synapse para serving cuando el patrón de consumo lo justifique. ADF coordinaría las dependencias.

### Preguntas probables

**1. ¿Cuál es el grano de la tabla de hechos?**
Una fila por `transaction_id` en su última versión válida. Lo declaro antes de elegir dimensiones o métricas para evitar duplicidad accidental.

**2. ¿Por qué una clave MD5 para cliente?**
Es determinista y suficiente para la demostración sin secuencias compartidas. En un warehouse productivo evaluaría claves enteras, colisiones, SCD y el sistema maestro.

**3. ¿Cómo sabes que las pruebas de relación sirven?**
El modo negativo introduce claves inexistentes y dbt devuelve exactamente un registro en cada relación. Luego restauro y el build vuelve a pasar.

**4. ¿Qué significa `gross_amount` con dos monedas?**
Solo es válido dentro del grano que incluye `currency`. No presento una suma entre MXN y USD sin tipo de cambio y fecha de conversión.

**5. ¿Por qué DuckDB?**
Permite un ejercicio OLAP reproducible, rápido y sin infraestructura. No lo presento como sustituto universal de Databricks o Synapse; el valor está en el modelado y las pruebas portables.

### Errores y limitaciones que debes contar

- dbt compiló y conectó en el sandbox, pero Windows no pudo crear pipes de multiprocessing; la misma ejecución fuera del sandbox pasó.
- El caso negativo falla por diseño; no debe confundirse con el build final, que se ejecuta después y queda verde.
- No se probaron incremental models de dbt, snapshots, SCD2 ni rendimiento distribuido.
- La propuesta Azure no incluye benchmark ni estimación de costo porque no se desplegaron recursos.

### Práctica personal

- Ejecuta `dbt build`, abre `dbt docs` y recorre el linaje.
- Escribe una consulta sobre `daily_transaction_metrics` y valida el resultado manualmente.
- Activa el caso negativo, identifica las claves huérfanas y restaura.
- Cambia una prueba `accepted_values` y observa el SQL compilado.
- Explica cuándo elegirías Databricks frente a Synapse serverless o dedicated.

## Divulgación de asistencia

Una forma honesta de decirlo:

> Preparé este portafolio con asistencia de IA para acelerar el scaffolding, la documentación y la revisión. Los casos son sintéticos. Antes de presentarlo revisé el código, ejecuté las pruebas, reproduje los fallos y practiqué explicar las decisiones. No lo presento como un sistema productivo ni como trabajo histórico para un empleador.
