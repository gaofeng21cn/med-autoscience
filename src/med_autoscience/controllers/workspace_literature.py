from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from med_autoscience.literature_records import LiteratureRecord
from med_autoscience.runtime_protocol.workspace_literature_status import (
    OPL_CONNECT_OWNER_REF,
    OPL_SOURCE_INTAKE_OWNER_REF,
    WORKSPACE_LITERATURE_SCHEMA_VERSION,
    workspace_literature_status,
)


def canonicalize_record_payload(*, raw_record: Mapping[str, object]) -> dict[str, object]:
    """Normalize medical literature semantics without owning its storage transport."""
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


def sync_workspace_literature(
    *,
    workspace_root: Path,
    records: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    canonical_records = [canonicalize_record_payload(raw_record=record) for record in records]
    unique_records = _dedupe_records(canonical_records)
    return {
        **workspace_literature_status(workspace_root=workspace_root),
        "surface_kind": "mas_literature_source_intake_request",
        "status": "opl_source_intake_required" if unique_records else "no_source_delta",
        "record_count": len(unique_records),
        "source_refs": [_source_ref(record) for record in unique_records],
        "records": unique_records,
        "source_mode": "domain_normalized_refs_for_opl_transport",
        "authority_boundary": _authority_boundary(),
    }


def init_workspace_literature(*, workspace_root: Path) -> dict[str, object]:
    status = workspace_literature_status(workspace_root=workspace_root)
    return {
        **status,
        "status": "opl_source_intake_required",
        "created_files": [],
        "skipped_files": [],
    }


def _dedupe_records(records: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    by_identity: dict[str, dict[str, object]] = {}
    for record in records:
        identity = _identity_key(record)
        existing = by_identity.get(identity)
        payload = dict(record)
        if existing is not None and existing != payload:
            raise ValueError(f"conflicting canonical literature record for {identity}")
        by_identity[identity] = payload
    return [by_identity[key] for key in sorted(by_identity)]


def _identity_key(record: Mapping[str, object]) -> str:
    for key in ("pmid", "pmcid", "doi", "arxiv_id"):
        if value := _optional_str(record.get(key)):
            return f"{key}:{value.lower()}"
    citation = record.get("citation_payload")
    if isinstance(citation, Mapping) and (url := _optional_str(citation.get("url"))):
        return f"url:{url.lower()}"
    return f"record:{_require_nonempty_str(record.get('record_id'), field='record_id').lower()}"


def _source_ref(record: Mapping[str, object]) -> dict[str, object]:
    return {
        "ref_kind": "medical_literature_ref",
        "record_id": record["record_id"],
        "doi": record.get("doi"),
        "pmid": record.get("pmid"),
        "pmcid": record.get("pmcid"),
        "arxiv_id": record.get("arxiv_id"),
        "relevance_role": record.get("relevance_role"),
        "claim_support_scope": list(record.get("claim_support_scope") or []),
    }


def _canonical_record_id(record: LiteratureRecord) -> str:
    for kind, value in (
        ("pmid", record.pmid),
        ("pmcid", record.pmcid),
        ("doi", record.doi),
        ("arxiv", record.arxiv_id),
    ):
        if value:
            return f"{kind}:{value}"
    citation_url = _optional_str(record.citation_payload.get("url"))
    return f"url:{citation_url}" if citation_url else record.record_id


def _normalize_record(raw_record: Mapping[str, object]) -> LiteratureRecord:
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
        claim_support_scope=_require_str_tuple(
            raw_record.get("claim_support_scope"),
            field="claim_support_scope",
        ),
    )


def _authority_boundary() -> dict[str, object]:
    return {
        "transport_owner": "one-person-lab",
        "domain_semantics_owner": "MedAutoScience",
        "mas_writes_generic_source_registry": False,
        "mas_materializes_workspace_bibtex": False,
        "mas_materializes_workspace_coverage": False,
        "mas_judges_medical_relevance": True,
    }


def _require_nonempty_str(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_str(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _optional_int(value: object, *, field: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int):
        raise ValueError(f"{field} must be an integer or null")
    return value


def _require_str_tuple(value: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field} must be a list of strings")
    items = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(items) != len(value):
        raise ValueError(f"{field} must contain non-empty strings")
    return items


def _require_dict(value: object, *, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a mapping")
    return dict(value)


__all__ = [
    "OPL_CONNECT_OWNER_REF",
    "OPL_SOURCE_INTAKE_OWNER_REF",
    "WORKSPACE_LITERATURE_SCHEMA_VERSION",
    "canonicalize_record_payload",
    "init_workspace_literature",
    "sync_workspace_literature",
    "workspace_literature_status",
]
