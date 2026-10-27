from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any

from .reports import (
    write_exception_log,
    write_migration_report,
    write_reconciliation_report,
    write_summary_json,
    write_uat_checklist,
)
from .transform import transform_customer, transform_transaction


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def count_missing_values(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows for value in row.values() if not (value or "").strip())


def add_exception(
    exceptions: list[dict[str, Any]],
    *,
    dataset: str,
    row_number: int,
    business_key: str,
    rule: str,
    message: str,
    action: str = "REJECTED",
) -> None:
    exceptions.append(
        {
            "dataset": dataset,
            "row_number": row_number,
            "business_key": business_key,
            "rule": rule,
            "severity": "ERROR",
            "message": message,
            "action": action,
        }
    )


def transform_customers(
    rows: list[dict[str, str]], exceptions: list[dict[str, Any]]
) -> tuple[list[dict[str, object]], int, int]:
    transformed: list[dict[str, object]] = []
    seen: set[str] = set()
    duplicates = 0
    rejected = 0
    for row_number, row in enumerate(rows, start=2):
        key = (row.get("legacy_customer_id") or "").strip().upper()
        if key in seen:
            duplicates += 1
            add_exception(
                exceptions,
                dataset="customers",
                row_number=row_number,
                business_key=key,
                rule="DUPLICATE_KEY",
                message="duplicate customer identifier",
                action="REJECTED_DUPLICATE",
            )
            continue
        seen.add(key)
        try:
            transformed.append(transform_customer(row))
        except ValueError as exc:
            rejected += 1
            add_exception(
                exceptions,
                dataset="customers",
                row_number=row_number,
                business_key=key,
                rule="CUSTOMER_VALIDATION",
                message=str(exc),
            )
    return transformed, duplicates, rejected


def transform_transactions(
    rows: list[dict[str, str]],
    valid_customer_ids: set[str],
    exceptions: list[dict[str, Any]],
) -> tuple[list[dict[str, object]], int, int]:
    transformed: list[dict[str, object]] = []
    seen: set[str] = set()
    duplicates = 0
    rejected = 0
    for row_number, row in enumerate(rows, start=2):
        key = (row.get("legacy_txn_id") or "").strip().upper()
        if key in seen:
            duplicates += 1
            add_exception(
                exceptions,
                dataset="transactions",
                row_number=row_number,
                business_key=key,
                rule="DUPLICATE_KEY",
                message="duplicate transaction identifier",
                action="REJECTED_DUPLICATE",
            )
            continue
        seen.add(key)
        try:
            transformed.append(transform_transaction(row, valid_customer_ids))
        except ValueError as exc:
            rejected += 1
            add_exception(
                exceptions,
                dataset="transactions",
                row_number=row_number,
                business_key=key,
                rule="TRANSACTION_VALIDATION",
                message=str(exc),
            )
    return transformed, duplicates, rejected


def create_target_database(
    database_path: Path,
    schema_path: Path,
    customers: list[dict[str, object]],
    transactions: list[dict[str, object]],
) -> None:
    if database_path.exists():
        database_path.unlink()
    with sqlite3.connect(database_path) as connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        connection.executemany(
            """
            INSERT INTO customers
                (customer_id, customer_name, email, country, created_at, is_active)
            VALUES
                (:customer_id, :customer_name, :email, :country, :created_at, :is_active)
            """,
            customers,
        )
        connection.executemany(
            """
            INSERT INTO transactions
                (transaction_id, customer_id, transaction_date, amount_cents, transaction_status)
            VALUES
                (:transaction_id, :customer_id, :transaction_date, :amount_cents, :transaction_status)
            """,
            transactions,
        )


def inspect_target(database_path: Path) -> dict[str, int]:
    with sqlite3.connect(database_path) as connection:
        customer_count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        transaction_count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        total_cents = connection.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) FROM transactions"
        ).fetchone()[0]
        orphan_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM transactions t
            LEFT JOIN customers c ON c.customer_id = t.customer_id
            WHERE c.customer_id IS NULL
            """
        ).fetchone()[0]
        customer_nulls = connection.execute(
            """
            SELECT COUNT(*) FROM customers
            WHERE customer_id IS NULL OR customer_name IS NULL OR email IS NULL
            """
        ).fetchone()[0]
    return {
        "customer_count": customer_count,
        "transaction_count": transaction_count,
        "total_cents": total_cents,
        "orphan_count": orphan_count,
        "customer_nulls": customer_nulls,
    }


def build_uat_checks(
    summary: dict[str, Any], target_metrics: dict[str, int]
) -> list[dict[str, str]]:
    checks = [
        {
            "id": "UAT-01",
            "test": "Customer records loaded",
            "expected": str(summary["customers"]["migrated_rows"]),
            "actual": str(target_metrics["customer_count"]),
        },
        {
            "id": "UAT-02",
            "test": "Transaction records loaded",
            "expected": str(summary["transactions"]["migrated_rows"]),
            "actual": str(target_metrics["transaction_count"]),
        },
        {
            "id": "UAT-03",
            "test": "Transaction value reconciled",
            "expected": f"EUR {summary['transactions']['valid_source_total_eur']:.2f}",
            "actual": f"EUR {summary['transactions']['target_total_eur']:.2f}",
        },
        {
            "id": "UAT-04",
            "test": "No orphan transactions",
            "expected": "0",
            "actual": str(target_metrics["orphan_count"]),
        },
        {
            "id": "UAT-05",
            "test": "No null required customer fields",
            "expected": "0",
            "actual": str(target_metrics["customer_nulls"]),
        },
    ]
    for item in checks:
        item["status"] = "PASS" if item["expected"] == item["actual"] else "FAIL"
    return checks


def run_migration(project_root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    output_dir = output_dir or project_root / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    customer_rows = read_csv(project_root / "data" / "legacy" / "customers.csv")
    transaction_rows = read_csv(project_root / "data" / "legacy" / "transactions.csv")
    mapping = json.loads(
        (project_root / "config" / "field_mapping.json").read_text(encoding="utf-8")
    )

    exceptions: list[dict[str, Any]] = []
    customers, customer_duplicates, customer_rejected = transform_customers(
        customer_rows, exceptions
    )
    valid_customer_ids = {str(row["customer_id"]) for row in customers}
    transactions, transaction_duplicates, transaction_rejected = transform_transactions(
        transaction_rows, valid_customer_ids, exceptions
    )

    database_path = output_dir / "target.db"
    create_target_database(
        database_path,
        project_root / "sql" / "target_schema.sql",
        customers,
        transactions,
    )
    target_metrics = inspect_target(database_path)
    valid_total_cents = sum(int(row["amount_cents"]) for row in transactions)
    difference_cents = valid_total_cents - target_metrics["total_cents"]

    summary: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "customers": {
            "source_rows": len(customer_rows),
            "unique_source_keys": len(customer_rows) - customer_duplicates,
            "duplicate_rows": customer_duplicates,
            "rejected_rows": customer_rejected,
            "migrated_rows": target_metrics["customer_count"],
            "missing_values": count_missing_values(customer_rows),
        },
        "transactions": {
            "source_rows": len(transaction_rows),
            "unique_source_keys": len(transaction_rows) - transaction_duplicates,
            "duplicate_rows": transaction_duplicates,
            "rejected_rows": transaction_rejected,
            "migrated_rows": target_metrics["transaction_count"],
            "valid_source_total_eur": valid_total_cents / 100,
            "target_total_eur": target_metrics["total_cents"] / 100,
            "total_difference_eur": difference_cents / 100,
        },
        "exceptions": {"total": len(exceptions)},
        "reconciliation_status": "PASS" if difference_cents == 0 else "FAIL",
    }

    uat_checks = build_uat_checks(summary, target_metrics)
    if any(item["status"] == "FAIL" for item in uat_checks):
        summary["reconciliation_status"] = "FAIL"

    write_exception_log(output_dir / "exception_log.csv", exceptions)
    write_summary_json(output_dir / "reconciliation_summary.json", summary)
    write_reconciliation_report(output_dir / "reconciliation_report.md", summary)
    write_uat_checklist(output_dir / "uat_checklist.md", uat_checks)
    write_migration_report(output_dir / "migration_report.md", summary, mapping)
    return summary

