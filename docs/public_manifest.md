# Manifiesto público exacto

Este es el contenido propuesto para una futura publicación. No se ha publicado todavía.

## Archivos (46)

```text
.github/workflows/ci.yml
.gitignore
ASSISTANCE.md
README.md
docs/_config.yml
docs/architecture_azure.md
docs/assets/architecture_azure.mmd
docs/assets/architecture_azure.svg
docs/data_dictionary.md
docs/github_profile.md
docs/index.md
docs/interview_guide.md
docs/public_manifest.md
docs/publication_checklist.md
evidence/github_actions_run.json
evidence/quality_report.html
evidence/validation_summary.json
evidence/validation_summary.md
projects/analytics_dbt/README.md
projects/analytics_dbt/analyses/business_metrics.sql
projects/analytics_dbt/dbt_project.yml
projects/analytics_dbt/models/marts/dim_customer.sql
projects/analytics_dbt/models/marts/dim_date.sql
projects/analytics_dbt/models/marts/fct_transactions.sql
projects/analytics_dbt/models/marts/schema.yml
projects/analytics_dbt/models/metrics/daily_transaction_metrics.sql
projects/analytics_dbt/models/metrics/schema.yml
projects/analytics_dbt/models/staging/schema.yml
projects/analytics_dbt/models/staging/sources.yml
projects/analytics_dbt/models/staging/stg_transactions.sql
projects/analytics_dbt/profiles.yml
projects/analytics_dbt/tests/assert_valid_amount_and_status.sql
projects/pipeline/README.md
projects/pipeline/airflow/dags/portfolio_transactions.py
pyproject.toml
requirements.txt
scripts/validate_portfolio.py
src/portfolio_pipeline/__init__.py
src/portfolio_pipeline/__main__.py
src/portfolio_pipeline/cli.py
src/portfolio_pipeline/database.py
src/portfolio_pipeline/generator.py
src/portfolio_pipeline/pipeline.py
src/portfolio_pipeline/reporting.py
tests/test_pipeline.py
tests/test_validation_context.py
```

## Datos públicos

- Nombre profesional: `Eva Cruz Valdovinos`.
- Bio tecnológica general confirmada por el CV, sin datos de contacto.
- Tres lotes definidos en `generator.py`, todos inventados:
  - `batch_001`: T1001-T1005.
  - `batch_002`: actualización T1002; T1006; T1007 repetida; T1008-T1011 con errores intencionales.
  - `batch_003_recovery`: actualización T1003 y alta T1012.
- Clientes ficticios C001-C010, fechas de septiembre de 2026, monedas MXN/USD y valores diseñados para las pruebas.
- Evidencia: 15 filas raw, 8 transacciones curated por 1312.90, 5 rechazos, una falla simulada recuperada, 8/8 pytest y 39/39 nodos dbt en el estado final.
- Identificadores UUID de las ejecuciones locales; no identifican a personas ni sistemas externos.

## Información que no está incluida

No aparecen CV, fotografía, teléfono, correo personal o laboral, domicilio, secretos, datos reales, nombres de tablas internas, capturas ni código de empleadores. Las bases DuckDB, CSV generados, entornos virtuales, logs y artefactos de compilación están excluidos por `.gitignore`.
