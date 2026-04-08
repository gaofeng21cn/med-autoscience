from __future__ import annotations

from collections import defaultdict
import hashlib
import subprocess
import json
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

from med_autoscience.display_pack_loader import (
    DisplayPackResolution,
    LoadedDisplayPack,
    LoadedDisplayTemplate,
    load_enabled_local_display_pack_records,
    load_enabled_local_display_pack_template_records,
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


def _git_stdout(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or f"git command failed: {' '.join(args)}")
    return result.stdout.strip()


def _asset_directory_metadata(
    template_root: Path,
    *,
    repo_root: Path,
    directory_name: str,
) -> dict[str, Any]:
    directory_path = template_root / directory_name
    if not directory_path.is_dir():
        return {
            f"{directory_name}_dir": None,
            f"{directory_name}_file_count": 0,
        }
    file_count = sum(1 for item in directory_path.rglob("*") if item.is_file())
    return {
        f"{directory_name}_dir": _relative_or_absolute(directory_path, repo_root=repo_root),
        f"{directory_name}_file_count": file_count,
    }


def _collect_template_entry(
    record: LoadedDisplayTemplate,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    template_root = record.template_path.parent
    payload = {
        "template_id": record.template_manifest.template_id,
        "full_template_id": record.template_manifest.full_template_id,
        "kind": record.template_manifest.kind,
        "paper_proven": record.template_manifest.paper_proven,
        "template_manifest_path": _relative_or_absolute(record.template_path, repo_root=repo_root),
        "template_manifest_sha256": _sha256_file(record.template_path),
        "golden_case_paths": list(record.template_manifest.golden_case_paths),
        "exemplar_refs": list(record.template_manifest.exemplar_refs),
    }
    payload.update(_asset_directory_metadata(template_root, repo_root=repo_root, directory_name="examples"))
    payload.update(_asset_directory_metadata(template_root, repo_root=repo_root, directory_name="goldens"))
    payload.update(_asset_directory_metadata(template_root, repo_root=repo_root, directory_name="exemplars"))
    payload.update(_asset_directory_metadata(template_root, repo_root=repo_root, directory_name="audit"))
    return payload


def _collect_source_provenance(
    record: LoadedDisplayPack,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source_kind": record.source_config.kind,
        "source_path": record.source_config.path,
        "source_package": record.source_config.package,
        "pack_subdir": record.source_config.pack_subdir,
        "requested_version": record.source_config.version,
        "declared_in": record.source_config.declared_in,
        "config_path": _relative_or_absolute(record.source_config.config_path, repo_root=repo_root),
        "resolved_source_root": _relative_or_absolute(record.source_config.resolved_source_root, repo_root=repo_root),
        "resolved_pack_root": _relative_or_absolute(record.pack_root, repo_root=repo_root),
    }
    if record.source_config.kind == "git_repo":
        payload["git_commit"] = _git_stdout(record.source_config.resolved_source_root, "rev-parse", "HEAD")
        payload["git_is_dirty"] = bool(
            _git_stdout(record.source_config.resolved_source_root, "status", "--short")
        )
    elif record.source_config.kind == "python_package" and record.source_config.package is not None:
        distribution_names = importlib_metadata.packages_distributions().get(
            record.source_config.package,
            [],
        )
        payload["python_distribution_names"] = distribution_names
        payload["python_distribution_versions"] = {
            name: importlib_metadata.version(name)
            for name in distribution_names
        }
    return payload


def _collect_pack_entry(
    record: LoadedDisplayPack,
    *,
    repo_root: Path,
    template_records: list[LoadedDisplayTemplate],
) -> dict[str, Any]:
    manifest_path = record.pack_root / "display_pack.toml"
    payload = {
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
        "manifest_path": _relative_or_absolute(manifest_path, repo_root=repo_root),
        "manifest_sha256": _sha256_file(manifest_path),
        "template_count": len(template_records),
        "templates": [
            _collect_template_entry(template_record, repo_root=repo_root)
            for template_record in sorted(
                template_records,
                key=lambda item: item.template_manifest.full_template_id,
            )
        ],
    }
    payload.update(_collect_source_provenance(record, repo_root=repo_root))
    return payload


def collect_enabled_pack_provenance(
    *,
    repo_root: Path,
    paper_root: Path | None = None,
) -> list[dict[str, Any]]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    pack_records = load_enabled_local_display_pack_records(
        normalized_repo_root,
        paper_root=paper_root,
    )
    template_records = load_enabled_local_display_pack_template_records(
        normalized_repo_root,
        paper_root=paper_root,
    )
    templates_by_pack_key: dict[tuple[str, Path], list[LoadedDisplayTemplate]] = defaultdict(list)
    for template_record in template_records:
        templates_by_pack_key[
            (
                template_record.pack_manifest.pack_id,
                template_record.pack_root.resolve(),
            )
        ].append(template_record)
    return [
        _collect_pack_entry(
            record,
            repo_root=normalized_repo_root,
            template_records=templates_by_pack_key.get(
                (
                    record.pack_manifest.pack_id,
                    record.pack_root.resolve(),
                ),
                [],
            ),
        )
        for record in pack_records
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
