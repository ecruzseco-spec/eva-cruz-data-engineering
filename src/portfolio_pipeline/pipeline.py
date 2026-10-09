"""Pipeline incremental con validación, rechazo, conciliación e idempotencia."""

from __future__ import annotations

import csv
import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .database import connect

ALLOWED_CURRENCIES = {"MXN", "USD"}
ALLOWED_STATUSES = {"COMPLETED", "PENDING", "REFUNDED"}


class PipelineError(RuntimeError):
    """Error controlado del pipeline."""


@dataclass(frozen=True)
class BatchResult:
    run_id: str
    batch_id: str
    status: str
    source_count: int
    accepted_count: int
    rejected_count: int
    inserted_count: int
    updated_count: int
    unchanged_count: int
    reconciliation_balanced: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _record_hash(row: dict[str, str]) -> str:
    payload = json.dumps(row, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = {"transaction_id", "customer_id", "amount", "currency", "status", "transaction_at", "source_updated_at"}
        if set(reader.fieldnames or []) != expected:
            raise PipelineError(f"INVALID_SCHEMA: columnas esperadas={sorted(expected)}")
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def _validate(
    row: dict[str, str],
    row_number: int,
    first_row_by_transaction: dict[str, int],
    curated_source_updated_at: datetime | None,
) -> tuple[Decimal | None, datetime | None, datetime | None, list[str]]:
    errors: list[str] = []
    required = ["transaction_id", "customer_id", "amount", "currency", "status", "transaction_at", "source_updated_at"]
    for field in required:
        if not row[field]:
            errors.append(f"REQUIRED_{field.upper()}")

    amount = _parse_decimal(row["amount"])
    transaction_at = _parse_datetime(row["transaction_at"])
    source_updated_at = _parse_datetime(row["source_updated_at"])
    if row["amount"] and amount is None:
        errors.append("INVALID_AMOUNT_TYPE")
    elif amount is not None and amount <= 0:
        errors.append("AMOUNT_NOT_POSITIVE")
    if row["transaction_at"] and transaction_at is None:
        errors.append("INVALID_TRANSACTION_DATE")
    if row["source_updated_at"] and source_updated_at is None:
        errors.append("INVALID_UPDATE_DATE")
    if row["currency"] and row["currency"] not in ALLOWED_CURRENCIES:
        errors.append("INVALID_CURRENCY")
    if row["status"] and row["status"] not in ALLOWED_STATUSES:
        errors.append("INVALID_STATUS")
    if transaction_at and source_updated_at and transaction_at > source_updated_at:
        errors.append("TRANSACTION_AFTER_UPDATE")
    tx_id = row["transaction_id"]
    if tx_id and first_row_by_transaction.get(tx_id, row_number) != row_number:
        errors.append("DUPLICATE_IN_BATCH")
    if source_updated_at and curated_source_updated_at and source_updated_at < curated_source_updated_at:
        errors.append("LATE_STALE_VERSION")
    return amount, transaction_at, source_updated_at, errors


def process_batch(
    database_path: Path,
    csv_path: Path,
    *,
    batch_id: str | None = None,
    simulate_failure_after_validation: bool = False,
) -> BatchResult:
    """Procesa un lote. Raw se confirma antes de promover para habilitar recuperación."""
    batch_id = batch_id or csv_path.stem
    rows = _read_csv(csv_path)
    checksum = _checksum(csv_path)
    run_id = str(uuid.uuid4())
    started_at = datetime.now()
    con = connect(database_path)
    try:
        existing_registry = con.execute(
            "SELECT file_checksum, status FROM control.batch_registry WHERE batch_id = ?", [batch_id]
        ).fetchone()
        attempt = con.execute(
            "SELECT coalesce(max(attempt), 0) + 1 FROM control.batch_runs WHERE batch_id = ?", [batch_id]
        ).fetchone()[0]
        if existing_registry and existing_registry[0] != checksum:
            raise PipelineError("BATCH_ID_CHECKSUM_MISMATCH")
        if existing_registry and existing_registry[1] == "COMPLETED":
            con.execute(
                "INSERT INTO control.batch_runs VALUES (?, ?, ?, 'SKIPPED_ALREADY_COMPLETED', ?, ?, ?, 0, 0, 0, 0, ?, NULL)",
                [run_id, batch_id, attempt, started_at, datetime.now(), len(rows), len(rows)],
            )
            return BatchResult(run_id, batch_id, "SKIPPED_ALREADY_COMPLETED", len(rows), 0, 0, 0, 0, len(rows), True)

        con.execute(
            "INSERT INTO control.batch_runs (run_id, batch_id, attempt, status, started_at, source_count) VALUES (?, ?, ?, 'RUNNING', ?, ?)",
            [run_id, batch_id, attempt, started_at, len(rows)],
        )
        con.execute(
            """INSERT INTO control.batch_registry (batch_id, file_checksum, status, last_run_id)
               VALUES (?, ?, 'RUNNING', ?)
               ON CONFLICT (batch_id) DO UPDATE SET status='RUNNING', last_run_id=excluded.last_run_id, updated_at=now()""",
            [batch_id, checksum, run_id],
        )
        for row_number, row in enumerate(rows, start=1):
            con.execute(
                """INSERT INTO raw.transactions
                   (batch_id, row_number, transaction_id, customer_id, amount_text, currency, status,
                    transaction_at_text, source_updated_at_text, record_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT (batch_id, row_number) DO NOTHING""",
                [batch_id, row_number, row["transaction_id"], row["customer_id"], row["amount"], row["currency"], row["status"], row["transaction_at"], row["source_updated_at"], _record_hash(row)],
            )

        first_row_by_transaction: dict[str, int] = {}
        for row_number, row in enumerate(rows, start=1):
            first_row_by_transaction.setdefault(row["transaction_id"], row_number)

        con.execute("BEGIN TRANSACTION")
        con.execute("DELETE FROM staging.validated_transactions WHERE batch_id = ?", [batch_id])
        con.execute("DELETE FROM quality.rejected_transactions WHERE batch_id = ?", [batch_id])
        accepted_rows: list[tuple[dict[str, str], Decimal, datetime, datetime, str]] = []
        rejected_count = 0
        for row_number, row in enumerate(rows, start=1):
            current = con.execute(
                "SELECT source_updated_at FROM curated.transactions WHERE transaction_id = ?", [row["transaction_id"]]
            ).fetchone()
            current_updated_at = current[0] if current else None
            amount, transaction_at, source_updated_at, errors = _validate(
                row, row_number, first_row_by_transaction, current_updated_at
            )
            record_hash = _record_hash(row)
            con.execute(
                """INSERT INTO staging.validated_transactions VALUES
                   (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [batch_id, row_number, row["transaction_id"], row["customer_id"], amount, row["currency"], row["status"], transaction_at, source_updated_at, record_hash, not errors, "|".join(errors) or None],
            )
            if errors:
                rejected_count += 1
                con.execute(
                    "INSERT INTO quality.rejected_transactions (batch_id, row_number, transaction_id, amount_numeric, reason_codes) VALUES (?, ?, ?, ?, ?)",
                    [batch_id, row_number, row["transaction_id"] or None, amount, "|".join(errors)],
                )
            else:
                assert amount is not None and transaction_at is not None and source_updated_at is not None
                accepted_rows.append((row, amount, transaction_at, source_updated_at, record_hash))

        if simulate_failure_after_validation:
            raise PipelineError("SIMULATED_FAILURE_AFTER_VALIDATION")

        inserted = updated = unchanged = 0
        for row, amount, transaction_at, source_updated_at, record_hash in accepted_rows:
            existing = con.execute(
                "SELECT source_updated_at, record_hash FROM curated.transactions WHERE transaction_id = ?", [row["transaction_id"]]
            ).fetchone()
            if existing is None:
                con.execute(
                    """INSERT INTO curated.transactions
                       (transaction_id, customer_id, amount, currency, status, transaction_at, source_updated_at,
                        record_hash, first_batch_id, last_batch_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    [row["transaction_id"], row["customer_id"], amount, row["currency"], row["status"], transaction_at, source_updated_at, record_hash, batch_id, batch_id],
                )
                inserted += 1
            elif source_updated_at > existing[0]:
                con.execute(
                    """UPDATE curated.transactions SET customer_id=?, amount=?, currency=?, status=?, transaction_at=?,
                       source_updated_at=?, record_hash=?, last_batch_id=?, updated_at=now()
                       WHERE transaction_id=?""",
                    [row["customer_id"], amount, row["currency"], row["status"], transaction_at, source_updated_at, record_hash, batch_id, row["transaction_id"]],
                )
                updated += 1
            else:
                unchanged += 1

        source_amount = sum((_parse_decimal(row["amount"]) or Decimal("0.00")) for row in rows)
        accepted_amount = sum((item[1] for item in accepted_rows), Decimal("0.00"))
        rejected_amount = con.execute(
            "SELECT coalesce(sum(amount_numeric), 0) FROM quality.rejected_transactions WHERE batch_id = ?", [batch_id]
        ).fetchone()[0]
        accepted_count = len(accepted_rows)
        count_difference = len(rows) - accepted_count - rejected_count
        amount_difference = source_amount - accepted_amount - Decimal(str(rejected_amount))
        balanced = count_difference == 0 and abs(amount_difference) < Decimal("0.005")
        con.execute(
            """INSERT INTO control.reconciliation VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, current_timestamp)""",
            [run_id, batch_id, len(rows), accepted_count, rejected_count, source_amount, accepted_amount, rejected_amount, count_difference, amount_difference, balanced],
        )
        watermark = max((item[3] for item in accepted_rows), default=None)
        con.execute(
            """UPDATE control.batch_runs SET status='COMPLETED', ended_at=now(), accepted_count=?,
               rejected_count=?, inserted_count=?, updated_count=?, unchanged_count=? WHERE run_id=?""",
            [accepted_count, rejected_count, inserted, updated, unchanged, run_id],
        )
        con.execute(
            """UPDATE control.batch_registry SET status='COMPLETED', last_run_id=?, watermark=?, source_count=?,
               accepted_count=?, rejected_count=?, updated_at=now() WHERE batch_id=?""",
            [run_id, watermark, len(rows), accepted_count, rejected_count, batch_id],
        )
        con.execute("COMMIT")
        if not balanced:
            raise PipelineError("RECONCILIATION_NOT_BALANCED")
        return BatchResult(run_id, batch_id, "COMPLETED", len(rows), accepted_count, rejected_count, inserted, updated, unchanged, balanced)
    except Exception as exc:
        try:
            con.execute("ROLLBACK")
        except Exception:
            pass
        if not isinstance(exc, PipelineError) or str(exc) != "BATCH_ID_CHECKSUM_MISMATCH":
            con.execute(
                """UPDATE control.batch_runs SET status='FAILED', ended_at=now(), error_message=?
                   WHERE run_id=?""",
                [str(exc), run_id],
            )
            con.execute(
                """UPDATE control.batch_registry SET status='FAILED', last_run_id=?, updated_at=now()
                   WHERE batch_id=?""",
                [run_id, batch_id],
            )
        raise
    finally:
        con.close()
