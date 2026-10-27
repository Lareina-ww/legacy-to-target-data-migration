# Legacy-to-Target Data Migration

A small, reproducible data migration project that moves synthetic customer and transaction records from legacy CSV exports into a relational SQLite target.

The project demonstrates the core controls used in a migration: source profiling, source-to-target mapping, cleansing, standardisation, duplicate handling, referential validation, loading, reconciliation, exception reporting, and user acceptance testing.

## What the project does

- Defines legacy and target schemas plus documented field mappings.
- Cleans and standardises identifiers, names, emails, country codes, dates, statuses, and monetary values.
- Rejects duplicate or invalid records into a traceable exception log.
- Loads valid customer and transaction records into SQLite using SQL constraints.
- Reconciles source and target row counts and financial totals.
- Produces a migration report, reconciliation report, exception log, and UAT checklist.
- Includes automated tests for transformations and the complete migration flow.

## Project structure

```text
.
├── config/field_mapping.json
├── data/legacy/
│   ├── customers.csv
│   └── transactions.csv
├── docs/migration_plan.md
├── outputs/
├── sql/target_schema.sql
├── src/data_migration/
│   ├── pipeline.py
│   ├── reports.py
│   └── transform.py
├── tests/
├── Makefile
├── requirements.txt
└── run_migration.py
```

## Run locally

```bash
make setup
make test
make migrate
```

Equivalent commands without `make`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python run_migration.py
```

## Generated deliverables

After running the migration, `outputs/` contains:

- `target.db`: migrated SQLite database
- `exception_log.csv`: rejected and duplicate records with reasons
- `reconciliation_summary.json`: machine-readable migration metrics
- `reconciliation_report.md`: source-to-target counts and totals
- `uat_checklist.md`: acceptance tests and sign-off fields
- `migration_report.md`: scope, mapping, controls, results, and production considerations

## Expected result

- 4 of 8 customer rows migrate successfully.
- 5 of 10 transaction rows migrate successfully.
- Duplicate and invalid rows are recorded as exceptions.
- Valid source and target transaction totals reconcile to **EUR 3,225.74**.
- All automated UAT checks pass.

## Scope note

This project uses synthetic data and SQLite to demonstrate migration methodology. It does not claim experience with a live SAP or Microsoft Dynamics 365 implementation. The same principles can be extended to ERP migrations with system-specific extraction, security, cutover, rollback, and post-go-live controls.

