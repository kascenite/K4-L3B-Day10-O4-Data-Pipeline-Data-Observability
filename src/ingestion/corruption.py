from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: str) -> pd.DataFrame:
    """Inject six reproducible data-quality failures and record their affected rows."""
    required_columns = {
        "paper_id",
        "title",
        "summary",
        "published",
        "authors_joined",
        "categories_joined",
    }
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError(f"Cannot corrupt dataframe; missing columns: {', '.join(sorted(missing_columns))}.")
    if df.empty:
        raise ValueError("Cannot corrupt an empty dataframe.")

    corrupted = df.copy()
    corrupted["published"] = pd.to_datetime(corrupted["published"], errors="coerce")
    if corrupted["published"].isna().any():
        raise ValueError("Cannot corrupt dataframe; published contains invalid dates.")

    log: dict[str, dict[str, object]] = {}

    drop_count = min(max(1, int(len(corrupted) * 0.2)), len(corrupted) - 1)
    dropped_indices = corrupted.nlargest(drop_count, "published").index
    corrupted = corrupted.drop(index=dropped_indices).copy()
    log["dropped_latest_records"] = {
        "count": int(drop_count),
        "affected_indices": [int(index) for index in dropped_indices],
    }

    sample_size = max(1, int(len(corrupted) * 0.1))

    def sample_indices(frame: pd.DataFrame, size: int, seed: int) -> pd.Index:
        return frame.sample(n=min(size, len(frame)), random_state=seed).index

    blank_indices = sample_indices(corrupted, sample_size, 41)
    corrupted.loc[blank_indices, "summary"] = ""
    log["blank_summary"] = {
        "count": len(blank_indices),
        "affected_indices": [int(index) for index in blank_indices],
    }

    nonblank_rows = corrupted.drop(index=blank_indices)
    noise_indices = sample_indices(nonblank_rows, sample_size, 42)
    corrupted.loc[noise_indices, "summary"] = (
        corrupted.loc[noise_indices, "summary"].astype(str) + " #@! NOISE_DATA !@#"
    )
    log["injected_noise"] = {
        "count": len(noise_indices),
        "affected_indices": [int(index) for index in noise_indices],
    }

    truncated_indices = sample_indices(corrupted, sample_size, 43)
    corrupted.loc[truncated_indices, "title"] = corrupted.loc[truncated_indices, "title"].astype(str).str[:7]
    log["truncated_title"] = {
        "count": len(truncated_indices),
        "affected_indices": [int(index) for index in truncated_indices],
    }

    stale_indices = sample_indices(corrupted, sample_size, 44)
    corrupted.loc[stale_indices, "published"] -= pd.Timedelta(days=365)
    log["stale_date"] = {
        "count": len(stale_indices),
        "affected_indices": [int(index) for index in stale_indices],
    }

    duplicate_indices = sample_indices(corrupted, sample_size, 45)
    corrupted = pd.concat([corrupted, corrupted.loc[duplicate_indices]], ignore_index=True)
    log["duplicated_rows"] = {
        "count": len(duplicate_indices),
        "original_indices_duplicated": [int(index) for index in duplicate_indices],
    }

    corrupted["summary_chars"] = corrupted["summary"].str.len()
    corrupted["age_days"] = (pd.Timestamp.now().normalize() - corrupted["published"]).dt.days
    corrupted["published"] = corrupted["published"].dt.strftime("%Y-%m-%d")
    corrupted["text_for_embedding"] = corrupted.apply(
        lambda row: "\n".join(
            (
                f"Title: {row['title']}",
                f"Authors: {row['authors_joined'] or 'Unknown'}",
                f"Published: {row['published']}",
                f"Categories: {row['categories_joined'] or 'Unknown'}",
                f"Summary: {row['summary']}",
            )
        ),
        axis=1,
    )

    log_path = Path(output_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[Corruption] Injected six failure types; detailed log saved to {log_path}")
    return corrupted