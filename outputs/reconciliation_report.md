# Reconciliation Report

Generated: 2026-10-27T22:07:13.186094+00:00

## Customer Reconciliation

| Measure | Value |
|---|---:|
| Source rows | 8 |
| Unique source keys | 7 |
| Duplicate rows rejected | 1 |
| Invalid rows rejected | 3 |
| Target rows | 4 |
| Missing source values | 1 |

## Transaction Reconciliation

| Measure | Value |
|---|---:|
| Source rows | 10 |
| Unique source keys | 9 |
| Duplicate rows rejected | 1 |
| Invalid rows rejected | 4 |
| Target rows | 5 |
| Valid source total | EUR 3225.74 |
| Target total | EUR 3225.74 |
| Total difference | EUR 0.00 |

## Result

**PASS**

Rejected and duplicate records are documented in `exception_log.csv` and were not loaded into the target database.
