"""DAG preparado para Airflow 2.x; no se ejecuta en la validación local del portafolio."""

from __future__ import annotations

import subprocess
from datetime import datetime

from airflow.decorators import dag, task


@dag(
    dag_id="portfolio_synthetic_transactions",
    description="Genera, valida, concilia y publica transacciones sintéticas",
    schedule="0 6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["portfolio", "synthetic", "duckdb"],
)
def portfolio_synthetic_transactions():
    @task
    def generate() -> None:
        subprocess.run(["python", "-m", "portfolio_pipeline", "generate"], check=True)

    @task(retries=2)
    def process() -> None:
        subprocess.run(["python", "-m", "portfolio_pipeline", "demo"], check=True)

    @task
    def verify() -> None:
        subprocess.run(["python", "-m", "portfolio_pipeline", "inspect"], check=True)

    generate() >> process() >> verify()


portfolio_synthetic_transactions()
