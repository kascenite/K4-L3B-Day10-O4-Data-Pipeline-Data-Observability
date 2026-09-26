from __future__ import annotations

from typing import Any

import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd

from core.config import Settings
from core.utils import write_json

# Freshness SLA: the dataset is stale if more than 25% of papers are older than the threshold.
MAX_STALE_RATIO = 0.25
MIN_SUMMARY_CHARS = 50
MAX_SUMMARY_CHARS = 10_000


def _build_suite(settings: Settings) -> gx.ExpectationSuite:
    suite = gx.ExpectationSuite(name="papers_quality_suite")
    for expectation in (
        gxe.ExpectTableRowCountToBeBetween(min_value=settings.max_results, max_value=settings.max_results),
        gxe.ExpectColumnValuesToNotBeNull(column="paper_id"),
        gxe.ExpectColumnValuesToBeUnique(column="paper_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="title"),
        gxe.ExpectColumnValueLengthsToBeBetween(
            column="summary", min_value=MIN_SUMMARY_CHARS, max_value=MAX_SUMMARY_CHARS
        ),
        # Freshness SLA as an expectation: at least 75% of rows within the threshold.
        gxe.ExpectColumnValuesToBeBetween(
            column="age_days",
            min_value=0,
            max_value=settings.freshness_threshold_days,
            mostly=1 - MAX_STALE_RATIO,
        ),
    ):
        suite.add_expectation(expectation)
    return suite


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = context.suites.add(_build_suite(settings))
    validation = batch.validate(suite)

    expectations = []
    for result in validation.results:
        config = result.expectation_config
        observed = result.result or {}
        expectations.append(
            {
                "expectation": config.type,
                "column": config.kwargs.get("column"),
                "success": bool(result.success),
                "observed_value": observed.get("observed_value"),
                "unexpected_count": observed.get("unexpected_count"),
                "unexpected_percent": observed.get("unexpected_percent"),
            }
        )

    freshness = build_freshness_report(df, settings, settings.paths.quality_dir / f"{report_name}_freshness.json")
    payload = {
        "report_name": report_name,
        "success": bool(validation.success),
        "row_count": int(len(df)),
        "evaluated_expectations": len(expectations),
        "failed_expectations": sum(not e["success"] for e in expectations),
        "expectations": expectations,
        "freshness": freshness,
    }
    write_json(settings.paths.quality_dir / f"{report_name}_quality_report.json", payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    published = pd.to_datetime(df["published"], errors="coerce")
    age_days = pd.to_numeric(df["age_days"], errors="coerce")
    total_rows = int(len(df))
    stale_rows = int((age_days > settings.freshness_threshold_days).sum())
    stale_ratio = stale_rows / total_rows if total_rows else 1.0

    payload = {
        "latest_published": published.max().strftime("%Y-%m-%d") if published.notna().any() else None,
        "oldest_published": published.min().strftime("%Y-%m-%d") if published.notna().any() else None,
        "threshold_days": settings.freshness_threshold_days,
        "max_stale_ratio": MAX_STALE_RATIO,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": round(stale_ratio, 4),
        "is_fresh": total_rows > 0 and stale_ratio <= MAX_STALE_RATIO,
    }
    write_json(report_path, payload)
    return payload
