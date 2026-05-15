from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import re
from typing import Any


AUTHORITY = {
    "can_replace_medical_literature_review": False,
    "can_authorize_publication_quality": False,
}

_BIB_ENTRY_RE = re.compile(r"@\w+\s*\{\s*([^,\s]+)", re.MULTILINE)
_MANUSCRIPT_CITATION_RE = re.compile(r"(?<![A-Za-z0-9_])@([A-Za-z0-9_:.+\-]+)")
_MANUSCRIPT_SURFACE_CANDIDATES: tuple[tuple[str, ...], ...] = (
    ("build", "review_manuscript.md"),
    ("manuscript.md",),
    ("submission_minimal", "manuscript.md"),
)
_RENDERED_BIBLIOGRAPHY_CANDIDATES: tuple[tuple[str, ...], ...] = (
    ("references_rendered.txt",),
    ("submission_minimal", "references_rendered.txt"),
    ("build", "references_rendered.txt"),
)
_INITIALS_FIRST_AUTHOR_RE = re.compile(
    r"(?m)^\s*[A-Z](?:\s+[A-Z])?(?:,\s*[A-Z](?:\s+[A-Z])?){2,}\b"
)


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _append_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)


def _blocked_projection(
    *,
    paper_root: Path,
    blockers: list[str],
    refs: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface": "medical_literature_hygiene_projection",
        "authority": dict(AUTHORITY),
        "status": "blocked",
        "blockers": blockers,
        "refs": refs
        or {
            "paper_root": str(paper_root),
            "evidence_ledger_path": str(paper_root / "evidence_ledger.json"),
            "references_bib_path": str(paper_root / "references.bib"),
        },
        "coverage": {
            "manuscript_citation_key_count": 0,
            "reference_key_count": 0,
            "ledger_citation_key_count": 0,
            "pubmed_provenance_count": 0,
            "doi_provenance_count": 0,
            "guideline_provenance_count": 0,
        },
        "citation_key_sync": {
            "manuscript_keys_missing_from_references": [],
            "manuscript_keys_missing_from_ledger": [],
            "reference_keys_missing_from_ledger": [],
            "ledger_keys_missing_from_references": [],
        },
        "duplicate_citation_keys": [],
        "unsupported_citation_blockers": [],
        "bibliography_style_audit": {
            "status": "not_checked",
            "checked_path": None,
            "issues": [],
        },
    }


def _load_ledger(path: Path) -> tuple[list[Mapping[str, Any]] | None, str | None]:
    if not path.exists():
        return None, "evidence_ledger_missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "evidence_ledger_unreadable"
    if not isinstance(payload, Mapping):
        return None, "evidence_ledger_invalid"
    items = payload.get("items")
    if not isinstance(items, list):
        return None, "evidence_ledger_invalid"
    records: list[Mapping[str, Any]] = []
    for item in items:
        if not isinstance(item, Mapping):
            return None, "evidence_ledger_invalid"
        records.append(item)
    return records, None


def _manuscript_surface_paths(paper_root: Path) -> list[Path]:
    return [
        path
        for parts in _MANUSCRIPT_SURFACE_CANDIDATES
        if (path := paper_root.joinpath(*parts)).exists()
    ]


def _extract_manuscript_citation_keys(paper_root: Path) -> list[str]:
    keys: list[str] = []
    for path in _manuscript_surface_paths(paper_root):
        for match in _MANUSCRIPT_CITATION_RE.finditer(path.read_text(encoding="utf-8")):
            _append_unique(keys, match.group(1))
    return sorted(keys)


def _extract_bib_keys(path: Path) -> tuple[list[str], list[str], str | None]:
    if not path.exists():
        return [], [], "references_bib_missing"
    try:
        keys = [match.group(1).strip() for match in _BIB_ENTRY_RE.finditer(path.read_text(encoding="utf-8"))]
    except OSError:
        return [], [], "references_bib_unreadable"
    seen: set[str] = set()
    duplicates: list[str] = []
    for key in keys:
        if key in seen:
            _append_unique(duplicates, key)
        seen.add(key)
    return sorted(set(keys)), sorted(duplicates), None


def _record_citation_keys(record: Mapping[str, Any]) -> list[str]:
    keys: list[str] = []
    for field in ("citation_key", "key", "citekey", "bibtex_key"):
        if key := _text(record.get(field)):
            _append_unique(keys, key)
    raw_keys = record.get("citation_keys")
    if isinstance(raw_keys, list):
        for item in raw_keys:
            if key := _text(item):
                _append_unique(keys, key)
    return keys


def _ledger_key_map(records: list[Mapping[str, Any]]) -> tuple[dict[str, list[Mapping[str, Any]]], list[str]]:
    key_map: dict[str, list[Mapping[str, Any]]] = {}
    duplicate_keys: list[str] = []
    for record in records:
        for key in _record_citation_keys(record):
            bucket = key_map.setdefault(key, [])
            if bucket:
                _append_unique(duplicate_keys, key)
            bucket.append(record)
    return key_map, sorted(duplicate_keys)


def _has_pubmed_provenance(record: Mapping[str, Any]) -> bool:
    return bool(_text(record.get("pmid")) or _text(record.get("PMID")))


def _has_doi_provenance(record: Mapping[str, Any]) -> bool:
    return bool(_text(record.get("doi")) or _text(record.get("DOI")))


def _has_guideline_provenance(record: Mapping[str, Any]) -> bool:
    source_kind = (_text(record.get("source_kind")) or "").lower()
    return bool(
        _text(record.get("guideline_family"))
        or _text(record.get("reporting_guideline_family"))
        or source_kind == "guideline"
    )


def _has_supported_provenance(record: Mapping[str, Any]) -> bool:
    return (
        _has_pubmed_provenance(record)
        or _has_doi_provenance(record)
        or _has_guideline_provenance(record)
    )


def _unsupported_citation_blockers(
    *,
    manuscript_keys: list[str],
    ledger_key_map: dict[str, list[Mapping[str, Any]]],
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for key in manuscript_keys:
        records = ledger_key_map.get(key) or []
        if records and not any(_has_supported_provenance(record) for record in records):
            blockers.append(
                {
                    "citation_key": key,
                    "reason": "missing_pubmed_doi_or_guideline_provenance",
                }
            )
    return blockers


def _rendered_bibliography_path(paper_root: Path) -> Path | None:
    for parts in _RENDERED_BIBLIOGRAPHY_CANDIDATES:
        path = paper_root.joinpath(*parts)
        if path.exists():
            return path
    return None


def _build_bibliography_style_audit(
    *,
    paper_root: Path,
    require_rendered_bibliography: bool,
) -> dict[str, Any]:
    rendered_path = _rendered_bibliography_path(paper_root)
    if rendered_path is None:
        if not require_rendered_bibliography:
            return {
                "status": "not_checked",
                "checked_path": None,
                "issues": [],
            }
        return {
            "status": "blocked",
            "checked_path": None,
            "issues": [
                {
                    "code": "rendered_bibliography_missing",
                    "severity": "blocker",
                    "detail": "Rendered bibliography surface is required but was not found.",
                }
            ],
        }

    rendered_text = rendered_path.read_text(encoding="utf-8")
    issues: list[dict[str, str]] = []
    if _INITIALS_FIRST_AUTHOR_RE.search(rendered_text):
        issues.append(
            {
                "code": "initials_first_author_abbreviation",
                "severity": "blocker",
                "detail": "Rendered bibliography contains initials-first author abbreviations.",
            }
        )
    if "The lancet Diabetes & endocrinology" in rendered_text:
        issues.append(
            {
                "code": "journal_title_case_mismatch",
                "severity": "blocker",
                "detail": "Rendered bibliography contains an improperly cased journal title.",
            }
        )
    if not re.search(r"\b(?:doi|https?://)\b", rendered_text, flags=re.IGNORECASE):
        issues.append(
            {
                "code": "missing_doi_or_url",
                "severity": "issue",
                "detail": "Rendered bibliography entries should include DOI or URL when available.",
            }
        )
    return {
        "status": "blocked" if any(issue["severity"] == "blocker" for issue in issues) else "clear",
        "checked_path": str(rendered_path),
        "issues": issues,
    }


def build_medical_literature_hygiene_projection(
    *,
    paper_root: Path,
    require_rendered_bibliography: bool = False,
) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    references_bib_path = resolved_paper_root / "references.bib"
    evidence_ledger_path = resolved_paper_root / "evidence_ledger.json"
    refs = {
        "paper_root": str(resolved_paper_root),
        "evidence_ledger_path": str(evidence_ledger_path),
        "references_bib_path": str(references_bib_path),
    }

    ledger_records, ledger_blocker = _load_ledger(evidence_ledger_path)
    if ledger_blocker is not None or ledger_records is None:
        return _blocked_projection(
            paper_root=resolved_paper_root,
            blockers=[ledger_blocker or "evidence_ledger_unreadable"],
            refs=refs,
        )

    reference_keys, bib_duplicate_keys, references_blocker = _extract_bib_keys(references_bib_path)
    if references_blocker is not None:
        return _blocked_projection(paper_root=resolved_paper_root, blockers=[references_blocker], refs=refs)

    manuscript_keys = _extract_manuscript_citation_keys(resolved_paper_root)
    ledger_key_map, ledger_duplicate_keys = _ledger_key_map(ledger_records)
    ledger_keys = sorted(ledger_key_map)

    duplicate_citation_keys = sorted(set([*bib_duplicate_keys, *ledger_duplicate_keys]))
    citation_key_sync = {
        "manuscript_keys_missing_from_references": sorted(set(manuscript_keys) - set(reference_keys)),
        "manuscript_keys_missing_from_ledger": sorted(set(manuscript_keys) - set(ledger_keys)),
        "reference_keys_missing_from_ledger": sorted(set(reference_keys) - set(ledger_keys)),
        "ledger_keys_missing_from_references": sorted(set(ledger_keys) - set(reference_keys)),
    }
    unsupported_citation_blockers = _unsupported_citation_blockers(
        manuscript_keys=manuscript_keys,
        ledger_key_map=ledger_key_map,
    )
    bibliography_style_audit = _build_bibliography_style_audit(
        paper_root=resolved_paper_root,
        require_rendered_bibliography=require_rendered_bibliography,
    )

    blockers: list[str] = []
    if duplicate_citation_keys:
        blockers.append("duplicate_citation_keys")
    if any(citation_key_sync.values()):
        blockers.append("citation_key_sync_failed")
    if unsupported_citation_blockers:
        blockers.append("unsupported_citation_blockers_present")
    if bibliography_style_audit["status"] == "blocked":
        issue_codes = {issue.get("code") for issue in bibliography_style_audit["issues"]}
        if "rendered_bibliography_missing" in issue_codes:
            blockers.append("rendered_bibliography_missing")
        else:
            blockers.append("rendered_bibliography_style_mismatch")

    return {
        "schema_version": 1,
        "surface": "medical_literature_hygiene_projection",
        "authority": dict(AUTHORITY),
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "refs": refs,
        "coverage": {
            "manuscript_citation_key_count": len(set(manuscript_keys)),
            "reference_key_count": len(set(reference_keys)),
            "ledger_citation_key_count": len(set(ledger_keys)),
            "pubmed_provenance_count": sum(1 for record in ledger_records if _has_pubmed_provenance(record)),
            "doi_provenance_count": sum(1 for record in ledger_records if _has_doi_provenance(record)),
            "guideline_provenance_count": sum(1 for record in ledger_records if _has_guideline_provenance(record)),
        },
        "citation_key_sync": citation_key_sync,
        "duplicate_citation_keys": duplicate_citation_keys,
        "unsupported_citation_blockers": unsupported_citation_blockers,
        "bibliography_style_audit": bibliography_style_audit,
    }
