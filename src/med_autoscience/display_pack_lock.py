from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.display_pack_loader import (
    DisplayPackResolution,
    LoadedDisplayPack,
    load_enabled_local_display_pack_records,
    resolve_display_pack_selection,
)


def _relative_or_absolute(path: Path | None, *, repo_root: Path) -> str | None:
    if path is None:
        return None
    normalized = path.expanduser().resolve()
    try:
        return normalized.relative_to(repo_root).as_posix()
    except ValueError:
        return str(normalized)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _collect_pack_entry(
    record: LoadedDisplayPack,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    manifest_path = record.pack_root / "display_pack.toml"
    template_paths = sorted((record.pack_root / "templates").glob("*/template.toml"))
    return {
        "pack_id": record.pack_manifest.pack_id,
        "version": record.pack_manifest.version,
        "display_api_version": record.pack_manifest.display_api_version,
        "default_execution_mode": record.pack_manifest.default_execution_mode,
        "summary": record.pack_manifest.summary,
        "maintainer": record.pack_manifest.maintainer,
        "license": record.pack_manifest.license,
        "source": record.pack_manifest.source,
        "paper_family_coverage": list(record.pack_manifest.paper_family_coverage),
        "recommended_templates": list(record.pack_manifest.recommended_templates),
        "source_kind": record.source_config.kind,
        "source_path": record.source_config.path,
        "requested_version": record.source_config.version,
        "declared_in": record.source_config.declared_in,
        "config_path": _relative_or_absolute(record.source_config.config_path, repo_root=repo_root),
        "resolved_pack_root": _relative_or_absolute(record.pack_root, repo_root=repo_root),
        "manifest_path": _relative_or_absolute(manifest_path, repo_root=repo_root),
        "manifest_sha256": _sha256_file(manifest_path),
        "template_count": len(template_paths),
    }


def collect_enabled_pack_provenance(
    *,
    repo_root: Path,
    paper_root: Path | None = None,
) -> list[dict[str, Any]]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    return [
        _collect_pack_entry(record, repo_root=normalized_repo_root)
        for record in load_enabled_local_display_pack_records(
            normalized_repo_root,
            paper_root=paper_root,
        )
    ]


def build_display_pack_lock_payload(
    *,
    repo_root: Path,
    paper_root: Path | None = None,
) -> dict[str, Any]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    resolution: DisplayPackResolution = resolve_display_pack_selection(
        normalized_repo_root,
        paper_root=paper_root,
    )
    return {
        "schema_version": 2,
        "repo_config_path": _relative_or_absolute(resolution.repo_config_path, repo_root=normalized_repo_root),
        "paper_config_path": _relative_or_absolute(resolution.paper_config_path, repo_root=normalized_repo_root),
        "paper_config_present": resolution.paper_config_present,
        "inherit_repo_defaults": resolution.inherit_repo_defaults,
        "enabled_pack_ids": list(resolution.enabled_pack_ids),
        "enabled_packs": collect_enabled_pack_provenance(
            repo_root=normalized_repo_root,
            paper_root=paper_root,
        ),
    }


def write_display_pack_lock(*, paper_root: Path, repo_root: Path) -> Path:
    normalized_paper_root = Path(paper_root).expanduser().resolve()
    output_path = normalized_paper_root / "build" / "display_pack_lock.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_display_pack_lock_payload(
        repo_root=repo_root,
        paper_root=normalized_paper_root,
    )
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path
