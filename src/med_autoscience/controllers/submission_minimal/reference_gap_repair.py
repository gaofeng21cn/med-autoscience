from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict
from pathlib import Path
import re
from typing import Any

from med_autoscience.adapters.literature import pubmed as pubmed_adapter
from med_autoscience.adapters.literature.opl_connect_receipts import records_from_resolution
from med_autoscience.literature_records import LiteratureRecord


def repair_submission_reference_gaps(
    *,
    paper_root: Path,
    workspace_root: Path,
    source_markdown_path: Path,
    references_path: Path | None,
    provider_receipts: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    from . import shared_base

    citation_keys = sorted(shared_base.markdown_citation_keys(source_markdown_path.read_text(encoding="utf-8")))
    if not citation_keys:
        return {"status": "not_required", "missing_citation_keys": []}
    reference_text = (
        references_path.read_text(encoding="utf-8")
        if references_path is not None and references_path.exists()
        else ""
    )
    missing_keys = sorted(set(citation_keys) - shared_base.bibtex_entry_keys(reference_text))
    if not missing_keys:
        return {"status": "already_complete", "missing_citation_keys": []}
    pmids_by_key = _pmids_by_submission_citation_key(missing_keys)
    unsupported_keys = [key for key in missing_keys if key not in pmids_by_key]
    if unsupported_keys:
        return {
            "status": "unsupported_missing_citation_keys",
            "missing_citation_keys": missing_keys,
            "unsupported_citation_keys": unsupported_keys,
        }

    requested_pmids = [pmids_by_key[key] for key in missing_keys]
    provider_resolution = pubmed_adapter.resolve_pubmed_summaries_from_receipts(
        pmids=requested_pmids,
        provider_receipts=provider_receipts,
    )
    fetched_records = list(records_from_resolution(provider_resolution))
    if provider_resolution["status"] != "resolved":
        return {
            "status": provider_resolution["status"],
            "missing_citation_keys": missing_keys,
            "requested_pmids": requested_pmids,
            "provider_resolution_request": provider_resolution["provider_resolution_request"],
            "provider_receipt_refs": provider_resolution["provider_receipt_refs"],
            "unresolved_citation_keys": [
                key
                for key in missing_keys
                if f"pmid:{pmids_by_key[key]}"
                in provider_resolution["missing_provider_evidence_reference_ids"]
            ],
        }
    fetched_by_key = {
        _submission_bibtex_key_for_record(record): record
        for record in fetched_records
        if _submission_bibtex_key_for_record(record) in missing_keys
    }
    still_missing = [key for key in missing_keys if key not in fetched_by_key]
    if still_missing:
        return {
            "status": "pubmed_records_missing",
            "missing_citation_keys": missing_keys,
            "unresolved_citation_keys": still_missing,
            "fetched_record_count": len(fetched_records),
        }

    source_path, source_kind = shared_base.resolve_submission_references_source(paper_root=paper_root)
    source_text = (
        source_path.read_text(encoding="utf-8")
        if source_path is not None and source_path.exists()
        else ""
    )
    existing_keys = shared_base.bibtex_entry_keys(source_text)
    appended_entries = [
        _render_submission_bib_entry(fetched_by_key[key])
        for key in missing_keys
        if key not in existing_keys
    ]
    target_path = paper_root / "references.bib"
    shared_base.write_text(target_path, _merge_references_text(source_text, appended_entries))
    workspace_literature_sync = _sync_workspace_literature(
        workspace_root=workspace_root,
        records=fetched_records,
    )
    return {
        "status": "repaired",
        "repair_scope": "study_paper_references",
        "source_kind": source_kind,
        "source_path": (
            shared_base._path_label_from_workspace(path=source_path, workspace_root=workspace_root)
            if source_path
            else None
        ),
        "output_path": shared_base._path_label_from_workspace(
            path=target_path,
            workspace_root=workspace_root,
        ),
        "missing_citation_keys": missing_keys,
        "fetched_pmids": requested_pmids,
        "fetched_record_count": len(fetched_records),
        "workspace_literature_sync": workspace_literature_sync,
    }


def _pmids_by_submission_citation_key(citation_keys: list[str]) -> dict[str, str]:
    pmids: dict[str, str] = {}
    for key in citation_keys:
        match = re.fullmatch(r"pmid[_:.-]?(\d+)", key, flags=re.IGNORECASE)
        if match:
            pmids[key] = match.group(1)
    return pmids


def _submission_bibtex_key_for_record(record: LiteratureRecord) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", record.record_id).strip("_") or "reference"


def _render_submission_bib_entry(record: LiteratureRecord) -> str:
    lines = [f"@article{{{_submission_bibtex_key_for_record(record)},", f"  title = {{{record.title}}},"]
    if record.authors:
        lines.append(f"  author = {{{' and '.join(record.authors)}}},")
    if record.journal:
        lines.append(f"  journal = {{{record.journal}}},")
    if record.year is not None:
        lines.append(f"  year = {{{record.year}}},")
    if record.doi:
        lines.append(f"  doi = {{{record.doi}}},")
    if record.pmid:
        lines.append(f"  pmid = {{{record.pmid}}},")
    lines.append("}")
    return "\n".join(lines) + "\n\n"


def _merge_references_text(source_text: str, appended_entries: list[str]) -> str:
    if not appended_entries:
        return source_text if source_text.endswith("\n") or not source_text else source_text + "\n"
    prefix = source_text.rstrip()
    return prefix + "\n\n" + "".join(appended_entries) if prefix else "".join(appended_entries)


def _sync_workspace_literature(
    *,
    workspace_root: Path,
    records: list[LiteratureRecord],
) -> dict[str, object] | None:
    if not records:
        return None
    from med_autoscience.controllers import workspace_literature as workspace_literature_controller

    return workspace_literature_controller.sync_workspace_literature(
        workspace_root=workspace_root,
        records=[asdict(record) for record in records],
    )


__all__ = ["repair_submission_reference_gaps"]
