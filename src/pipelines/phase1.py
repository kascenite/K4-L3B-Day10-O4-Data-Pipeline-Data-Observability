from __future__ import annotations

import json

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def _save_clean_data(df: pd.DataFrame, csv_path, json_path) -> None:
    write_csv(df, csv_path)
    # Convert Timestamp/numpy scalar values to plain JSON-compatible values.
    records = json.loads(df.to_json(orient="records", date_format="iso"))
    write_json(json_path, records)


def _load_or_fetch_records(settings):
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        return fetch_source_records(settings)
    return load_raw_records(settings.paths.raw_records_json)


def main() -> None:
    """Run ingestion, cleaning, validation, indexing, and baseline evaluation."""
    settings = load_settings()
    print("[phase1] Loading source records")
    records = _load_or_fetch_records(settings)

    print(f"[phase1] Cleaning {len(records)} raw records")
    clean_df = build_clean_dataframe(records, now_utc())
    if clean_df.empty:
        raise RuntimeError("Cleaning produced no valid records; baseline pipeline stopped.")
    _save_clean_data(clean_df, settings.paths.clean_csv, settings.paths.clean_json)

    print("[phase1] Running Great Expectations quality gate and freshness SLA")
    quality = run_data_quality_checks(clean_df, settings, "baseline")
    freshness = quality["freshness"]
    # Keep the canonical freshness artifact requested by the project config.
    write_json(settings.paths.freshness_report, freshness)
    if not quality["success"]:
        failed = quality.get("failed_expectations", "unknown")
        raise RuntimeError(f"Data quality gate failed ({failed} failed expectations).")

    print(f"[phase1] Building Chroma collection '{settings.baseline_collection_name}'")
    index = LocalEmbeddingIndex.build(clean_df, settings, settings.paths.embeddings_json)
    indexed_documents = index.collection.count()
    if indexed_documents != len(clean_df):
        raise RuntimeError(
            f"Chroma indexed {indexed_documents} documents, expected {len(clean_df)}."
        )

    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        test_set = build_test_set(clean_df, settings.paths.eval_testset)
    else:
        test_set = read_json(settings.paths.eval_testset)
    if len(test_set) != 10:
        raise RuntimeError(f"Evaluation set must contain 10 questions; found {len(test_set)}.")

    print(f"[phase1] Evaluating {len(test_set)} benchmark questions")
    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    artifact_paths = {
        "clean_csv": settings.paths.clean_csv,
        "clean_json": settings.paths.clean_json,
        "chroma": settings.paths.chroma_dir,
        "test_set": settings.paths.eval_testset,
        "baseline_metrics": settings.paths.baseline_metrics,
        "baseline_answers": settings.paths.baseline_answers,
        "quality_report": settings.paths.baseline_quality_report,
        "freshness_report": settings.paths.freshness_report,
    }
    source_summary = {
        "source": settings.source_api,
        "query": settings.source_query,
        "raw_records": len(records),
        "clean_records": len(clean_df),
        "collection_name": index.collection_name,
        "indexed_documents": indexed_documents,
        "embedding_model": settings.embedding_model,
        "test_questions": len(test_set),
        "artifacts": {
            name: path.relative_to(settings.paths.project_dir).as_posix()
            for name, path in artifact_paths.items()
        },
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=evaluation.summary,
        quality=quality,
        freshness=freshness,
    )

    print(
        "[phase1] Complete: "
        f"{len(clean_df)} papers, hit_rate={evaluation.summary['retrieval_hit_rate']:.2%}, "
        f"mean_token_f1={evaluation.summary['mean_token_f1']:.4f}"
    )
    print(f"[phase1] Report: {settings.paths.baseline_report}")
