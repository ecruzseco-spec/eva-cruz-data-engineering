"""Esquema DuckDB para capas raw, staging, curated, control y quality."""

from __future__ import annotations

from pathlib import Path

import duckdb


DDL = """
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS curated;
CREATE SCHEMA IF NOT EXISTS control;
CREATE SCHEMA IF NOT EXISTS quality;

CREATE TABLE IF NOT EXISTS raw.transactions (
    batch_id VARCHAR NOT NULL,
    row_number INTEGER NOT NULL,
    transaction_id VARCHAR,
    customer_id VARCHAR,
    amount_text VARCHAR,
    currency VARCHAR,
    status VARCHAR,
    transaction_at_text VARCHAR,
    source_updated_at_text VARCHAR,
    ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    record_hash VARCHAR NOT NULL,
    PRIMARY KEY (batch_id, row_number)
);

CREATE TABLE IF NOT EXISTS staging.validated_transactions (
    batch_id VARCHAR NOT NULL,
    row_number INTEGER NOT NULL,
    transaction_id VARCHAR,
    customer_id VARCHAR,
    amount DECIMAL(18,2),
    currency VARCHAR,
    status VARCHAR,
    transaction_at TIMESTAMP,
    source_updated_at TIMESTAMP,
    record_hash VARCHAR NOT NULL,
    is_accepted BOOLEAN NOT NULL,
    validation_errors VARCHAR,
    PRIMARY KEY (batch_id, row_number)
);

CREATE TABLE IF NOT EXISTS curated.transactions (
    transaction_id VARCHAR PRIMARY KEY,
    customer_id VARCHAR NOT NULL,
    amount DECIMAL(18,2) NOT NULL,
    currency VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    transaction_at TIMESTAMP NOT NULL,
    source_updated_at TIMESTAMP NOT NULL,
    record_hash VARCHAR NOT NULL,
    first_batch_id VARCHAR NOT NULL,
    last_batch_id VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS quality.rejected_transactions (
    batch_id VARCHAR NOT NULL,
    row_number INTEGER NOT NULL,
    transaction_id VARCHAR,
    amount_numeric DECIMAL(18,2),
    reason_codes VARCHAR NOT NULL,
    rejected_at TIMESTAMP NOT NULL DEFAULT current_timestamp,
    PRIMARY KEY (batch_id, row_number)
);

CREATE TABLE IF NOT EXISTS control.batch_runs (
    run_id VARCHAR PRIMARY KEY,
    batch_id VARCHAR NOT NULL,
    attempt INTEGER NOT NULL,
    status VARCHAR NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    source_count INTEGER DEFAULT 0,
    accepted_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    inserted_count INTEGER DEFAULT 0,
    updated_count INTEGER DEFAULT 0,
    unchanged_count INTEGER DEFAULT 0,
    error_message VARCHAR
);

CREATE TABLE IF NOT EXISTS control.batch_registry (
    batch_id VARCHAR PRIMARY KEY,
    file_checksum VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    last_run_id VARCHAR NOT NULL,
    watermark TIMESTAMP,
    source_count INTEGER DEFAULT 0,
    accepted_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS control.reconciliation (
    run_id VARCHAR PRIMARY KEY,
    batch_id VARCHAR NOT NULL,
    source_count INTEGER NOT NULL,
    accepted_count INTEGER NOT NULL,
    rejected_count INTEGER NOT NULL,
    source_amount DECIMAL(18,2) NOT NULL,
    accepted_amount DECIMAL(18,2) NOT NULL,
    rejected_amount DECIMAL(18,2) NOT NULL,
    count_difference INTEGER NOT NULL,
    amount_difference DECIMAL(18,2) NOT NULL,
    is_balanced BOOLEAN NOT NULL,
    reconciled_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);
"""


def connect(database_path: Path) -> duckdb.DuckDBPyConnection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(database_path))
    connection.execute(DDL)
    return connection
