"""Generación determinista de lotes de transacciones completamente sintéticas."""

from __future__ import annotations

import csv
from pathlib import Path

FIELDS = [
    "transaction_id",
    "customer_id",
    "amount",
    "currency",
    "status",
    "transaction_at",
    "source_updated_at",
]


BATCHES: dict[str, list[dict[str, str]]] = {
    "batch_001": [
        {"transaction_id": "T1001", "customer_id": "C001", "amount": "120.50", "currency": "MXN", "status": "COMPLETED", "transaction_at": "2026-09-01T10:00:00", "source_updated_at": "2026-09-01T10:05:00"},
        {"transaction_id": "T1002", "customer_id": "C002", "amount": "250.00", "currency": "MXN", "status": "COMPLETED", "transaction_at": "2026-09-01T11:00:00", "source_updated_at": "2026-09-01T11:05:00"},
        {"transaction_id": "T1003", "customer_id": "C001", "amount": "75.25", "currency": "MXN", "status": "PENDING", "transaction_at": "2026-09-02T09:00:00", "source_updated_at": "2026-09-02T09:03:00"},
        {"transaction_id": "T1004", "customer_id": "C003", "amount": "520.00", "currency": "MXN", "status": "COMPLETED", "transaction_at": "2026-09-02T12:30:00", "source_updated_at": "2026-09-02T12:31:00"},
        {"transaction_id": "T1005", "customer_id": "C004", "amount": "35.50", "currency": "USD", "status": "REFUNDED", "transaction_at": "2026-09-03T14:00:00", "source_updated_at": "2026-09-03T15:00:00"},
    ],
    "batch_002": [
        {"transaction_id": "T1002", "customer_id": "C002", "amount": "275.00", "currency": "MXN", "status": "COMPLETED", "transaction_at": "2026-09-01T11:00:00", "source_updated_at": "2026-09-05T08:00:00"},
        {"transaction_id": "T1006", "customer_id": "C005", "amount": "89.90", "currency": "MXN", "status": "COMPLETED", "transaction_at": "2026-09-05T10:00:00", "source_updated_at": "2026-09-05T10:01:00"},
        {"transaction_id": "T1007", "customer_id": "C006", "amount": "42.00", "currency": "MXN", "status": "PENDING", "transaction_at": "2026-09-05T10:30:00", "source_updated_at": "2026-09-05T10:31:00"},
        {"transaction_id": "T1007", "customer_id": "C006", "amount": "42.00", "currency": "MXN", "status": "PENDING", "transaction_at": "2026-09-05T10:30:00", "source_updated_at": "2026-09-05T10:31:00"},
        {"transaction_id": "T1008", "customer_id": "", "amount": "55.00", "currency": "MXN", "status": "COMPLETED", "transaction_at": "2026-09-05T11:00:00", "source_updated_at": "2026-09-05T11:01:00"},
        {"transaction_id": "T1009", "customer_id": "C007", "amount": "-10.00", "currency": "MXN", "status": "COMPLETED", "transaction_at": "2026-09-05T12:00:00", "source_updated_at": "2026-09-05T12:01:00"},
        {"transaction_id": "T1010", "customer_id": "C008", "amount": "33.00", "currency": "BTC", "status": "UNKNOWN", "transaction_at": "2026-09-05T13:00:00", "source_updated_at": "2026-09-05T13:01:00"},
        {"transaction_id": "T1011", "customer_id": "C009", "amount": "70.00", "currency": "MXN", "status": "COMPLETED", "transaction_at": "fecha-invalida", "source_updated_at": "2026-09-05T14:01:00"},
    ],
    "batch_003_recovery": [
        {"transaction_id": "T1003", "customer_id": "C001", "amount": "80.00", "currency": "MXN", "status": "COMPLETED", "transaction_at": "2026-09-02T09:00:00", "source_updated_at": "2026-09-06T08:00:00"},
        {"transaction_id": "T1012", "customer_id": "C010", "amount": "150.00", "currency": "MXN", "status": "COMPLETED", "transaction_at": "2026-09-06T09:00:00", "source_updated_at": "2026-09-06T09:01:00"},
    ],
}


def generate_batches(output_dir: Path) -> list[Path]:
    """Escribe los mismos lotes en cada ejecución y devuelve sus rutas."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for batch_id, rows in BATCHES.items():
        path = output_dir / f"{batch_id}.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        paths.append(path)
    return paths
