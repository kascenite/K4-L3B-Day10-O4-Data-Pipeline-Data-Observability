from __future__ import annotations

from dataclasses import asdict, dataclass
import html
from pathlib import Path
import re
import time

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


CROSSREF_API_URL = "https://api.crossref.org/works"
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 4
# Over-fetch so enough records survive validation / English-only filtering.
FETCH_MULTIPLIER = 2
# Function words of other Latin-script languages; non-Latin scripts are caught by the ASCII check.
NON_ENGLISH_FUNCTION_WORDS = {
    "dan", "yang", "untuk", "dengan", "pada", "dalam", "berbasis", "menggunakan", "terhadap", "sebagai",  # id/ms
    "del", "los", "las", "el", "y", "para", "con", "por", "una", "uma", "com", "em", "dos", "das",  # es/pt
    "le", "les", "des", "du", "et", "pour", "avec", "dans", "sur", "une",  # fr
    "der", "und", "mit", "zur", "zum", "eine", "einer", "het", "een", "voor",  # de/nl
}


def _strip_tags(value: str) -> str:
    return normalize_whitespace(html.unescape(re.sub(r"<[^>]+>", " ", value or "")))


def _date_from_parts(field: dict | None) -> str:
    parts = ((field or {}).get("date-parts") or [[]])[0]
    if not parts or parts[0] is None:
        return ""
    year, month, day = (list(parts) + [1, 1])[:3]
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def _is_english(title: str, language: str | None) -> bool:
    if language and not language.lower().startswith("en"):
        return False
    if any(ch.isalpha() and not ch.isascii() for ch in title):
        return False
    words = set(re.findall(r"[a-z]+", title.lower()))
    return not words & NON_ENGLISH_FUNCTION_WORDS


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    records: list[PaperRecord] = []
    seen: set[str] = set()
    for item in payload.get("message", {}).get("items", []):
        doi = normalize_whitespace(item.get("DOI", "")).lower()
        title = _strip_tags(" ".join(item.get("title") or []))
        summary = _strip_tags(item.get("abstract", ""))
        if not doi or not title or not summary or doi in seen:
            continue
        if not _is_english(title, item.get("language")):
            continue
        seen.add(doi)

        authors = [
            normalize_whitespace(f"{a.get('given', '')} {a.get('family', '')}") or normalize_whitespace(a.get("name", ""))
            for a in item.get("author") or []
        ]
        authors = [a for a in authors if a]
        categories = [normalize_whitespace(c) for c in item.get("subject") or [] if c]
        published = (
            _date_from_parts(item.get("published"))
            or _date_from_parts(item.get("published-online"))
            or _date_from_parts(item.get("published-print"))
            or _date_from_parts(item.get("issued"))
            or _date_from_parts(item.get("created"))
        )
        updated = (item.get("created") or {}).get("date-time", "")[:10] or published
        url = item.get("URL") or f"https://doi.org/{doi}"
        pdf_url = next(
            (link.get("URL") for link in item.get("link") or [] if link.get("content-type") == "application/pdf"),
            url,
        )

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=categories[0] if categories else "",
                published=published,
                updated=updated,
                abs_url=url,
                pdf_url=pdf_url,
                comment=f"Crossref record {doi}",
            )
        )
    return records


def _request_crossref(settings: Settings) -> dict:
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results * FETCH_MULTIPLIER,
        "sort": "relevance",
    }
    headers = {"User-Agent": "day10-data-observability-lab/0.1 (student lab)"}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = requests.get(CROSSREF_API_URL, params=params, headers=headers, timeout=30)
        if response.status_code in RETRY_STATUS_CODES and attempt < MAX_ATTEMPTS:
            wait = float(response.headers.get("Retry-After", 2**attempt))
            print(f"[crossref] HTTP {response.status_code}, retry {attempt}/{MAX_ATTEMPTS - 1} after {wait:.0f}s")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError("unreachable")


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch from Crossref (with retry); fall back to the local raw snapshot on failure."""
    raw_path = settings.paths.raw_api_response
    try:
        payload = _request_crossref(settings)
        write_json(raw_path, payload)
        print(f"[crossref] fetched live data -> {raw_path}")
    except (requests.RequestException, ValueError) as exc:
        if not raw_path.exists():
            raise RuntimeError(f"Crossref fetch failed and no local snapshot at {raw_path}") from exc
        print(f"[crossref] fetch failed ({exc}); using local snapshot {raw_path}")
        payload = read_json(raw_path)

    records = parse_crossref_payload(payload)[: settings.max_results]
    write_json(settings.paths.raw_records_json, [asdict(r) for r in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    return [PaperRecord(**row) for row in read_json(path)]
