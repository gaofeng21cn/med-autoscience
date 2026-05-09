from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib import request

from pypdf import PdfReader

from med_autoscience.adapters.literature import pubmed as pubmed_adapter
from med_autoscience.controllers import workspace_literature as workspace_literature_controller
from med_autoscience.controllers import study_delivery_sync
from med_autoscience.literature_records import LiteratureRecord
from med_autoscience.display_pack_resolver import get_pack_id
from med_autoscience.publication_profiles import (
    FRONTIERS_FAMILY_HARVARD_PROFILE,
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    JACS_PROFILE,
    is_frontiers_family_harvard_profile,
    normalize_publication_profile,
)
from med_autoscience.runtime_protocol.paper_artifacts import (
    materialize_archived_reference_only_submission_surface_manifests,
    resolve_managed_submission_surface_roots,
)


from .export_renderers import export_docx, export_pdf
from .profile_config import (
    FRONTIERS_HARVARD_CSL_URL,
    FRONTIERS_KEYWORDS,
    FRONTIERS_TEMPLATE_ZIP_URL,
    STYLES_ROOT,
    SUBMISSION_FRONT_MATTER_FIELD_ALIASES,
    PublicationProfileConfig,
    default_acs_csl_path,
    default_ama_csl_path,
    default_frontiers_harvard_csl_path,
    default_frontiers_supplementary_template_docx_path,
    default_frontiers_template_docx_path,
    download_to_path,
    ensure_frontiers_harvard_csl_path,
    ensure_frontiers_word_templates,
    frontiers_cache_dir,
    resolve_override_path,
    resolve_publication_profile_config,
)



def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def count_bibtex_entries(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.lstrip().startswith("@"))


def bibtex_entry_keys(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"@\w+\s*\{\s*([^,\s]+)", text)
        if match.group(1).strip()
    }


def markdown_citation_keys(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"(?<![A-Za-z0-9_])@([A-Za-z0-9_:.#/-]+)", text)
        if match.group(1).strip()
    }


def relpath_from_workspace(path: Path, workspace_root: Path) -> str:
    return path.resolve().relative_to(workspace_root.resolve()).as_posix()


def workspace_root_from_paper_root(paper_root: Path) -> Path:
    return paper_root.resolve().parent


def _canonical_paper_relative_path(value: str | Path) -> str | None:
    parts = Path(str(value).strip()).parts
    paper_indexes = [index for index, part in enumerate(parts) if part == "paper"]
    if not paper_indexes:
        return None
    return Path(*parts[paper_indexes[-1] :]).as_posix()


def resolve_relpath(workspace_root: Path, value: str) -> Path:
    raw_value = str(value).strip()
    candidate_path = Path(raw_value).expanduser()
    if candidate_path.is_absolute():
        return candidate_path
    canonical_paper_relpath = _canonical_paper_relative_path(raw_value)
    if canonical_paper_relpath is not None:
        canonical_candidate = workspace_root / canonical_paper_relpath
        try:
            if canonical_candidate.exists():
                return canonical_candidate
        except OSError:
            pass
    return workspace_root / raw_value


def build_figure_basename(figure_id: str) -> str:
    if figure_id.startswith("SupplementaryFigure"):
        return figure_id
    if figure_id.startswith("Figure"):
        return figure_id
    if figure_id.startswith("FS"):
        return f"SupplementaryFigureS{figure_id[2:]}"
    if figure_id.startswith("F"):
        return f"Figure{figure_id[1:]}"
    return figure_id


def build_table_basename(table_id: str) -> str:
    if table_id.startswith("AppendixTable"):
        return table_id
    if table_id.startswith("Table"):
        return table_id
    if table_id.startswith("TA"):
        return f"AppendixTable{table_id[2:]}"
    if table_id.startswith("T"):
        return f"Table{table_id[1:]}"
    return table_id


def resolve_bundle_input_path(
    *,
    bundle_manifest: dict[str, Any],
    key: str,
    fallback: str | None = None,
) -> str:
    bundle_inputs = bundle_manifest.get("bundle_inputs") or {}
    value = bundle_inputs.get(key)
    if value:
        return str(value)
    if key == "compile_report_path" and bundle_manifest.get("compile_report_path"):
        return str(bundle_manifest["compile_report_path"])
    if fallback:
        return fallback
    raise KeyError(f"missing bundle input `{key}` in paper bundle manifest")


def resolve_compile_report_path(*, workspace_root: Path, paper_root: Path, bundle_manifest: dict[str, Any]) -> Path:
    candidates = [
        resolve_bundle_input_path(
            bundle_manifest=bundle_manifest,
            key="compile_report_path",
            fallback="",
        ),
        "paper/build/compile_report.json",
        "paper/compile_report.json",
        "paper/submission_minimal/compile_report.json",
        "build/compile_report.json",
        "compile_report.json",
        "submission_minimal/compile_report.json",
    ]
    first_candidate: Path | None = None
    seen: set[Path] = set()
    for candidate in candidates:
        if not candidate:
            continue
        candidate_path = resolve_relpath(workspace_root, candidate)
        try:
            resolved = candidate_path.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if first_candidate is None:
            first_candidate = resolved
        try:
            if resolved.exists():
                return resolved
        except OSError:
            continue
    if first_candidate is not None:
        return first_candidate
    return paper_root / "build" / "compile_report.json"


def _first_nonempty_string(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
    return None


def _path_is_within_any_root(path: Path, roots: tuple[Path, ...]) -> bool:
    resolved_path = path.resolve()
    for root in roots:
        try:
            resolved_path.relative_to(root.resolve())
        except ValueError:
            continue
        return True
    return False


def _candidate_values_include_root(
    *,
    workspace_root: Path,
    candidate_values: list[object],
    root: Path,
) -> bool:
    root_resolved = root.resolve()
    for candidate in candidate_values:
        if not isinstance(candidate, str):
            continue
        normalized = candidate.strip()
        if not normalized:
            continue
        try:
            resolve_relpath(workspace_root, normalized).resolve().relative_to(root_resolved)
        except ValueError:
            continue
        return True
    return False


def _resolve_compiled_surface_candidate(
    *,
    workspace_root: Path,
    candidate_values: list[object],
    excluded_roots: tuple[Path, ...],
    missing_error: str,
) -> Path:
    normalized_candidates = [
        str(value).strip()
        for value in candidate_values
        if isinstance(value, str) and str(value).strip()
    ]
    if not normalized_candidates:
        raise KeyError(missing_error)

    first_candidate: Path | None = None
    first_nonexcluded_candidate: Path | None = None
    for candidate in normalized_candidates:
        resolved_candidate = resolve_relpath(workspace_root, candidate)
        if first_candidate is None:
            first_candidate = resolved_candidate
        if _path_is_within_any_root(resolved_candidate, excluded_roots):
            continue
        if first_nonexcluded_candidate is None:
            first_nonexcluded_candidate = resolved_candidate
        if resolved_candidate.exists():
            return resolved_candidate

    if first_nonexcluded_candidate is not None:
        return first_nonexcluded_candidate
    assert first_candidate is not None
    return first_candidate


def resolve_compiled_markdown_path(
    *,
    workspace_root: Path,
    bundle_manifest: dict[str, Any],
    compile_report: dict[str, Any],
    excluded_roots: tuple[Path, ...] = (),
) -> Path:
    bundle_inputs = bundle_manifest.get("bundle_inputs") or {}
    return _resolve_compiled_surface_candidate(
        workspace_root=workspace_root,
        candidate_values=[
            bundle_inputs.get("compiled_markdown_path"),
            compile_report.get("source_markdown_path"),
            compile_report.get("source_markdown"),
            bundle_manifest.get("draft_path"),
        ],
        excluded_roots=excluded_roots,
        missing_error=(
            "submission export could not resolve compiled markdown from "
            "bundle_manifest.bundle_inputs.compiled_markdown_path, "
            "bundle_manifest.draft_path, compile_report.source_markdown_path, "
            "or compile_report.source_markdown"
        ),
    )


def resolve_compiled_pdf_path(
    *,
    workspace_root: Path,
    bundle_manifest: dict[str, Any],
    compile_report: dict[str, Any],
    excluded_roots: tuple[Path, ...] = (),
) -> Path:
    return _resolve_compiled_surface_candidate(
        workspace_root=workspace_root,
        candidate_values=[
            compile_report.get("output_pdf"),
            compile_report.get("pdf_path"),
            bundle_manifest.get("pdf_path"),
        ],
        excluded_roots=excluded_roots,
        missing_error=(
            "submission export could not resolve compiled pdf from "
            "compile_report.output_pdf, compile_report.pdf_path, or bundle_manifest.pdf_path"
        ),
    )


def resolve_submission_compiled_source_excluded_roots(
    *,
    paper_root: Path,
    workspace_root: Path,
    submission_root: Path,
    bundle_manifest: dict[str, Any],
    compile_report: dict[str, Any],
    exclude_live_submission_root_for_markdown_candidates: bool = False,
) -> tuple[Path, ...]:
    managed_submission_surface_roots = tuple(
        root.resolve()
        for root in resolve_managed_submission_surface_roots(paper_root)
        if root.resolve() != submission_root.resolve()
    )
    compiled_pdf_candidate_values = [
        compile_report.get("output_pdf"),
        compile_report.get("pdf_path"),
        bundle_manifest.get("pdf_path"),
    ]
    if exclude_live_submission_root_for_markdown_candidates:
        bundle_inputs = bundle_manifest.get("bundle_inputs") or {}
        compiled_surface_candidate_values = [
            bundle_inputs.get("compiled_markdown_path"),
            compile_report.get("source_markdown_path"),
            compile_report.get("source_markdown"),
            bundle_manifest.get("draft_path"),
            *compiled_pdf_candidate_values,
        ]
    else:
        compiled_surface_candidate_values = compiled_pdf_candidate_values
    exclude_live_submission_root = _candidate_values_include_root(
        workspace_root=workspace_root,
        candidate_values=compiled_surface_candidate_values,
        root=submission_root,
    )
    return managed_submission_surface_roots + (
        (submission_root.resolve(),) if exclude_live_submission_root else ()
    )


def copy_with_renamed_targets(
    *,
    workspace_root: Path,
    paper_root: Path,
    source_paths: list[str],
    output_dir: Path,
    basename: str,
) -> list[str]:
    output_relpaths: list[str] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for source_rel in source_paths:
        source_path = resolve_submission_source_path(
            workspace_root=workspace_root,
            paper_root=paper_root,
            candidate_path=source_rel,
        )
        if not source_path.exists():
            raise FileNotFoundError(f"missing submission asset: {source_path}")
        suffix = source_path.suffix
        target_path = output_dir / f"{basename}{suffix}"
        shutil.copy2(source_path, target_path)
        output_relpaths.append(relpath_from_workspace(target_path, workspace_root))
    return output_relpaths


def resolve_submission_source_path(
    *,
    workspace_root: Path,
    paper_root: Path,
    candidate_path: str,
) -> Path:
    normalized_candidate = str(candidate_path).strip()
    canonical_paper_relpath = _canonical_paper_relative_path(normalized_candidate)
    if canonical_paper_relpath is not None:
        canonical_candidate = (paper_root.parent / canonical_paper_relpath).resolve()
        if canonical_candidate.exists():
            return canonical_candidate
    return resolve_relpath(workspace_root, normalized_candidate).resolve()


def find_missing_source_paths(*, workspace_root: Path, paper_root: Path, source_paths: list[str]) -> list[Path]:
    missing: list[Path] = []
    for source_rel in source_paths:
        source_path = resolve_submission_source_path(
            workspace_root=workspace_root,
            paper_root=paper_root,
            candidate_path=source_rel,
        )
        if not source_path.exists():
            missing.append(source_path)
    return missing


def filter_existing_source_paths(*, workspace_root: Path, paper_root: Path, source_paths: list[str]) -> list[str]:
    existing: list[str] = []
    for source_rel in source_paths:
        source_path = resolve_submission_source_path(
            workspace_root=workspace_root,
            paper_root=paper_root,
            candidate_path=source_rel,
        )
        if source_path.exists():
            existing.append(source_rel)
    return existing


def resolve_figure_source_paths(entry: dict[str, Any]) -> list[str]:
    export_paths = entry.get("export_paths")
    if isinstance(export_paths, list):
        normalized = [str(item).strip() for item in export_paths if str(item).strip()]
        if normalized:
            return normalized
    canonical_paths = []
    for key in ("pdf_path", "png_path"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            canonical_paths.append(value.strip())
    if canonical_paths:
        return canonical_paths
    planned_exports = entry.get("planned_exports")
    if isinstance(planned_exports, list):
        normalized = [str(item).strip() for item in planned_exports if str(item).strip()]
        if normalized:
            return normalized
    return []


def resolve_table_source_paths(entry: dict[str, Any]) -> list[str]:
    asset_paths = entry.get("asset_paths")
    if isinstance(asset_paths, list):
        normalized = [str(item).strip() for item in asset_paths if str(item).strip()]
        if normalized:
            return normalized
    canonical_paths = []
    for key in ("csv_path", "markdown_path"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            canonical_paths.append(value.strip())
    if canonical_paths:
        return canonical_paths
    path_value = entry.get("path")
    if isinstance(path_value, str) and path_value.strip():
        return [path_value.strip()]
    return []


def collect_referenced_paper_surface_paths(
    *,
    figure_catalog: dict[str, Any],
    table_catalog: dict[str, Any],
) -> set[str]:
    referenced_paths: set[str] = set()
    for entry in figure_catalog.get("figures", []):
        if not isinstance(entry, dict):
            continue
        referenced_paths.update(resolve_figure_source_paths(entry))
    for entry in table_catalog.get("tables", []):
        if not isinstance(entry, dict):
            continue
        referenced_paths.update(resolve_table_source_paths(entry))
    return {path for path in referenced_paths if isinstance(path, str) and path.strip()}


def prune_legacy_paper_surface_exports(
    *,
    paper_root: Path,
    figure_catalog: dict[str, Any],
    table_catalog: dict[str, Any],
) -> list[str]:
    referenced_paths = collect_referenced_paper_surface_paths(
        figure_catalog=figure_catalog,
        table_catalog=table_catalog,
    )
    deleted_paths: list[str] = []
    patterns = (
        ("figures", "Figure*"),
        ("figures", "SupplementaryFigure*"),
        ("figures", "GA*"),
        ("tables", "Table*"),
        ("tables", "AppendixTable*"),
    )
    allowed_suffixes = {".png", ".pdf", ".svg", ".csv", ".md"}
    for directory_name, pattern in patterns:
        surface_root = paper_root / directory_name
        if not surface_root.exists():
            continue
        for candidate in sorted(surface_root.glob(pattern)):
            if not candidate.is_file() or candidate.suffix.lower() not in allowed_suffixes:
                continue
            relpath = f"paper/{candidate.relative_to(paper_root).as_posix()}"
            if relpath in referenced_paths:
                continue
            candidate.unlink()
            deleted_paths.append(relpath)
    return deleted_paths


def is_planned_catalog_entry(entry: dict[str, Any]) -> bool:
    status = str(entry.get("status") or "").strip().lower()
    return status.startswith("planned")


def _resolve_pack_id(entry: dict[str, Any], *, id_field: str) -> str | None:
    explicit_pack_id = str(entry.get("pack_id") or "").strip()
    if explicit_pack_id:
        return explicit_pack_id
    identifier = str(entry.get(id_field) or "").strip()
    if not identifier:
        return None
    try:
        return get_pack_id(identifier)
    except ValueError:
        return None


def _load_display_pack_lock_payload(*, paper_root: Path) -> tuple[Path, dict[str, Any]] | None:
    lock_path = paper_root / "build" / "display_pack_lock.json"
    if not lock_path.exists():
        return None
    payload = load_json(lock_path)
    if not isinstance(payload, dict):
        raise ValueError("display_pack_lock.json must contain an object")
    return lock_path, payload


def _build_display_pack_summary_by_id(
    lock_payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    enabled_packs = lock_payload.get("enabled_packs")
    if enabled_packs is None:
        return {}
    if not isinstance(enabled_packs, list):
        raise ValueError("display_pack_lock.json enabled_packs must be a list")

    summaries: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(enabled_packs):
        if not isinstance(item, dict):
            raise ValueError(f"display_pack_lock.json enabled_packs[{index}] must be an object")
        pack_id = str(item.get("pack_id") or "").strip()
        if not pack_id:
            raise ValueError(f"display_pack_lock.json enabled_packs[{index}] is missing pack_id")
        summary = {
            "pack_id": pack_id,
            "version": item.get("version"),
            "requested_version": item.get("requested_version"),
            "source_kind": item.get("source_kind"),
            "declared_in": item.get("declared_in"),
            "manifest_sha256": item.get("manifest_sha256"),
        }
        source_path = item.get("source_path")
        source_package = item.get("source_package")
        if source_path:
            summary["source_path"] = source_path
        if source_package:
            summary["source_package"] = source_package
        summaries[pack_id] = summary
    return summaries


def _attach_pack_provenance(
    entry: dict[str, Any],
    *,
    pack_id: str | None,
    pack_summary_by_id: dict[str, dict[str, Any]],
) -> None:
    if pack_id is None:
        return
    summary = pack_summary_by_id.get(pack_id)
    if summary is None:
        return
    entry["pack_version"] = summary.get("version")
    entry["pack_requested_version"] = summary.get("requested_version")
    entry["pack_source_kind"] = summary.get("source_kind")
    entry["pack_declared_in"] = summary.get("declared_in")
    entry["pack_manifest_sha256"] = summary.get("manifest_sha256")


def resolve_output_root(*, paper_root: Path, publication_profile: str) -> Path:
    normalized_profile = normalize_publication_profile(publication_profile)
    if normalized_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        return paper_root / "submission_minimal"
    return paper_root / "journal_submissions" / normalized_profile


def create_staging_output_root(*, target_root: Path) -> Path:
    target_root.parent.mkdir(parents=True, exist_ok=True)
    return Path(
        tempfile.mkdtemp(
            dir=target_root.parent,
            prefix=f".{target_root.name}.tmp-",
        )
    ).resolve()


def remap_staging_path_to_target(*, path: Path, staging_root: Path, target_root: Path) -> Path:
    resolved_path = path.expanduser().resolve()
    try:
        relative = resolved_path.relative_to(staging_root.expanduser().resolve())
    except ValueError:
        return resolved_path
    return (target_root.expanduser().resolve() / relative).resolve()


def remap_staging_relpath_to_target(*, relpath: str, workspace_root: Path, staging_root: Path, target_root: Path) -> str:
    return relpath_from_workspace(
        remap_staging_path_to_target(
            path=resolve_relpath(workspace_root, relpath),
            staging_root=staging_root,
            target_root=target_root,
        ),
        workspace_root,
    )


def replace_directory_atomically(*, staging_root: Path, target_root: Path) -> None:
    resolved_staging_root = staging_root.expanduser().resolve()
    resolved_target_root = target_root.expanduser().resolve()
    backup_root = resolved_target_root.parent / (
        f".{resolved_target_root.name}.bak-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    )
    replaced_existing_root = False
    try:
        if resolved_target_root.exists():
            resolved_target_root.replace(backup_root)
            replaced_existing_root = True
        resolved_staging_root.replace(resolved_target_root)
    except Exception:
        if resolved_target_root.exists():
            shutil.rmtree(resolved_target_root, ignore_errors=True)
        if replaced_existing_root and backup_root.exists():
            backup_root.replace(resolved_target_root)
        raise
    finally:
        if backup_root.exists():
            shutil.rmtree(backup_root, ignore_errors=True)


def build_submission_minimal_readme(*, publication_profile: str) -> str:
    normalized_profile = normalize_publication_profile(publication_profile)
    canonical_package_root = (
        "paper/submission_minimal/"
        if normalized_profile == GENERAL_MEDICAL_JOURNAL_PROFILE
        else f"paper/journal_submissions/{normalized_profile}/"
    )
    return (
        "# Canonical Submission Package\n\n"
        f"- Publication profile: `{normalized_profile}`\n"
        "- Canonical authority surface: `paper/`\n"
        "- Canonical rendered assets: `paper/figures/generated/` and `paper/tables/generated/`\n"
        f"- Canonical package root: `{canonical_package_root}`\n"
        "- Human-facing delivery mirror refreshed from this package: `manuscript/`\n"
        "- Auxiliary finalize/runtime evidence, when needed: `artifacts/`\n\n"
        "Use this directory as the fixed paper-owned submission-package lookup path. "
        "`manuscript/` is the only human-facing final-delivery mirror; `artifacts/` is reserved for auxiliary machine-generated evidence rather than duplicated figure/table lookup.\n"
    )






def split_front_matter(markdown_text: str) -> tuple[dict[str, str], str]:
    if not markdown_text.startswith("---\n"):
        return {}, markdown_text
    closing_marker = markdown_text.find("\n---\n", 4)
    if closing_marker == -1:
        return {}, markdown_text
    raw_front_matter = markdown_text[4:closing_marker]
    body = markdown_text[closing_marker + len("\n---\n") :]
    metadata: dict[str, str] = {}
    for raw_line in raw_front_matter.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, body


def build_front_matter_placeholders(*, metadata: dict[str, str]) -> dict[str, str]:
    placeholders: dict[str, str] = {}
    for field_name, aliases in SUBMISSION_FRONT_MATTER_FIELD_ALIASES.items():
        resolved_value = ""
        for alias in aliases:
            candidate = str(metadata.get(alias) or "").strip()
            if candidate:
                resolved_value = candidate
                break
        placeholders[field_name] = resolved_value or "pending"
    return placeholders


def materialize_submission_references(
    *,
    paper_root: Path,
    submission_root: Path,
    workspace_root: Path,
) -> dict[str, Any] | None:
    source_path, source_kind = resolve_submission_references_source(paper_root=paper_root)
    if source_path is None:
        return None
    target_path = submission_root / "references.bib"
    shutil.copy2(source_path, target_path)
    entry_count = count_bibtex_entries(source_path.read_text(encoding="utf-8"))
    return {
        "_source_abs_path": str(source_path.resolve()),
        "source_path": _path_label_from_workspace(path=source_path, workspace_root=workspace_root),
        "source_kind": source_kind,
        "output_path": relpath_from_workspace(target_path, workspace_root),
        "entry_count": entry_count,
    }


def _path_label_from_workspace(*, path: Path, workspace_root: Path) -> str:
    try:
        return relpath_from_workspace(path, workspace_root)
    except ValueError:
        return str(path.expanduser().resolve())


def resolve_submission_references_source(*, paper_root: Path) -> tuple[Path | None, str | None]:
    resolved_paper_root = paper_root.expanduser().resolve()
    paper_references = resolved_paper_root / "references.bib"
    if paper_references.exists():
        return paper_references, "paper_references"
    for ancestor in resolved_paper_root.parents:
        candidate = ancestor / "portfolio" / "research_memory" / "literature" / "references.bib"
        if candidate.exists():
            return candidate, "workspace_literature"
    return None, None


def validate_submission_references_coverage(
    *,
    source_markdown_path: Path,
    references_path: Path | None,
) -> dict[str, Any]:
    citation_keys = sorted(markdown_citation_keys(source_markdown_path.read_text(encoding="utf-8")))
    if not citation_keys:
        return {
            "status": "not_required",
            "citation_key_count": 0,
            "missing_citation_keys": [],
        }
    if references_path is None or not references_path.exists():
        raise FileNotFoundError(
            "missing submission references.bib for citation keys: " + ", ".join(citation_keys)
        )
    reference_keys = bibtex_entry_keys(references_path.read_text(encoding="utf-8"))
    missing = sorted(set(citation_keys) - reference_keys)
    if missing:
        raise ValueError("submission references.bib missing citation keys: " + ", ".join(missing))
    return {
        "status": "complete",
        "citation_key_count": len(citation_keys),
        "missing_citation_keys": [],
    }
