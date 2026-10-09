# Evidencia de validación local

> Demostración de portafolio con datos 100% sintéticos. No es una implementación productiva.

- Fecha: `2026-10-08T12:06:10-06:00`
- Entorno: Python 3.12.10, DuckDB 1.5.6, dbt-core 1.12.5, Windows
- Instalación limpia siguiendo el README: **aprobada**
- pytest: **6 aprobadas**
- dbt normal: **39/39 aprobados**
- dbt negativo: **fallo esperado detectado** en las relaciones de cliente y fecha
- dbt restauración final: **39/39 aprobados**
- GitHub Actions: **validación aprobada el 9 de octubre de 2026**; consulta el historial en la pestaña Actions.

## Resultado del pipeline

- Raw: 15 filas.
- Curated: 8 transacciones, importe 1312.90.
- Rechazos: 5 filas con motivo.
- Fallas registradas: 1 (corresponde a la falla simulada y recuperada).
- Conciliaciones no balanceadas: 0.
- Reproceso de `batch_001`: `SKIPPED_ALREADY_COMPLETED`, sin duplicados.

| Lote | Origen | Aceptados | Rechazados | Diferencia importe | Balanceado |
|---|---:|---:|---:|---:|---|
| batch_001 | 5 | 5 | 0 | 0.00 | True |
| batch_002 | 8 | 3 | 5 | 0.00 | True |
| batch_003_recovery | 2 | 2 | 0 | 0.00 | True |

## Caso analítico negativo

Con `inject_invalid_relationship: true`, dbt agregó una fila sintética huérfana solo para la prueba. Las pruebas de relación a `dim_customer` y `dim_date` devolvieron un registro cada una y el proceso terminó con código distinto de cero, como se esperaba. Después se ejecutó nuevamente el build normal y quedó en estado válido.

El reporte navegable está en [quality_report.html](quality_report.html) y el detalle estructurado en [validation_summary.json](validation_summary.json).
