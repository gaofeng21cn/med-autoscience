from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.submission_package_layout import (
    build_analysis_manifest_document,
    build_source_relative_paths_document,
    build_source_signature_document,
    audit_path,
    reproducibility_path,
    resolve_submission_manifest_path,
)

from .delivery_context import FORMAL_PAPER_DELIVERY_RELATIVE_PATHS
from .delivery_io import (
    build_zip_from_directory,
    copy_file,
    copy_tree,
    dump_json,
    reset_directory,
    write_text,
)
from .delivery_rendering import (
    build_current_package_readme,
    build_submission_todo_from_manifest,
)


def _append_generated_file(
    generated_files: list[dict[str, str]],
    *,
    category: str,
    path: Path,
) -> None:
    generated_files.append(
        {
            "category": category,
            "path": str(path.resolve()),
        }
    )


def _build_zip_from_directory(*, source_root: Path, output_path: Path) -> None:
    build_zip_from_directory(source_root=source_root, output_path=output_path)


__all__ = [
    "sync_current_package_projection",
]


def _copy_current_package_audit_surfaces(
    *,
    paper_root: Path | None,
    source_root: Path,
    current_package_root: Path,
    resolved_projected_current_package_root: Path,
    copied_files: list[dict[str, str]],
    review_ledger_source: Path | None,
    charter_contract_linkage: dict[str, Any] | None,
) -> tuple[dict[str, Any], Path]:
    if paper_root is not None:
        resolved_paper_root = Path(paper_root).expanduser().resolve()
        for relative_path in FORMAL_PAPER_DELIVERY_RELATIVE_PATHS:
            source_path = resolved_paper_root / relative_path
            if not source_path.exists():
                continue
            copy_file(
                source=source_path,
                target=audit_path(current_package_root, "evidence_ledger"),
                category="current_package",
                copied_files=copied_files,
            )
    if review_ledger_source is not None and review_ledger_source.exists():
        copy_file(
            source=review_ledger_source,
            target=audit_path(current_package_root, "review_ledger"),
            category="current_package_review_surface",
            copied_files=copied_files,
        )

    linkage_payload = charter_contract_linkage if charter_contract_linkage is not None else {}
    study_charter_ref = dict(linkage_payload.get("study_charter_ref") or {})
    raw_charter_artifact_path = str(study_charter_ref.get("artifact_path") or "").strip()
    if raw_charter_artifact_path:
        charter_artifact_path = Path(raw_charter_artifact_path).expanduser()
        if charter_artifact_path.exists():
            copy_file(
                source=charter_artifact_path,
                target=audit_path(current_package_root, "study_charter"),
                category="current_package_charter_surface",
                copied_files=copied_files,
            )
            study_charter_ref["mirrored_artifact_path"] = str(
                audit_path(resolved_projected_current_package_root, "study_charter")
            )
            linkage_payload["study_charter_ref"] = study_charter_ref

    source_manifest_path = resolve_submission_manifest_path(source_root)
    if source_manifest_path.exists() and not audit_path(current_package_root, "submission_manifest").exists():
        copy_file(
            source=source_manifest_path,
            target=audit_path(current_package_root, "submission_manifest"),
            category="current_package_manifest",
            copied_files=copied_files,
        )
    return linkage_payload, source_manifest_path


def _source_signature_payload_from_manifest(source_manifest_path: Path) -> dict[str, Any]:
    if not source_manifest_path.exists():
        return {"source_signature": ""}
    try:
        source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"source_signature": ""}
    if not isinstance(source_manifest, dict):
        return {"source_signature": ""}
    source_contract = (
        source_manifest.get("source_contract")
        if isinstance(source_manifest.get("source_contract"), dict)
        else {}
    )
    source_signature = str(
        source_manifest.get("source_signature") or source_contract.get("source_signature") or ""
    ).strip()
    return {
        "source_signature": source_signature,
        "source_contract": source_contract,
        "source_paths": list(source_contract.get("source_paths") or []),
        "source_files": list(source_contract.get("source_files") or []),
    }


def _write_current_package_reproducibility_documents(
    *,
    current_package_root: Path,
    source_signature_payload: dict[str, Any],
    generated_files: list[dict[str, str]],
) -> None:
    source_signature_path = reproducibility_path(current_package_root, "source_signature")
    dump_json(
        source_signature_path,
        build_source_signature_document(
            source_signature=str(source_signature_payload.get("source_signature") or ""),
            source_contract=dict(source_signature_payload.get("source_contract") or {}),
            package_role="human_facing_mirror",
        ),
    )
    _append_generated_file(
        generated_files,
        category="current_package_reproducibility",
        path=source_signature_path,
    )

    source_paths_path = reproducibility_path(current_package_root, "source_relative_paths")
    dump_json(
        source_paths_path,
        build_source_relative_paths_document(
            source_relative_paths=source_signature_payload.get("source_paths") or [],
            source_files=source_signature_payload.get("source_files") or [],
            package_role="human_facing_mirror",
        ),
    )
    _append_generated_file(
        generated_files,
        category="current_package_reproducibility",
        path=source_paths_path,
    )

    analysis_manifest_path = reproducibility_path(current_package_root, "analysis_manifest")
    dump_json(
        analysis_manifest_path,
        build_analysis_manifest_document(
            analysis_manifest_source=None,
            analysis_manifest_present=False,
            package_role="human_facing_mirror",
        ),
    )
    _append_generated_file(
        generated_files,
        category="current_package_reproducibility",
        path=analysis_manifest_path,
    )


def sync_current_package_projection(
    *,
    paper_root: Path | None,
    source_root: Path,
    current_package_root: Path,
    current_package_zip: Path,
    projected_current_package_root: Path | None = None,
    study_id: str,
    stage: str,
    source_relative_root: str,
    status_line: str,
    copied_files: list[dict[str, str]],
    generated_files: list[dict[str, str]],
    review_ledger_source: Path | None = None,
    charter_contract_linkage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reset_directory(current_package_root)
    resolved_projected_current_package_root = (
        Path(projected_current_package_root).expanduser().resolve()
        if projected_current_package_root is not None
        else current_package_root.expanduser().resolve()
    )
    copy_tree(
        source_root=source_root,
        target_root=current_package_root,
        category="current_package",
        copied_files=copied_files,
        ignore_filenames=(
            "submission_manifest.json",
            "evidence_ledger.json",
        ),
    )
    linkage_payload, source_manifest_path = _copy_current_package_audit_surfaces(
        paper_root=paper_root,
        source_root=source_root,
        current_package_root=current_package_root,
        resolved_projected_current_package_root=resolved_projected_current_package_root,
        copied_files=copied_files,
        review_ledger_source=review_ledger_source,
        charter_contract_linkage=charter_contract_linkage,
    )

    readme_path = current_package_root / "README.md"
    write_text(
        readme_path,
        build_current_package_readme(
            study_id=study_id,
            stage=stage,
            source_relative_root=source_relative_root,
            status_line=status_line,
            charter_contract_linkage=linkage_payload,
        ),
    )
    _append_generated_file(generated_files, category="current_package", path=readme_path)
    readme_payload = {
        "authority": "controller_authorized_delivery_sync_apply_only",
        "controller_authorized": True,
        "readme_path": str((resolved_projected_current_package_root / "README.md").resolve()),
        "written": True,
        "sections": [
            "Submission files",
            "Audit and reproducibility",
            "Delivery status",
            "Next controller-authorized sync",
        ],
        "editable_source": False,
    }
    submission_todo = build_submission_todo_from_manifest(
        manifest_path=resolve_submission_manifest_path(current_package_root),
    )
    if submission_todo is not None:
        todo_path = current_package_root / "SUBMISSION_TODO.md"
        write_text(todo_path, submission_todo)
        _append_generated_file(
            generated_files,
            category="current_package_submission_todo",
            path=todo_path,
        )
    _write_current_package_reproducibility_documents(
        current_package_root=current_package_root,
        source_signature_payload=_source_signature_payload_from_manifest(source_manifest_path),
        generated_files=generated_files,
    )
    _build_zip_from_directory(source_root=current_package_root, output_path=current_package_zip)
    _append_generated_file(generated_files, category="current_package", path=current_package_zip)
    return readme_payload
