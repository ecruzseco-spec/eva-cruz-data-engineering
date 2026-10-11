# Evidencia de validación (local)

> Demostración de portafolio con datos 100% sintéticos. No es una implementación productiva.

- Fecha: `2026-10-10T20:30:49-06:00`
- Entorno: Python 3.12.14, DuckDB 1.5.6, dbt-core 1.12.5, Windows
- Instalación limpia siguiendo el README: **aprobada**
- pytest: **8 aprobadas**
- dbt normal: **39/39 aprobados**
- dbt negativo: **fallo esperado detectado** en las relaciones de cliente y fecha
- dbt restauración final: **39/39 aprobados**
- Ejecución de estos resultados: **local**.
- Esta ejecución local no constituye un nuevo run remoto.
- GitHub Actions, run histórico comprobado: [38006360263](https://github.com/ecruzseco-spec/eva-cruz-data-engineering/actions/runs/38006360263), commit `dba664d4ec30f76df06631c0fc5d36489e125f6a`, conclusión **success**; comprobado el 2026-10-11T02:23:29.3845774Z.
- El run histórico corresponde únicamente a ese commit. Este script no comprueba la conclusión final del workflow en curso ni de ejecuciones futuras.
- Azure: diseño no desplegado. Airflow: DAG no ejecutado.

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
