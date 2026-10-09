from __future__ import annotations

import ast
import csv
from pathlib import Path

import duckdb
import pytest

from portfolio_pipeline.generator import FIELDS, generate_batches
from portfolio_pipeline.pipeline import PipelineError, process_batch


@pytest.fixture()
def demo(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    database = tmp_path / "portfolio.duckdb"
    paths = {path.stem: path for path in generate_batches(tmp_path / "generated")}
    return database, paths


def test_normal_batch_is_balanced(demo: tuple[Path, dict[str, Path]]) -> None:
    database, paths = demo
    result = process_batch(database, paths["batch_001"])
    assert result.status == "COMPLETED"
    assert (result.source_count, result.accepted_count, result.rejected_count) == (5, 5, 0)
    assert result.reconciliation_balanced is True


def test_invalid_rows_are_rejected_with_traceability(demo: tuple[Path, dict[str, Path]]) -> None:
    database, paths = demo
    process_batch(database, paths["batch_001"])
    result = process_batch(database, paths["batch_002"])
    assert (result.source_count, result.accepted_count, result.rejected_count) == (8, 3, 5)
    con = duckdb.connect(str(database), read_only=True)
    try:
        reasons = "|".join(row[0] for row in con.execute("SELECT reason_codes FROM quality.rejected_transactions").fetchall())
    finally:
        con.close()
    assert "DUPLICATE_IN_BATCH" in reasons
    assert "REQUIRED_CUSTOMER_ID" in reasons
    assert "AMOUNT_NOT_POSITIVE" in reasons
    assert "INVALID_STATUS" in reasons
    assert "INVALID_TRANSACTION_DATE" in reasons


def test_recovery_after_partial_failure_does_not_duplicate(demo: tuple[Path, dict[str, Path]]) -> None:
    database, paths = demo
    process_batch(database, paths["batch_001"])
    with pytest.raises(PipelineError, match="SIMULATED_FAILURE"):
        process_batch(database, paths["batch_003_recovery"], simulate_failure_after_validation=True)
    recovered = process_batch(database, paths["batch_003_recovery"])
    assert recovered.status == "COMPLETED"
    con = duckdb.connect(str(database), read_only=True)
    try:
        assert con.execute("SELECT count(*) FROM raw.transactions WHERE batch_id='batch_003_recovery'").fetchone()[0] == 2
        assert con.execute("SELECT count(*) FROM curated.transactions WHERE transaction_id='T1012'").fetchone()[0] == 1
    finally:
        con.close()


def test_completed_batch_reprocessing_is_idempotent(demo: tuple[Path, dict[str, Path]]) -> None:
    database, paths = demo
    process_batch(database, paths["batch_001"])
    second = process_batch(database, paths["batch_001"])
    assert second.status == "SKIPPED_ALREADY_COMPLETED"
    con = duckdb.connect(str(database), read_only=True)
    try:
        assert con.execute("SELECT count(*), sum(amount) FROM curated.transactions").fetchone() == (5, pytest.approx(1001.25))
    finally:
        con.close()


def test_stale_late_record_is_rejected(demo: tuple[Path, dict[str, Path]], tmp_path: Path) -> None:
    database, paths = demo
    process_batch(database, paths["batch_001"])
    late = tmp_path / "late.csv"
    with late.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow({"transaction_id": "T1002", "customer_id": "C002", "amount": "10.00", "currency": "MXN", "status": "COMPLETED", "transaction_at": "2026-08-01T10:00:00", "source_updated_at": "2026-08-01T10:01:00"})
    result = process_batch(database, late, batch_id="batch_late")
    assert result.rejected_count == 1
    assert result.reconciliation_balanced is True


def test_airflow_dag_is_syntactically_valid() -> None:
    dag_path = Path("projects/pipeline/airflow/dags/portfolio_transactions.py")
    ast.parse(dag_path.read_text(encoding="utf-8"))
