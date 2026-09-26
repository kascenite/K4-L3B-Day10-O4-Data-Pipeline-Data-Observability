# Corruption & Repair Report

Generated at: 2026-09-26T05:03:24.863968+00:00

## Executive Summary

This report compares three pipeline states to demonstrate the impact of data corruption
on RAG retrieval quality and the effectiveness of the idempotent repair mechanism.

- **Corrupted quality gate**: FAIL
- **Repaired quality gate**: PASS

## Metrics Comparison (Baseline vs Corrupted vs Repaired)

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| Retrieval Hit Rate | 1.0000 | 0.5000 | 1.0000 |
| Mean Token F1 | 1.0000 | 0.7187 | 1.0000 |
| Judge Accuracy | 1.0000 | 0.7000 | 1.0000 |
| Mean Judge Score | 5.0000 | 3.8000 | 5.0000 |

## Data Quality Gate

| Check | Corrupted | Repaired |
|---|---|---|
| GX Validation | FAIL | PASS |
| Failed Expectations | 3 | 0 |

## Freshness SLA

| Field | Corrupted | Repaired |
|---|---:|---:|
| Stale Ratio | 9.09% | 0.00% |
| Is Fresh | YES | YES |

## Conclusion

The system detected Silent Failure when Hit Rate dropped from **1.0000** to **0.5000** after data corruption.
After triggering the idempotent repair flow from raw records, performance recovered to **1.0000**.
