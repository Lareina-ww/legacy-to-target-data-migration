# Migration Plan

## 1. Purpose

Demonstrate a controlled legacy-to-target migration for customer and transaction data. The project focuses on source profiling, field mapping, transformation, validation, loading, reconciliation, exception handling, and user acceptance testing.

## 2. Source and Target

- **Legacy source:** CSV exports representing customer and transaction tables from an older business system.
- **Target:** A relational SQLite database with required fields, primary keys, a foreign key, uniqueness checks, and amount constraints.
- **Mapping:** `config/field_mapping.json` defines each source field, target field, requirement status, and transformation rule.

## 3. Migration Stages

1. Profile source files and count missing values.
2. Detect duplicate business keys.
3. Clean text, identifiers, dates, country codes, statuses, and monetary values.
4. Reject invalid records and capture the reason in an exception log.
5. Load valid customer records before dependent transaction records.
6. Compare valid source counts and financial totals with target results.
7. Execute acceptance checks and prepare reports for review.

## 4. Data Quality Rules

- Customer and transaction identifiers must be present and unique.
- Required customer fields must be populated.
- Dates must match one of the supported legacy formats and be valid calendar dates.
- Transaction amounts must be valid and non-negative.
- Transactions may only reference customers that were successfully migrated.
- Target financial totals must equal the total of valid source transactions.

## 5. Exception Handling

Invalid and duplicate rows are not silently corrected or discarded. They are written to `outputs/exception_log.csv` with the dataset, row number, business key, failed rule, message, and action. A data owner would review these records before a production cutover.

## 6. Acceptance Criteria

- Migrated row counts match expected valid source row counts.
- Valid source and target transaction totals match exactly.
- The target contains no orphan transactions.
- Required target customer fields contain no null values.
- All exceptions are traceable to their source row.
- UAT results are documented for business sign-off.

## 7. Production Considerations

This mini-project uses synthetic data and SQLite. A production ERP migration would also require access controls, environment promotion, approved cutover and rollback plans, performance testing, backup validation, data-owner approvals, and post-go-live monitoring.

