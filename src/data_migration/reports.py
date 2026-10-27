from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def write_exception_log(path: Path, exceptions: list[dict[str, Any]]) -> None:
    fieldnames = [
        "dataset",
        "row_number",
        "business_key",
        "rule",
        "severity",
        "message",
        "action",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(exceptions)


def write_summary_json(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def write_reconciliation_report(path: Path, summary: dict[str, Any]) -> None:
    customers = summary["customers"]
    transactions = summary["transactions"]
    content = f"""# Reconciliation Report

Generated: {summary['generated_at']}

## Customer Reconciliation

| Measure | Value |
|---|---:|
| Source rows | {customers['source_rows']} |
| Unique source keys | {customers['unique_source_keys']} |
| Duplicate rows rejected | {customers['duplicate_rows']} |
| Invalid rows rejected | {customers['rejected_rows']} |
| Target rows | {customers['migrated_rows']} |
| Missing source values | {customers['missing_values']} |

## Transaction Reconciliation

| Measure | Value |
|---|---:|
| Source rows | {transactions['source_rows']} |
| Unique source keys | {transactions['unique_source_keys']} |
| Duplicate rows rejected | {transactions['duplicate_rows']} |
| Invalid rows rejected | {transactions['rejected_rows']} |
| Target rows | {transactions['migrated_rows']} |
| Valid source total | EUR {transactions['valid_source_total_eur']:.2f} |
| Target total | EUR {transactions['target_total_eur']:.2f} |
| Total difference | EUR {transactions['total_difference_eur']:.2f} |

## Result

**{summary['reconciliation_status']}**

Rejected and duplicate records are documented in `exception_log.csv` and were not loaded into the target database.
"""
    path.write_text(content, encoding="utf-8")


def write_uat_checklist(path: Path, checks: list[dict[str, str]]) -> None:
    rows = "\n".join(
        f"| {item['id']} | {item['test']} | {item['expected']} | {item['actual']} | {item['status']} |"
        for item in checks
    )
    content = f"""# User Acceptance Testing Checklist

| ID | Test | Expected | Actual | Status |
|---|---|---|---|---|
{rows}

## Sign-off

- Business owner: ____________________
- Data owner: ____________________
- Date: ____________________
- Decision: Accept / Accept with exceptions / Reject

Open exceptions should be reviewed in `exception_log.csv` before sign-off.
"""
    path.write_text(content, encoding="utf-8")


def write_migration_report(
    path: Path,
    summary: dict[str, Any],
    mapping: dict[str, list[dict[str, Any]]],
) -> None:
    mapping_rows: list[str] = []
    for dataset, fields in mapping.items():
        for field in fields:
            mapping_rows.append(
                f"| {dataset} | {field['source']} | {field['target']} | "
                f"{field['transformation']} | {'Yes' if field['required'] else 'No'} |"
            )
    content = f"""# Migration Report

## Objective

Migrate legacy customer and transaction exports into a relational SQLite target while preserving traceability, rejecting invalid records, and reconciling migrated counts and financial totals.

## Scope

- Source: CSV exports in `data/legacy/`
- Target: SQLite database in `outputs/target.db`
- Migration method: Python transformations plus SQL target constraints
- Controls: duplicate detection, required-field checks, date and amount validation, referential-integrity checks, count reconciliation, and financial-total reconciliation

## Source-to-Target Mapping

| Dataset | Source field | Target field | Transformation | Required |
|---|---|---|---|---|
{chr(10).join(mapping_rows)}

## Migration Result

- Customers loaded: {summary['customers']['migrated_rows']}
- Transactions loaded: {summary['transactions']['migrated_rows']}
- Exceptions recorded: {summary['exceptions']['total']}
- Reconciliation status: {summary['reconciliation_status']}

## Deliverables

- `target.db`: migrated target database
- `reconciliation_report.md`: source-to-target counts and financial totals
- `reconciliation_summary.json`: machine-readable reconciliation results
- `exception_log.csv`: rejected and duplicate records with reasons
- `uat_checklist.md`: acceptance checks and sign-off section

## Cutover Note

This is a controlled mini-project. A production migration would additionally require approved data owners, environment-specific access controls, cutover scheduling, backup and rollback procedures, and formal business sign-off.
"""
    path.write_text(content, encoding="utf-8")

