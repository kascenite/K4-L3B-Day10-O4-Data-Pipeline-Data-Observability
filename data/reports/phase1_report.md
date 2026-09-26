# Phase 1 Baseline Report

Generated at: 2026-09-26T05:49:46.529428+00:00

## Executive summary

The Phase 1 pipeline processed **24** clean papers, indexed them in ChromaDB, and evaluated **10** benchmark questions. The data quality gate status is **PASS** and the freshness SLA status is **PASS**.

## Source and indexing

| Field | Value |
|---|---|
| Source | Crossref REST API |
| Query | agentic retrieval augmented generation large language model |
| Raw records | 24 |
| Clean records | 24 |
| Chroma collection | `papers-baseline` |
| Indexed documents | 24 |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Evaluation questions | 10 |

## Baseline evaluation

| Metric | Value |
|---|---:|
| Retrieval hit rate | 100.00% |
| Mean token F1 | 1.0000 |
| Judge accuracy | 100.00% |
| Mean judge score | 5.00 |
| Ragas | Set RUN_RAGAS=1 to enable the slower Ragas pass. |

## Data quality gate

| Check | Result |
|---|---|
| Overall GX validation | PASS |
| Evaluated expectations | 6 |
| Failed expectations | 0 |

| Expectation | Column | Status | Observed value | Unexpected count |
|---|---|---:|---:|---:|
| expect_table_row_count_to_be_between | n/a | PASS | 24 | n/a |
| expect_column_values_to_not_be_null | paper_id | PASS | n/a | 0 |
| expect_column_values_to_be_unique | paper_id | PASS | n/a | 0 |
| expect_column_values_to_not_be_null | title | PASS | n/a | 0 |
| expect_column_value_lengths_to_be_between | summary | PASS | n/a | 0 |
| expect_column_values_to_be_between | age_days | PASS | n/a | 0 |

## Freshness SLA

| Field | Value |
|---|---:|
| Latest publication | 2026-09-15 |
| Oldest publication | 2026-04-01 |
| Threshold | 180 days |
| Maximum stale ratio | 25.00% |
| Stale records | 0 / 24 |
| Observed stale ratio | 0.00% |
| SLA status | PASS |

## Artifacts

| Artifact | Path |
|---|---|
| `clean_csv` | `data/clean/papers_clean.csv` |
| `clean_json` | `data/clean/papers_clean.json` |
| `chroma` | `data/chroma` |
| `test_set` | `data/eval/test_set.json` |
| `baseline_metrics` | `data/results/baseline_metrics.json` |
| `baseline_answers` | `data/results/baseline_answers.json` |
| `quality_report` | `data/quality/baseline_quality_report.json` |
| `freshness_report` | `data/quality/freshness_report.json` |
