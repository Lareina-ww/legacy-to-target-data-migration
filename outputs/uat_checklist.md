# User Acceptance Testing Checklist

| ID | Test | Expected | Actual | Status |
|---|---|---|---|---|
| UAT-01 | Customer records loaded | 4 | 4 | PASS |
| UAT-02 | Transaction records loaded | 5 | 5 | PASS |
| UAT-03 | Transaction value reconciled | EUR 3225.74 | EUR 3225.74 | PASS |
| UAT-04 | No orphan transactions | 0 | 0 | PASS |
| UAT-05 | No null required customer fields | 0 | 0 | PASS |

## Sign-off

- Business owner: ____________________
- Data owner: ____________________
- Date: ____________________
- Decision: Accept / Accept with exceptions / Reject

Open exceptions should be reviewed in `exception_log.csv` before sign-off.
