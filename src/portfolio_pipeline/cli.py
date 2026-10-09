"""CLI reproducible para generar, procesar e inspeccionar la demostración."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .database import connect
from .generator import generate_batches
from .pipeline import PipelineError, process_batch
from .reporting import write_quality_report


def _default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_demo(database: Path, generated_dir: Path, report: Path) -> dict[str, object]:
    paths = {path.stem: path for path in generate_batches(generated_dir)}
    results: list[dict[str, object]] = []
    results.append(process_batch(database, paths["batch_001"]).to_dict())
    results.append(process_batch(database, paths["batch_002"]).to_dict())
    simulated_failure = "not_run"
    try:
        process_batch(database, paths["batch_003_recovery"], simulate_failure_after_validation=True)
    except PipelineError as exc:
        simulated_failure = str(exc)
    results.append(process_batch(database, paths["batch_003_recovery"]).to_dict())
    results.append(process_batch(database, paths["batch_001"]).to_dict())
    write_quality_report(database, report)
    return {
        "database": str(database),
        "quality_report": str(report),
        "simulated_failure": simulated_failure,
        "runs": results,
    }


def inspect_database(database: Path) -> dict[str, object]:
    con = connect(database)
    try:
        return {
            "curated_count": con.execute("SELECT count(*) FROM curated.transactions").fetchone()[0],
            "curated_amount": str(con.execute("SELECT coalesce(sum(amount), 0) FROM curated.transactions").fetchone()[0]),
            "raw_count": con.execute("SELECT count(*) FROM raw.transactions").fetchone()[0],
            "rejected_count": con.execute("SELECT count(*) FROM quality.rejected_transactions").fetchone()[0],
            "failed_runs": con.execute("SELECT count(*) FROM control.batch_runs WHERE status='FAILED'").fetchone()[0],
            "unbalanced_reconciliations": con.execute("SELECT count(*) FROM control.reconciliation WHERE NOT is_balanced").fetchone()[0],
        }
    finally:
        con.close()


def build_parser() -> argparse.ArgumentParser:
    root = _default_root()
    parser = argparse.ArgumentParser(description="Pipeline sintético del portafolio")
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate", help="Genera lotes sintéticos")
    generate.add_argument("--output-dir", type=Path, default=root / "projects/pipeline/data/generated")
    run = sub.add_parser("run", help="Procesa un CSV")
    run.add_argument("csv", type=Path)
    run.add_argument("--database", type=Path, default=root / "projects/pipeline/data/portfolio.duckdb")
    run.add_argument("--batch-id")
    run.add_argument("--simulate-failure", action="store_true")
    demo = sub.add_parser("demo", help="Ejecuta casos normal, errores, recuperación e idempotencia")
    demo.add_argument("--database", type=Path, default=root / "projects/pipeline/data/portfolio.duckdb")
    demo.add_argument("--generated-dir", type=Path, default=root / "projects/pipeline/data/generated")
    demo.add_argument("--report", type=Path, default=root / "projects/pipeline/artifacts/quality_report.html")
    inspect = sub.add_parser("inspect", help="Resume el estado de una base")
    inspect.add_argument("--database", type=Path, default=root / "projects/pipeline/data/portfolio.duckdb")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "generate":
        print(json.dumps([str(path) for path in generate_batches(args.output_dir)], indent=2))
    elif args.command == "run":
        result = process_batch(args.database, args.csv, batch_id=args.batch_id, simulate_failure_after_validation=args.simulate_failure)
        print(json.dumps(result.to_dict(), indent=2))
    elif args.command == "demo":
        print(json.dumps(run_demo(args.database, args.generated_dir, args.report), indent=2))
    elif args.command == "inspect":
        print(json.dumps(inspect_database(args.database), indent=2))


if __name__ == "__main__":
    main()
