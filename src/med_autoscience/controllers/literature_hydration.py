from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re
from typing import Any

from med_autoscience.literature_records import LiteratureRecord


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _require_nonempty_str(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _optional_int(value: object, *, field: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int):
        raise ValueError(f"{field} must be an integer or null")
    return value


def _require_str_tuple(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field} must be a list of strings")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field} must contain non-empty strings")
        items.append(item.strip())
    return tuple(items)


def _require_dict(value: object, *, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a mapping")
    return dict(value)


def _normalize_record(raw_record: object) -> LiteratureRecord:
    if not isinstance(raw_record, dict):
        raise ValueError("literature record must be a mapping")
    source_priority = raw_record.get("source_priority")
    if not isinstance(source_priority, int):
        raise ValueError("source_priority must be an integer")
    return LiteratureRecord(
        record_id=_require_nonempty_str(raw_record.get("record_id"), field="record_id"),
        title=_require_nonempty_str(raw_record.get("title"), field="title"),
        authors=_require_str_tuple(raw_record.get("authors"), field="authors"),
        year=_optional_int(raw_record.get("year"), field="year"),
        journal=_optional_str(raw_record.get("journal")),
        doi=_optional_str(raw_record.get("doi")),
        pmid=_optional_str(raw_record.get("pmid")),
        pmcid=_optional_str(raw_record.get("pmcid")),
        arxiv_id=_optional_str(raw_record.get("arxiv_id")),
        abstract=_optional_str(raw_record.get("abstract")),
        full_text_availability=_require_nonempty_str(
            raw_record.get("full_text_availability"),
            field="full_text_availability",
        ),
        source_priority=source_priority,
        citation_payload=_require_dict(raw_record.get("citation_payload"), field="citation_payload"),
        local_asset_paths=_require_str_tuple(raw_record.get("local_asset_paths"), field="local_asset_paths"),
        relevance_role=_require_nonempty_str(raw_record.get("relevance_role"), field="relevance_role"),
        claim_support_scope=_require_str_tuple(raw_record.get("claim_support_scope"), field="claim_support_scope"),
    )


def _render_jsonl(records: list[LiteratureRecord]) -> str:
    if not records:
        return ""
    return "".join(json.dumps(asdict(record), ensure_ascii=False) + "\n" for record in records)


def _bibtex_key(record_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", record_id).strip("_") or "reference"


def _render_bib_entry(record: LiteratureRecord) -> str:
    lines = [f"@article{{{_bibtex_key(record.record_id)},", f"  title = {{{record.title}}},"]
    if record.authors:
        lines.append(f"  author = {{{' and '.join(record.authors)}}},")
    if record.journal:
        lines.append(f"  journal = {{{record.journal}}},")
    if record.year is not None:
        lines.append(f"  year = {{{record.year}}},")
    if record.doi:
        lines.append(f"  doi = {{{record.doi}}},")
    lines.append("}")
    return "\n".join(lines) + "\n\n"


def run_literature_hydration(*, quest_root: Path, records: list[dict[str, object]]) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    normalized_records = [_normalize_record(item) for item in records]

    pubmed_records_path = resolved_quest_root / "literature" / "pubmed" / "records.jsonl"
    imported_records_path = resolved_quest_root / "literature" / "imported" / "records.jsonl"
    references_bib_path = resolved_quest_root / "paper" / "references.bib"
    coverage_path = resolved_quest_root / "paper" / "reference_coverage_report.json"

    pubmed_records = [record for record in normalized_records if record.primary_source == "pubmed"]
    imported_records = [record for record in normalized_records if record.primary_source != "pubmed"]

    _write_text(pubmed_records_path, _render_jsonl(pubmed_records))
    _write_text(imported_records_path, _render_jsonl(imported_records))
    _write_text(references_bib_path, "".join(_render_bib_entry(record) for record in normalized_records))
    _write_json(
        coverage_path,
        {
            "record_count": len(normalized_records),
            "records_with_doi": sum(1 for record in normalized_records if record.doi),
            "records_with_pmid": sum(1 for record in normalized_records if record.pmid),
            "records_by_primary_source": {
                "pubmed": sum(1 for record in normalized_records if record.primary_source == "pubmed"),
                "imported": sum(1 for record in normalized_records if record.primary_source != "pubmed"),
            },
            "high_priority_missing": [],
        },
    )

    return {
        "status": "hydrated",
        "record_count": len(normalized_records),
        "records_path": str(pubmed_records_path),
        "imported_records_path": str(imported_records_path),
        "references_bib_path": str(references_bib_path),
        "coverage_report_path": str(coverage_path),
    }
