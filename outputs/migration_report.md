# Migration Report

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
| customers | legacy_customer_id | customer_id | trim and uppercase | Yes |
| customers | full_name | customer_name | trim and collapse whitespace | Yes |
| customers | email | email | trim and lowercase | Yes |
| customers | country_code | country | trim and uppercase ISO alpha-2 | Yes |
| customers | created_date | created_at | convert supported formats to YYYY-MM-DD | Yes |
| customers | status | is_active | map active to 1 and inactive to 0 | Yes |
| transactions | legacy_txn_id | transaction_id | trim and uppercase | Yes |
| transactions | legacy_customer_id | customer_id | trim and uppercase; validate against migrated customers | Yes |
| transactions | transaction_date | transaction_date | convert supported formats to YYYY-MM-DD | Yes |
| transactions | amount_eur | amount_cents | remove thousands separators and convert EUR to integer cents | Yes |
| transactions | status | transaction_status | map completed, paid, or settled to SETTLED | Yes |

## Migration Result

- Customers loaded: 4
- Transactions loaded: 5
- Exceptions recorded: 9
- Reconciliation status: PASS

## Deliverables

- `target.db`: migrated target database
- `reconciliation_report.md`: source-to-target counts and financial totals
- `reconciliation_summary.json`: machine-readable reconciliation results
- `exception_log.csv`: rejected and duplicate records with reasons
- `uat_checklist.md`: acceptance checks and sign-off section

## Cutover Note

This is a controlled mini-project. A production migration would additionally require approved data owners, environment-specific access controls, cutover scheduling, backup and rollback procedures, and formal business sign-off.
