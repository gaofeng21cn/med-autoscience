from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .shared_base import (
    filter_existing_source_paths,
    relpath_from_workspace,
    resolve_figure_source_paths,
    resolve_submission_source_path,
    resolve_table_source_paths,
)


def _hash_file_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _source_contract_path_label(*, path: Path, workspace_root: Path) -> str:
    resolved = path.resolve()
    try:
        return relpath_from_workspace(resolved, workspace_root)
    except ValueError:
        return str(resolved)


def _append_source_contract_entry(
    *,
    entries_by_path: dict[str, dict[str, Any]],
    path: Path,
    workspace_root: Path,
) -> None:
    resolved = path.expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        return
    key = str(resolved)
    if key in entries_by_path:
        return
    stat = resolved.stat()
    entries_by_path[key] = {
        "path": _source_contract_path_label(path=resolved, workspace_root=workspace_root),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": _hash_file_bytes(resolved),
    }


def _source_signature_payload(source_files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "path": item["path"],
            "size": item["size"],
            "sha256": item["sha256"],
        }
        for item in source_files
    ]


def build_submission_minimal_source_contract(
    *,
    paper_root: Path,
    workspace_root: Path,
    compile_report_path: Path,
    compiled_markdown_path: Path,
    figure_catalog_path: Path,
    table_catalog_path: Path,
    figure_catalog: dict[str, Any],
    table_catalog: dict[str, Any],
    pack_lock_path: Path | None = None,
) -> dict[str, Any]:
    resolved_paper_root = paper_root.expanduser().resolve()
    resolved_workspace_root = workspace_root.expanduser().resolve()
    entries_by_path: dict[str, dict[str, Any]] = {}
    missing_source_paths: set[str] = set()

    def add_required(path: Path) -> None:
        resolved = path.expanduser().resolve()
        if not resolved.exists() or not resolved.is_file():
            missing_source_paths.add(_source_contract_path_label(path=resolved, workspace_root=resolved_workspace_root))
            return
        _append_source_contract_entry(
            entries_by_path=entries_by_path,
            path=resolved,
            workspace_root=resolved_workspace_root,
        )

    add_required(resolved_paper_root / "paper_bundle_manifest.json")
    add_required(compile_report_path)
    add_required(compiled_markdown_path)
    add_required(figure_catalog_path)
    add_required(table_catalog_path)

    references_path = resolved_paper_root / "references.bib"
    if references_path.exists():
        add_required(references_path)
    if pack_lock_path is not None and pack_lock_path.exists():
        add_required(pack_lock_path)
    for entry in figure_catalog.get("figures", []) or []:
        if not isinstance(entry, dict):
            continue
        source_paths = resolve_figure_source_paths(entry)
        existing_source_paths = filter_existing_source_paths(
            workspace_root=resolved_workspace_root,
            paper_root=resolved_paper_root,
            source_paths=source_paths,
        )
        if existing_source_paths:
            source_paths = existing_source_paths
        for source_rel in source_paths:
            source_path = resolve_submission_source_path(
                workspace_root=resolved_workspace_root,
                paper_root=resolved_paper_root,
                candidate_path=source_rel,
            )
            if not source_path.exists():
                missing_source_paths.add(source_rel)
                continue
            add_required(source_path)

    for entry in table_catalog.get("tables", []) or []:
        if not isinstance(entry, dict):
            continue
        for source_rel in resolve_table_source_paths(entry):
            source_path = resolve_submission_source_path(
                workspace_root=resolved_workspace_root,
                paper_root=resolved_paper_root,
                candidate_path=source_rel,
            )
            if not source_path.exists():
                missing_source_paths.add(source_rel)
                continue
            add_required(source_path)

    source_files = sorted(entries_by_path.values(), key=lambda item: str(item["path"]))
    source_signature = hashlib.sha256(
        json.dumps(_source_signature_payload(source_files), ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    latest_source_mtime_ns = max((int(item["mtime_ns"]) for item in source_files), default=0)
    return {
        "schema_version": 1,
        "source_files": source_files,
        "source_paths": [str(item["path"]) for item in source_files],
        "source_signature": source_signature,
        "latest_source_mtime_ns": latest_source_mtime_ns,
        "missing_source_paths": sorted(missing_source_paths),
    }
