import csv
import json
from pathlib import Path
import sqlite3

from data_migration.pipeline import run_migration


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_end_to_end_migration_reconciles_counts_and_amounts(tmp_path: Path) -> None:
    summary = run_migration(PROJECT_ROOT, tmp_path)

    assert summary["customers"]["source_rows"] == 8
    assert summary["customers"]["migrated_rows"] == 4
    assert summary["customers"]["duplicate_rows"] == 1
    assert summary["customers"]["rejected_rows"] == 3

    assert summary["transactions"]["source_rows"] == 10
    assert summary["transactions"]["migrated_rows"] == 5
    assert summary["transactions"]["duplicate_rows"] == 1
    assert summary["transactions"]["rejected_rows"] == 4
    assert summary["transactions"]["valid_source_total_eur"] == 3225.74
    assert summary["transactions"]["target_total_eur"] == 3225.74
    assert summary["transactions"]["total_difference_eur"] == 0
    assert summary["reconciliation_status"] == "PASS"


def test_outputs_are_traceable_and_target_has_no_orphans(tmp_path: Path) -> None:
    run_migration(PROJECT_ROOT, tmp_path)

    expected_files = {
        "target.db",
        "exception_log.csv",
        "migration_report.md",
        "reconciliation_report.md",
        "reconciliation_summary.json",
        "uat_checklist.md",
    }
    assert expected_files.issubset({path.name for path in tmp_path.iterdir()})

    with (tmp_path / "exception_log.csv").open(encoding="utf-8") as handle:
        exceptions = list(csv.DictReader(handle))
    assert len(exceptions) == 9
    assert {row["rule"] for row in exceptions} == {
        "DUPLICATE_KEY",
        "CUSTOMER_VALIDATION",
        "TRANSACTION_VALIDATION",
    }

    summary = json.loads(
        (tmp_path / "reconciliation_summary.json").read_text(encoding="utf-8")
    )
    assert summary["reconciliation_status"] == "PASS"

    with sqlite3.connect(tmp_path / "target.db") as connection:
        orphan_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM transactions t
            LEFT JOIN customers c ON c.customer_id = t.customer_id
            WHERE c.customer_id IS NULL
            """
        ).fetchone()[0]
    assert orphan_count == 0

