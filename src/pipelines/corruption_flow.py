from __future__ import annotations

import json

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def _save_clean_data(df: pd.DataFrame, csv_path, json_path) -> None:
    write_csv(df, csv_path)
    records = json.loads(df.to_json(orient="records", date_format="iso"))
    write_json(json_path, records)


def main() -> None:
    """Corruption -> evaluate -> repair -> compare flow."""
    settings = load_settings()

    print("=== BẮT ĐẦU LUỒNG SILENT FAILURE & REPAIR ===")

    # ------------------------------------------------------------------
    # 1. Load baseline metrics
    # ------------------------------------------------------------------
    print("\n1. Đang tải baseline metrics...")
    baseline_metrics = read_json(settings.paths.baseline_metrics)

    # ------------------------------------------------------------------
    # 2. Load clean data & corrupt it
    # ------------------------------------------------------------------
    print("2. Đang tải clean dataset và tạo corrupted dataframe...")
    df_clean = pd.read_csv(settings.paths.clean_csv)
    df_corrupted = corrupt_clean_dataframe(df_clean, str(settings.paths.corruption_log))

    # Save corrupted artifacts
    _save_clean_data(df_corrupted, settings.paths.corrupted_clean_csv, settings.paths.corrupted_clean_json)

    # ------------------------------------------------------------------
    # 3. Run quality checks on corrupted data
    # ------------------------------------------------------------------
    print("3. Đang chạy Data Observability (Great Expectations) trên dữ liệu hỏng...")
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, "corrupted")

    # ------------------------------------------------------------------
    # 4. Rebuild index & evaluate on corrupted data
    # ------------------------------------------------------------------
    print("4. Rebuild Vector DB và Đánh giá RAG trên Corrupted Data...")
    corrupted_index = LocalEmbeddingIndex.build(
        df_corrupted, settings, settings.paths.corrupted_embeddings_json
    )
    corrupted_eval = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    corrupted_metrics = corrupted_eval.summary
    print(f"   Corrupted hit_rate={corrupted_metrics['retrieval_hit_rate']:.2%}")

    # ------------------------------------------------------------------
    # 5. Repair: re-clean from raw records
    # ------------------------------------------------------------------
    print("5. [BÁO ĐỘNG] Dữ liệu hỏng! Tiến hành phục hồi từ raw records...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    df_repaired = build_clean_dataframe(raw_records, now_utc())
    _save_clean_data(df_repaired, settings.paths.repaired_clean_csv, settings.paths.repaired_clean_json)

    # ------------------------------------------------------------------
    # 6. Quality checks on repaired data
    # ------------------------------------------------------------------
    print("6. Đang chạy Data Observability trên dữ liệu đã phục hồi...")
    repaired_quality = run_data_quality_checks(df_repaired, settings, "repaired")

    # ------------------------------------------------------------------
    # 7. Rebuild index & evaluate on repaired data
    # ------------------------------------------------------------------
    print("7. Rebuild Vector DB và Đánh giá lại RAG trên Repaired Data...")
    repaired_index = LocalEmbeddingIndex.build(
        df_repaired, settings, settings.paths.repaired_embeddings_json
    )
    repaired_eval = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_metrics = repaired_eval.summary
    print(f"   Repaired hit_rate={repaired_metrics['retrieval_hit_rate']:.2%}")

    # ------------------------------------------------------------------
    # 8. Generate comparison report
    # ------------------------------------------------------------------
    print("\n8. Đang tạo báo cáo đối chiếu 3 trạng thái...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_quality.get("freshness", {}),
        repaired_freshness=repaired_quality.get("freshness", {}),
    )

    # ------------------------------------------------------------------
    # 9. Print summary
    # ------------------------------------------------------------------
    print("\n=== KẾT QUẢ ĐỐI CHIẾU ===")
    header = f"{'Metric':<25} {'Baseline':>12} {'Corrupted':>12} {'Repaired':>12}"
    print(header)
    print("-" * len(header))
    for key in ("retrieval_hit_rate", "mean_token_f1"):
        b = baseline_metrics.get(key, 0)
        c = corrupted_metrics.get(key, 0)
        r = repaired_metrics.get(key, 0)
        print(f"{key:<25} {b:>12.4f} {c:>12.4f} {r:>12.4f}")
    print(f"\nĐã xuất báo cáo tại: {settings.paths.comparison_report}")
    print("=== HOÀN TẤT ===")


if __name__ == "__main__":
    main()