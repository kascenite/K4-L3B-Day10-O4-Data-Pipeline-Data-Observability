from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from core.utils import write_text


def _percent(value: Any) -> str:
    try:
        return f"{float(value):.2%}"
    except (TypeError, ValueError):
        return "n/a"


def _number(value: Any, digits: int = 4) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "n/a"


def _cell(value: Any) -> str:
    return str(value if value is not None else "n/a").replace("|", "\\|").replace("\n", " ")


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a self-contained Markdown report for the baseline pipeline."""
    expectations = quality.get("expectations", [])
    expectation_rows = "\n".join(
        "| {expectation} | {column} | {success} | {observed} | {unexpected} |".format(
            expectation=_cell(item.get("expectation")),
            column=_cell(item.get("column")),
            success="PASS" if item.get("success") else "FAIL",
            observed=_cell(item.get("observed_value")),
            unexpected=_cell(item.get("unexpected_count")),
        )
        for item in expectations
    ) or "| n/a | n/a | n/a | n/a | n/a |"

    artifacts = source_summary.get("artifacts", {})
    artifact_rows = "\n".join(
        f"| `{_cell(name)}` | `{_cell(path)}` |" for name, path in artifacts.items()
    ) or "| n/a | n/a |"

    ragas = metrics.get("ragas", {})
    if isinstance(ragas, dict) and ragas.get("skipped"):
        ragas_status = ragas["skipped"]
    elif isinstance(ragas, dict) and ragas.get("error"):
        ragas_status = ragas["error"]
    else:
        ragas_status = "Completed" if ragas else "Not configured"

    report = f"""# Phase 1 Baseline Report

Generated at: {datetime.now(UTC).isoformat()}

## Executive summary

The Phase 1 pipeline processed **{_cell(source_summary.get('clean_records'))}** clean papers, indexed them in ChromaDB, and evaluated **{_cell(metrics.get('samples'))}** benchmark questions. The data quality gate status is **{'PASS' if quality.get('success') else 'FAIL'}** and the freshness SLA status is **{'PASS' if freshness.get('is_fresh') else 'FAIL'}**.

## Source and indexing

| Field | Value |
|---|---|
| Source | {_cell(source_summary.get('source'))} |
| Query | {_cell(source_summary.get('query'))} |
| Raw records | {_cell(source_summary.get('raw_records'))} |
| Clean records | {_cell(source_summary.get('clean_records'))} |
| Chroma collection | `{_cell(source_summary.get('collection_name'))}` |
| Indexed documents | {_cell(source_summary.get('indexed_documents'))} |
| Embedding model | `{_cell(source_summary.get('embedding_model'))}` |
| Evaluation questions | {_cell(source_summary.get('test_questions'))} |

## Baseline evaluation

| Metric | Value |
|---|---:|
| Retrieval hit rate | {_percent(metrics.get('retrieval_hit_rate'))} |
| Mean token F1 | {_number(metrics.get('mean_token_f1'))} |
| Judge accuracy | {_percent(metrics.get('judge_accuracy'))} |
| Mean judge score | {_number(metrics.get('mean_judge_score'), 2)} |
| Ragas | {_cell(ragas_status)} |

## Data quality gate

| Check | Result |
|---|---|
| Overall GX validation | {'PASS' if quality.get('success') else 'FAIL'} |
| Evaluated expectations | {_cell(quality.get('evaluated_expectations'))} |
| Failed expectations | {_cell(quality.get('failed_expectations'))} |

| Expectation | Column | Status | Observed value | Unexpected count |
|---|---|---:|---:|---:|
{expectation_rows}

## Freshness SLA

| Field | Value |
|---|---:|
| Latest publication | {_cell(freshness.get('latest_published'))} |
| Oldest publication | {_cell(freshness.get('oldest_published'))} |
| Threshold | {_cell(freshness.get('threshold_days'))} days |
| Maximum stale ratio | {_percent(freshness.get('max_stale_ratio'))} |
| Stale records | {_cell(freshness.get('stale_rows'))} / {_cell(freshness.get('total_rows'))} |
| Observed stale ratio | {_percent(freshness.get('stale_ratio'))} |
| SLA status | {'PASS' if freshness.get('is_fresh') else 'FAIL'} |

## Artifacts

| Artifact | Path |
|---|---|
{artifact_rows}
"""
    write_text(report_path, report)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write a Markdown report comparing Baseline vs Corrupted vs Repaired."""

    def _get(d: dict, key: str) -> str:
        v = d.get(key)
        if v is None:
            return "n/a"
        try:
            return f"{float(v):.4f}"
        except (TypeError, ValueError):
            return str(v)

    report = f"""# Corruption & Repair Report

Generated at: {datetime.now(UTC).isoformat()}

## Executive Summary

This report compares three pipeline states to demonstrate the impact of data corruption
on RAG retrieval quality and the effectiveness of the idempotent repair mechanism.

- **Corrupted quality gate**: {'PASS' if corrupted_quality.get('success') else 'FAIL'}
- **Repaired quality gate**: {'PASS' if repaired_quality.get('success') else 'FAIL'}

## Metrics Comparison (Baseline vs Corrupted vs Repaired)

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| Retrieval Hit Rate | {_get(baseline_metrics, 'retrieval_hit_rate')} | {_get(corrupted_metrics, 'retrieval_hit_rate')} | {_get(repaired_metrics, 'retrieval_hit_rate')} |
| Mean Token F1 | {_get(baseline_metrics, 'mean_token_f1')} | {_get(corrupted_metrics, 'mean_token_f1')} | {_get(repaired_metrics, 'mean_token_f1')} |
| Judge Accuracy | {_get(baseline_metrics, 'judge_accuracy')} | {_get(corrupted_metrics, 'judge_accuracy')} | {_get(repaired_metrics, 'judge_accuracy')} |
| Mean Judge Score | {_get(baseline_metrics, 'mean_judge_score')} | {_get(corrupted_metrics, 'mean_judge_score')} | {_get(repaired_metrics, 'mean_judge_score')} |

## Data Quality Gate

| Check | Corrupted | Repaired |
|---|---|---|
| GX Validation | {'PASS' if corrupted_quality.get('success') else 'FAIL'} | {'PASS' if repaired_quality.get('success') else 'FAIL'} |
| Failed Expectations | {_cell(corrupted_quality.get('failed_expectations'))} | {_cell(repaired_quality.get('failed_expectations'))} |

## Freshness SLA

| Field | Corrupted | Repaired |
|---|---:|---:|
| Stale Ratio | {_percent(corrupted_freshness.get('stale_ratio'))} | {_percent(repaired_freshness.get('stale_ratio'))} |
| Is Fresh | {'YES' if corrupted_freshness.get('is_fresh') else 'NO'} | {'YES' if repaired_freshness.get('is_fresh') else 'NO'} |

## Conclusion

The system detected Silent Failure when Hit Rate dropped from **{_get(baseline_metrics, 'retrieval_hit_rate')}** to **{_get(corrupted_metrics, 'retrieval_hit_rate')}** after data corruption.
After triggering the idempotent repair flow from raw records, performance recovered to **{_get(repaired_metrics, 'retrieval_hit_rate')}**.
"""
    write_text(report_path, report)

