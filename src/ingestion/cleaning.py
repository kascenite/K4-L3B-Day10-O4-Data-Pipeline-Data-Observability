from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import html
import re

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord

MIN_SUMMARY_CHARS = 50
# Leading section heading left over from <jats:title>Abstract</jats:title>.
ABSTRACT_HEADING = re.compile(r"^(abstract|summary)\b[\s.:\-\u2013\u2014]*", re.IGNORECASE)


def _clean_text(value) -> str:
    if not isinstance(value, str):
        return ""
    # Crossref abstracts carry JATS XML (<jats:p>, <jats:italic>, ...) and HTML entities.
    return normalize_whitespace(html.unescape(re.sub(r"<[^>]+>", " ", value)))


def _clean_list(values) -> list[str]:
    seen: dict[str, None] = {}
    for value in values if isinstance(values, list) else []:
        cleaned = _clean_text(value)
        if cleaned:
            seen.setdefault(cleaned, None)
    return list(seen)


def _text_for_embedding(row: pd.Series) -> str:
    return "\n".join(
        [
            f"Title: {row['title']}",
            f"Authors: {row['authors_joined'] or 'Unknown'}",
            f"Published: {row['published']}",
            f"Categories: {row['categories_joined'] or 'Unknown'}",
            f"Summary: {row['summary']}",
        ]
    )


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    df = pd.DataFrame([asdict(r) for r in records], columns=list(PaperRecord.__dataclass_fields__))

    df["paper_id"] = df["paper_id"].map(_clean_text).str.lower()
    for column in ("title", "summary", "primary_category", "abs_url", "pdf_url", "comment"):
        df[column] = df[column].map(_clean_text)
    df["summary"] = df["summary"].str.replace(ABSTRACT_HEADING, "", regex=True)
    df["authors"] = df["authors"].map(_clean_list)
    df["categories"] = df["categories"].map(_clean_list)
    df["primary_category"] = df.apply(
        lambda row: row["primary_category"] or (row["categories"][0] if row["categories"] else ""), axis=1
    )

    published = pd.to_datetime(df["published"], errors="coerce")
    updated = pd.to_datetime(df["updated"], errors="coerce").fillna(published)
    df["published"] = published.dt.strftime("%Y-%m-%d")
    df["updated"] = updated.dt.strftime("%Y-%m-%d")
    df["age_days"] = (pd.Timestamp(run_date.date()) - published).dt.days

    df["authors_joined"] = df["authors"].map(compact_join)
    df["categories_joined"] = df["categories"].map(compact_join)
    df["summary_chars"] = df["summary"].str.len()

    # Filter bad rows, then de-duplicate by paper_id.
    valid = (
        (df["paper_id"] != "")
        & (df["title"] != "")
        & (df["summary_chars"] >= MIN_SUMMARY_CHARS)
        & published.notna()
    )
    df = df[valid].drop_duplicates(subset="paper_id", keep="first")

    df["age_days"] = df["age_days"].astype(int)
    df["text_for_embedding"] = df.apply(_text_for_embedding, axis=1)
    return df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
