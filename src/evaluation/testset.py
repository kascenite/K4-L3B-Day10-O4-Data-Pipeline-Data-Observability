from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build a reproducible 10-question evaluation set from cleaned papers."""
    required = {"paper_id", "title", "summary", "authors", "published"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Cleaned dataframe is missing columns: {sorted(missing)}")

    papers = df.drop_duplicates("paper_id").to_dict(orient="records")
    if len(papers) < 10:
        raise ValueError(f"At least 10 unique papers are required; found {len(papers)}")

    # Three summary, three authors, two date, and two category questions.
    selections = [
        ("summary", 0), ("summary", 2), ("summary", 5),
        ("authors", 1), ("authors", 4), ("authors", 7),
        ("date", 10), ("date", 13),
        ("categories", 0), ("categories", 1),
    ]
    test_set: list[dict[str, Any]] = []
    for number, (kind, index) in enumerate(selections, start=1):
        paper = papers[index]
        title = str(paper["title"]).strip()
        if kind == "summary":
            answer = str(paper["summary"]).strip()
            question = f"Bài báo ‘{title}’ nghiên cứu vấn đề gì và đạt được kết quả nào?"
        elif kind == "authors":
            authors = paper["authors"]
            if isinstance(authors, str):
                authors = [name.strip() for name in authors.split(",") if name.strip()]
            answer = ", ".join(authors) if authors else "Không có thông tin tác giả trong dữ liệu."
            question = f"Ai là tác giả của bài báo ‘{title}’?"
        elif kind == "date":
            answer = str(paper["published"]).strip()
            question = f"Bài báo ‘{title}’ được xuất bản vào ngày nào?"
        else:
            categories = paper.get("categories") or []
            if isinstance(categories, str):
                categories = [value.strip() for value in categories.split(",") if value.strip()]
            answer = ", ".join(categories) or str(paper.get("primary_category") or "")
            if not answer:
                answer = "Bản ghi không có thông tin danh mục (categories)."
            question = f"Bản ghi của bài báo ‘{title}’ liệt kê những danh mục nào?"
        test_set.append({
            "id": f"q{number:02d}",
            "question_type": kind,
            "question": question,
            "ground_truth": answer,
            "ground_truth_doc_ids": [str(paper["paper_id"])],
        })

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(test_set, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return test_set
