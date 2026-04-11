from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from med_autoscience.literature_records import LiteratureRecord


WORKSPACE_LITERATURE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class WorkspaceLiteratureFile:
    path: Path
    content: str


def _workspace_literature_root(workspace_root: Path) -> Path:
    return workspace_root / "portfolio" / "research_memory" / "literature"


def _registry_path(workspace_root: Path) -> Path:
    return _workspace_literature_root(workspace_root) / "registry.jsonl"


def _references_bib_path(workspace_root: Path) -> Path:
    return _workspace_literature_root(workspace_root) / "references.bib"


def _coverage_path(workspace_root: Path) -> Path:
    return _workspace_literature_root(workspace_root) / "coverage" / "latest.json"


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


def _identity_key(record: LiteratureRecord) -> str:
    if record.pmid:
        return f"pmid:{record.pmid.lower()}"
    if record.pmcid:
        return f"pmcid:{record.pmcid.lower()}"
    if record.doi:
        return f"doi:{record.doi.lower()}"
    if record.arxiv_id:
        return f"arxiv:{record.arxiv_id.lower()}"
    citation_url = _optional_str(record.citation_payload.get("url"))
    if citation_url:
        return f"url:{citation_url.lower()}"
    return f"record:{record.record_id.lower()}"


def _canonical_record_id(record: LiteratureRecord) -> str:
    if record.pmid:
        return f"pmid:{record.pmid}"
    if record.pmcid:
        return f"pmcid:{record.pmcid}"
    if record.doi:
        return f"doi:{record.doi}"
    if record.arxiv_id:
        return f"arxiv:{record.arxiv_id}"
    citation_url = _optional_str(record.citation_payload.get("url"))
    if citation_url:
        return f"url:{citation_url}"
    return record.record_id


def _merge_optional_str(
    *,
    field: str,
    identity_key: str,
    existing: str | None,
    incoming: str | None,
) -> str | None:
    if existing is None:
        return incoming
    if incoming is None:
        return existing
    if existing != incoming:
        raise ValueError(f"conflicting canonical literature record for {identity_key}: field {field}")
    return existing


def _merge_optional_int(
    *,
    field: str,
    identity_key: str,
    existing: int | None,
    incoming: int | None,
) -> int | None:
    if existing is None:
        return incoming
    if incoming is None:
        return existing
    if existing != incoming:
        raise ValueError(f"conflicting canonical literature record for {identity_key}: field {field}")
    return existing


def _merge_str_tuple(
    *,
    field: str,
    identity_key: str,
    existing: tuple[str, ...],
    incoming: tuple[str, ...],
    allow_union: bool = False,
) -> tuple[str, ...]:
    if not existing:
        return incoming
    if not incoming:
        return existing
    if existing == incoming:
        return existing
    if allow_union:
        return tuple(dict.fromkeys([*existing, *incoming]))
    raise ValueError(f"conflicting canonical literature record for {identity_key}: field {field}")


def _merge_dict_values(
    *,
    identity_key: str,
    existing: dict[str, object],
    incoming: dict[str, object],
) -> dict[str, object]:
    merged = dict(existing)
    for key, value in incoming.items():
        if key not in merged:
            merged[key] = value
            continue
        if merged[key] != value:
            raise ValueError(f"conflicting canonical literature record for {identity_key}: citation_payload.{key}")
    return merged


def canonicalize_record_payload(*, raw_record: dict[str, object]) -> dict[str, object]:
    record = _normalize_record(raw_record)
    canonical = LiteratureRecord(
        record_id=_canonical_record_id(record),
        title=record.title,
        authors=record.authors,
        year=record.year,
        journal=record.journal,
        doi=record.doi,
        pmid=record.pmid,
        pmcid=record.pmcid,
        arxiv_id=record.arxiv_id,
        abstract=record.abstract,
        full_text_availability=record.full_text_availability,
        source_priority=record.source_priority,
        citation_payload=dict(record.citation_payload),
        local_asset_paths=record.local_asset_paths,
        relevance_role="canonical_reference",
        claim_support_scope=(),
    )
    return asdict(canonical)


def _merge_canonical_records(existing: LiteratureRecord, incoming: LiteratureRecord) -> LiteratureRecord:
    identity_key = _identity_key(existing)
    return LiteratureRecord(
        record_id=existing.record_id,
        title=_require_nonempty_str(
            _merge_optional_str(field="title", identity_key=identity_key, existing=existing.title, incoming=incoming.title),
            field="title",
        ),
        authors=_merge_str_tuple(
            field="authors",
            identity_key=identity_key,
            existing=existing.authors,
            incoming=incoming.authors,
        ),
        year=_merge_optional_int(field="year", identity_key=identity_key, existing=existing.year, incoming=incoming.year),
        journal=_merge_optional_str(
            field="journal",
            identity_key=identity_key,
            existing=existing.journal,
            incoming=incoming.journal,
        ),
        doi=_merge_optional_str(field="doi", identity_key=identity_key, existing=existing.doi, incoming=incoming.doi),
        pmid=_merge_optional_str(field="pmid", identity_key=identity_key, existing=existing.pmid, incoming=incoming.pmid),
        pmcid=_merge_optional_str(
            field="pmcid",
            identity_key=identity_key,
            existing=existing.pmcid,
            incoming=incoming.pmcid,
        ),
        arxiv_id=_merge_optional_str(
            field="arxiv_id",
            identity_key=identity_key,
            existing=existing.arxiv_id,
            incoming=incoming.arxiv_id,
        ),
        abstract=_merge_optional_str(
            field="abstract",
            identity_key=identity_key,
            existing=existing.abstract,
            incoming=incoming.abstract,
        ),
        full_text_availability=_require_nonempty_str(
            _merge_optional_str(
                field="full_text_availability",
                identity_key=identity_key,
                existing=existing.full_text_availability,
                incoming=incoming.full_text_availability,
            ),
            field="full_text_availability",
        ),
        source_priority=min(existing.source_priority, incoming.source_priority),
        citation_payload=_merge_dict_values(
            identity_key=identity_key,
            existing=existing.citation_payload,
            incoming=incoming.citation_payload,
        ),
        local_asset_paths=_merge_str_tuple(
            field="local_asset_paths",
            identity_key=identity_key,
            existing=existing.local_asset_paths,
            incoming=incoming.local_asset_paths,
            allow_union=True,
        ),
        relevance_role="canonical_reference",
        claim_support_scope=(),
    )


def _registry_records(path: Path) -> list[LiteratureRecord]:
    if not path.exists():
        return []
    records: list[LiteratureRecord] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        records.append(_normalize_record(json.loads(line)))
    return records


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


def _render_bibliography(records: list[LiteratureRecord]) -> str:
    return "".join(_render_bib_entry(record) for record in records)


def _bibliography_entry_count(text: str) -> int:
    if not text.strip():
        return 0
    return text.count("\n@") + (1 if text.lstrip().startswith("@") else 0)


def _coverage_payload(records: list[LiteratureRecord]) -> dict[str, object]:
    return {
        "schema_version": WORKSPACE_LITERATURE_SCHEMA_VERSION,
        "record_count": len(records),
        "records_with_doi": sum(1 for record in records if record.doi),
        "records_with_pmid": sum(1 for record in records if record.pmid),
        "records_by_primary_source": {
            "pubmed": sum(1 for record in records if record.primary_source == "pubmed"),
            "imported": sum(1 for record in records if record.primary_source != "pubmed"),
        },
        "high_priority_missing": [],
    }


def _render_readme() -> str:
    return (
        "# Workspace Canonical Literature\n\n"
        "这里存放 disease workspace 跨 study 复用的 canonical 文献层。\n\n"
        "它负责：\n\n"
        "- 维护跨 study 可复用的去重文献 registry\n"
        "- 为 study reference context 和 quest materialization 提供稳定 authority root\n"
        "- 提供 workspace 级 bibliography 与 coverage summary\n"
    )


def render_workspace_literature_files(*, workspace_root: Path) -> list[WorkspaceLiteratureFile]:
    return [
        WorkspaceLiteratureFile(path=_workspace_literature_root(workspace_root) / "README.md", content=_render_readme()),
        WorkspaceLiteratureFile(path=_registry_path(workspace_root), content=""),
        WorkspaceLiteratureFile(path=_references_bib_path(workspace_root), content=""),
        WorkspaceLiteratureFile(
            path=_coverage_path(workspace_root),
            content=json.dumps(_coverage_payload([]), ensure_ascii=False, indent=2) + "\n",
        ),
    ]


def init_workspace_literature(*, workspace_root: Path) -> dict[str, object]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    root = _workspace_literature_root(resolved_workspace_root)
    root.mkdir(parents=True, exist_ok=True)
    created_files: list[str] = []
    skipped_files: list[str] = []
    for rendered in render_workspace_literature_files(workspace_root=resolved_workspace_root):
        if rendered.path.exists():
            skipped_files.append(str(rendered.path))
            continue
        _write_text(rendered.path, rendered.content)
        created_files.append(str(rendered.path))
    return {
        "schema_version": WORKSPACE_LITERATURE_SCHEMA_VERSION,
        "workspace_root": str(resolved_workspace_root),
        "workspace_literature_root": str(root),
        "created_files": created_files,
        "skipped_files": skipped_files,
        "registry_path": str(_registry_path(resolved_workspace_root)),
        "references_bib_path": str(_references_bib_path(resolved_workspace_root)),
        "coverage_report_path": str(_coverage_path(resolved_workspace_root)),
    }


def sync_workspace_literature(*, workspace_root: Path, records: list[dict[str, object]]) -> dict[str, object]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    init_workspace_literature(workspace_root=resolved_workspace_root)
    existing_records = _registry_records(_registry_path(resolved_workspace_root))
    records_by_identity = {_identity_key(record): record for record in existing_records}

    for raw_record in records:
        canonical = _normalize_record(canonicalize_record_payload(raw_record=raw_record))
        identity_key = _identity_key(canonical)
        existing = records_by_identity.get(identity_key)
        if existing is None:
            records_by_identity[identity_key] = canonical
        else:
            records_by_identity[identity_key] = _merge_canonical_records(existing, canonical)

    merged_records = sorted(records_by_identity.values(), key=lambda item: item.record_id)
    _write_text(_registry_path(resolved_workspace_root), _render_jsonl(merged_records))
    bibliography_text = _render_bibliography(merged_records)
    _write_text(_references_bib_path(resolved_workspace_root), bibliography_text)
    _write_json(_coverage_path(resolved_workspace_root), _coverage_payload(merged_records))
    status = workspace_literature_status(workspace_root=resolved_workspace_root)
    status["source_mode"] = "synchronized"
    return status


def workspace_literature_status(*, workspace_root: Path) -> dict[str, object]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    root = _workspace_literature_root(resolved_workspace_root)
    registry_path = _registry_path(resolved_workspace_root)
    references_bib_path = _references_bib_path(resolved_workspace_root)
    coverage_report_path = _coverage_path(resolved_workspace_root)
    registry_records = _registry_records(registry_path)
    bibliography_text = references_bib_path.read_text(encoding="utf-8") if references_bib_path.exists() else ""
    coverage = (
        json.loads(coverage_report_path.read_text(encoding="utf-8"))
        if coverage_report_path.exists()
        else _coverage_payload(registry_records)
    )
    return {
        "schema_version": WORKSPACE_LITERATURE_SCHEMA_VERSION,
        "workspace_root": str(resolved_workspace_root),
        "workspace_literature_root": str(root),
        "workspace_literature_exists": root.exists(),
        "registry_path": str(registry_path),
        "references_bib_path": str(references_bib_path),
        "coverage_report_path": str(coverage_report_path),
        "record_count": len(registry_records),
        "references_bib_entry_count": _bibliography_entry_count(bibliography_text),
        "coverage": coverage if isinstance(coverage, dict) else _coverage_payload(registry_records),
    }
