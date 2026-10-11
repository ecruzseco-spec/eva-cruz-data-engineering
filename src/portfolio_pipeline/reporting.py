"""Reporte HTML autocontenido de resultados reales almacenados en DuckDB."""

from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

from .database import connect


def _table(headers: list[str], rows: list[tuple[object, ...]]) -> str:
    head = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in row) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def write_quality_report(database_path: Path, output_path: Path) -> Path:
    con = connect(database_path)
    try:
        runs = con.execute(
            """SELECT batch_id, attempt, status, source_count, accepted_count, rejected_count,
                      inserted_count, updated_count, unchanged_count
               FROM control.batch_runs ORDER BY started_at"""
        ).fetchall()
        reconciliation = con.execute(
            """SELECT batch_id, source_count, accepted_count, rejected_count, source_amount,
                      accepted_amount, rejected_amount, amount_difference, is_balanced
               FROM control.reconciliation ORDER BY reconciled_at"""
        ).fetchall()
        reasons = con.execute(
            """SELECT reason_codes, count(*) AS records
               FROM quality.rejected_transactions GROUP BY reason_codes ORDER BY records DESC, reason_codes"""
        ).fetchall()
        curated = con.execute(
            "SELECT count(*), coalesce(sum(amount), 0), max(source_updated_at) FROM curated.transactions"
        ).fetchone()
    finally:
        con.close()

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    document = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reporte de calidad - Portafolio</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#172033}}
h1,h2{{color:#12355b}} .notice{{background:#eef6ff;border-left:5px solid #1f6feb;padding:1rem}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin:1.5rem 0}}
.card{{border:1px solid #d8dee8;border-radius:10px;padding:1rem}} .value{{font-size:1.7rem;font-weight:700;color:#0b6e4f}}
table{{border-collapse:collapse;width:100%;margin:1rem 0 2rem}} th,td{{border:1px solid #d8dee8;padding:.55rem;text-align:left}}
th{{background:#12355b;color:#fff}} tbody tr:nth-child(even){{background:#f6f8fa}} code{{background:#f1f3f5;padding:.1rem .3rem}}
</style></head><body>
<h1>Reporte de calidad del pipeline</h1>
<p class="notice"><strong>Demostración de portafolio.</strong> Todos los datos son sintéticos. No representa una implementación productiva.</p>
<p>Generado por una ejecución real de la demostración: <code>{html.escape(generated_at)}</code>.</p>
<div class="cards">
  <div class="card"><div>Registros curated</div><div class="value">{curated[0]}</div></div>
  <div class="card"><div>Importe curated</div><div class="value">{curated[1]}</div></div>
  <div class="card"><div>Marca de avance</div><div>{html.escape(str(curated[2]))}</div></div>
</div>
<h2>Bitácora de lotes</h2>
{_table(['Lote','Intento','Estado','Origen','Aceptados','Rechazados','Altas','Cambios','Sin cambio'], runs)}
<h2>Conciliación</h2>
{_table(['Lote','Origen','Aceptados','Rechazados','Importe origen','Importe aceptado','Importe rechazado','Diferencia','Balanceado'], reconciliation)}
<h2>Motivos de rechazo</h2>
{_table(['Motivo(s)','Registros'], reasons)}
</body></html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    return output_path
