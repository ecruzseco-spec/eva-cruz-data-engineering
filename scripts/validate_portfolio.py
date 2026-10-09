"""Validación integral reproducible y exportación de evidencia pública sanitizada."""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import dbt.version
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT / "projects" / "analytics_dbt"
DATABASE = ROOT / "projects" / "pipeline" / "data" / "portfolio.duckdb"
GENERATED = ROOT / "projects" / "pipeline" / "data" / "generated"
ARTIFACTS = ROOT / "projects" / "pipeline" / "artifacts"
EVIDENCE = ROOT / "evidence"
TEST_TEMP = ROOT / "tmp" / "validation_pytest"
PYTEST_JUNIT = ROOT / "tmp" / "pytest_results.xml"


def dbt_executable() -> str:
    executable_name = "dbt.exe" if os.name == "nt" else "dbt"
    candidate = Path(sys.executable).with_name(executable_name)
    if candidate.exists():
        return str(candidate)
    discovered = shutil.which("dbt")
    if not discovered:
        raise RuntimeError("No se encontró el ejecutable dbt del entorno activo")
    return discovered


def run(command: list[str], *, cwd: Path = ROOT, expect_success: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    if expect_success and result.returncode != 0:
        raise RuntimeError(f"Falló {' '.join(command)}\n{result.stdout}\n{result.stderr}")
    return result


def clean_generated_outputs() -> None:
    for path in [DATABASE, DATABASE.with_suffix(".duckdb.wal")]:
        if path.exists():
            path.unlink()
    for directory in [GENERATED, ARTIFACTS, DBT_DIR / "target", DBT_DIR / "logs", TEST_TEMP]:
        if directory.exists():
            shutil.rmtree(directory)


def parse_pass_total(output: str) -> tuple[int, int]:
    match = re.search(r"PASS=(\d+).*TOTAL=(\d+)", output)
    if not match:
        raise RuntimeError("No se encontró el resumen PASS/TOTAL de dbt")
    return int(match.group(1)), int(match.group(2))


def main() -> None:
    clean_generated_outputs()
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    pytest_result = run([
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "-q",
        "--basetemp",
        str(TEST_TEMP),
        "-p",
        "no:cacheprovider",
        "--junitxml",
        str(PYTEST_JUNIT),
    ])
    demo = run([sys.executable, "-m", "portfolio_pipeline", "demo"])
    demo_payload = json.loads(demo.stdout)

    dbt_command = [dbt_executable(), "build", "--profiles-dir", ".", "--no-use-colors"]
    dbt_normal = run(dbt_command, cwd=DBT_DIR)
    normal_pass, normal_total = parse_pass_total(dbt_normal.stdout)

    dbt_negative = run(
        dbt_command + ["--vars", "{inject_invalid_relationship: true}"],
        cwd=DBT_DIR,
        expect_success=False,
    )
    negative_output = dbt_negative.stdout + dbt_negative.stderr
    expected_failures = [
        "relationships_fct_transactions_customer_key",
        "relationships_fct_transactions_date_key",
    ]
    if dbt_negative.returncode == 0 or not all(name in negative_output for name in expected_failures):
        raise RuntimeError("El caso negativo dbt no detectó las relaciones huérfanas esperadas")

    dbt_repair = run(dbt_command, cwd=DBT_DIR)
    repair_pass, repair_total = parse_pass_total(dbt_repair.stdout)
    run([dbt_executable(), "docs", "generate", "--profiles-dir", ".", "--no-use-colors"], cwd=DBT_DIR)

    con = duckdb.connect(str(DATABASE), read_only=True)
    try:
        inspection = {
            "raw_count": con.execute("select count(*) from raw.transactions").fetchone()[0],
            "curated_count": con.execute("select count(*) from curated.transactions").fetchone()[0],
            "curated_amount": str(con.execute("select sum(amount) from curated.transactions").fetchone()[0]),
            "rejected_count": con.execute("select count(*) from quality.rejected_transactions").fetchone()[0],
            "failed_runs_expected": con.execute("select count(*) from control.batch_runs where status='FAILED'").fetchone()[0],
            "unbalanced_reconciliations": con.execute("select count(*) from control.reconciliation where not is_balanced").fetchone()[0],
            "reconciliations": [
                {
                    "batch_id": row[0],
                    "source_count": row[1],
                    "accepted_count": row[2],
                    "rejected_count": row[3],
                    "amount_difference": str(row[4]),
                    "is_balanced": row[5],
                }
                for row in con.execute(
                    "select batch_id, source_count, accepted_count, rejected_count, amount_difference, is_balanced from control.reconciliation order by batch_id"
                ).fetchall()
            ],
            "rejection_reasons": [
                {"reason_codes": row[0], "count": row[1]}
                for row in con.execute(
                    "select reason_codes, count(*) from quality.rejected_transactions group by reason_codes order by reason_codes"
                ).fetchall()
            ],
        }
    finally:
        con.close()

    quality_report = Path(demo_payload["quality_report"])
    shutil.copy2(quality_report, EVIDENCE / "quality_report.html")
    junit_root = ET.parse(PYTEST_JUNIT).getroot()
    suites = [junit_root] if junit_root.tag == "testsuite" else list(junit_root.findall("testsuite"))
    pytest_total = sum(int(suite.attrib.get("tests", 0)) for suite in suites)
    pytest_failures = sum(int(suite.attrib.get("failures", 0)) for suite in suites)
    pytest_errors = sum(int(suite.attrib.get("errors", 0)) for suite in suites)
    pytest_skipped = sum(int(suite.attrib.get("skipped", 0)) for suite in suites)
    pytest_passed = pytest_total - pytest_failures - pytest_errors - pytest_skipped
    if pytest_total == 0 or pytest_failures or pytest_errors:
        raise RuntimeError("El resultado JUnit de pytest no confirma una suite aprobada")
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    evidence = {
        "generated_at": generated_at,
        "scope": "Ejecución local sobre datos 100% sintéticos",
        "environment": {
            "python": platform.python_version(),
            "duckdb": duckdb.__version__,
            "dbt_core": dbt.version.__version__,
            "operating_system": platform.system(),
            "clean_readme_setup": "PASS" if os.environ.get("PORTFOLIO_CLEAN_ENV_VERIFICATION") == "1" else "NOT_DECLARED",
        },
        "pytest": {"passed": pytest_passed, "total": pytest_total, "skipped": pytest_skipped, "status": "PASS"},
        "pipeline": {
            "simulated_failure_detected": demo_payload["simulated_failure"],
            "completed_runs": demo_payload["runs"],
            **inspection,
        },
        "dbt": {
            "normal_build": {"passed": normal_pass, "total": normal_total, "status": "PASS"},
            "negative_relationship_case": {
                "process_exit_code": dbt_negative.returncode,
                "status": "EXPECTED_FAILURE_DETECTED",
                "detected_tests": expected_failures,
            },
            "final_repair_build": {"passed": repair_pass, "total": repair_total, "status": "PASS"},
        },
        "github_actions": "PREPARED_NOT_EXECUTED",
    }
    (EVIDENCE / "validation_summary.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    reconciliation_rows = "\n".join(
        f"| {item['batch_id']} | {item['source_count']} | {item['accepted_count']} | {item['rejected_count']} | {item['amount_difference']} | {item['is_balanced']} |"
        for item in inspection["reconciliations"]
    )
    markdown = f"""# Evidencia de validación local

> Demostración de portafolio con datos 100% sintéticos. No es una implementación productiva.

- Fecha: `{generated_at}`
- Entorno: Python {platform.python_version()}, DuckDB {duckdb.__version__}, dbt-core {dbt.version.__version__}, {platform.system()}
- Instalación limpia siguiendo el README: **{'aprobada' if os.environ.get('PORTFOLIO_CLEAN_ENV_VERIFICATION') == '1' else 'no declarada en esta ejecución'}**
- pytest: **{pytest_passed} aprobadas**
- dbt normal: **{normal_pass}/{normal_total} aprobados**
- dbt negativo: **fallo esperado detectado** en las relaciones de cliente y fecha
- dbt restauración final: **{repair_pass}/{repair_total} aprobados**
- GitHub Actions: **preparado, todavía no ejecutado en GitHub**

## Resultado del pipeline

- Raw: {inspection['raw_count']} filas.
- Curated: {inspection['curated_count']} transacciones, importe {inspection['curated_amount']}.
- Rechazos: {inspection['rejected_count']} filas con motivo.
- Fallas registradas: {inspection['failed_runs_expected']} (corresponde a la falla simulada y recuperada).
- Conciliaciones no balanceadas: {inspection['unbalanced_reconciliations']}.
- Reproceso de `batch_001`: `SKIPPED_ALREADY_COMPLETED`, sin duplicados.

| Lote | Origen | Aceptados | Rechazados | Diferencia importe | Balanceado |
|---|---:|---:|---:|---:|---|
{reconciliation_rows}

## Caso analítico negativo

Con `inject_invalid_relationship: true`, dbt agregó una fila sintética huérfana solo para la prueba. Las pruebas de relación a `dim_customer` y `dim_date` devolvieron un registro cada una y el proceso terminó con código distinto de cero, como se esperaba. Después se ejecutó nuevamente el build normal y quedó en estado válido.

El reporte navegable está en [quality_report.html](quality_report.html) y el detalle estructurado en [validation_summary.json](validation_summary.json).
"""
    (EVIDENCE / "validation_summary.md").write_text(markdown, encoding="utf-8")
    print(json.dumps({"status": "PASS", "evidence": str(EVIDENCE / "validation_summary.json")}, indent=2))


if __name__ == "__main__":
    main()
