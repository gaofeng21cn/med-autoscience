from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request

from pypdf import PdfReader

from med_autoscience.controllers import study_delivery_sync
from med_autoscience.display_pack_resolver import get_pack_id
from med_autoscience.publication_profiles import (
    FRONTIERS_FAMILY_HARVARD_PROFILE,
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    is_frontiers_family_harvard_profile,
    normalize_publication_profile,
)
from med_autoscience.runtime_protocol.paper_artifacts import (
    materialize_archived_reference_only_submission_surface_manifests,
    resolve_managed_submission_surface_roots,
)


STYLES_ROOT = Path(__file__).resolve().parents[1] / "styles"
FRONTIERS_TEMPLATE_ZIP_URL = "https://www.frontiersin.org/Design/zip/Frontiers_Word_Templates.zip"
FRONTIERS_HARVARD_CSL_URL = "https://raw.githubusercontent.com/citation-style-language/styles/master/frontiers.csl"
FRONTIERS_KEYWORDS = [
    "NF-PitNET",
    "pituitary neuroendocrine tumor",
    "residual disease",
    "non-gross-total resection",
    "risk stratification",
    "pituitary surgery",
]
SUBMISSION_FRONT_MATTER_FIELD_ALIASES = {
    "authors": ("authors", "author"),
    "affiliations": ("affiliations",),
    "corresponding_author": ("corresponding_author", "correspondence"),
    "funding": ("funding",),
    "conflict_of_interest": ("conflict_of_interest", "conflicts_of_interest"),
    "ethics": ("ethics", "ethics_statement"),
    "data_availability": ("data_availability", "data_availability_statement"),
}


@dataclass(frozen=True)
class PublicationProfileConfig:
    publication_profile: str
    citation_style: str
    csl_path: Path
    output_dir_rel: Path
    reference_doc_path: Path | None = None
    supplementary_reference_doc_path: Path | None = None
    supplementary_docx_name: str | None = None
    journal_name: str | None = None
    journal_family: str | None = None
    reference_style_family: str | None = None


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


def relpath_from_workspace(path: Path, workspace_root: Path) -> str:
    return path.resolve().relative_to(workspace_root.resolve()).as_posix()


def workspace_root_from_paper_root(paper_root: Path) -> Path:
    return paper_root.resolve().parent


def resolve_relpath(workspace_root: Path, value: str) -> Path:
    return workspace_root / value


def default_ama_csl_path() -> Path:
    return STYLES_ROOT / "american-medical-association.csl"


def default_frontiers_harvard_csl_path() -> Path:
    return STYLES_ROOT / "frontiers.csl"


def frontiers_cache_dir() -> Path:
    xdg_cache = os.getenv("XDG_CACHE_HOME", "").strip()
    if xdg_cache:
        return Path(xdg_cache).expanduser() / "med-autoscience" / "frontiers_word_templates"
    return Path.home() / ".cache" / "med-autoscience" / "frontiers_word_templates"


def default_frontiers_template_docx_path() -> Path:
    return frontiers_cache_dir() / "Frontiers_Template.docx"


def default_frontiers_supplementary_template_docx_path() -> Path:
    return frontiers_cache_dir() / "Supplementary_Material.docx"


def _canonical_paper_relative_path(value: str | Path) -> str | None:
    parts = Path(str(value).strip()).parts
    paper_indexes = [index for index, part in enumerate(parts) if part == "paper"]
    if not paper_indexes:
        return None
    return Path(*parts[paper_indexes[-1] :]).as_posix()


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


def resolve_override_path(env_name: str) -> Path | None:
    value = os.getenv(env_name, "").strip()
    if not value:
        return None
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"missing override resource for {env_name}: {path}")
    return path


def download_to_path(*, url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with request.urlopen(url) as response:  # noqa: S310
        output_path.write_bytes(response.read())
    return output_path


def ensure_frontiers_word_templates() -> tuple[Path, Path]:
    manuscript_override = resolve_override_path("DEEPSCIENTIST_FRONTIERS_TEMPLATE_DOCX")
    supplementary_override = resolve_override_path("DEEPSCIENTIST_FRONTIERS_SUPPLEMENTARY_TEMPLATE_DOCX")
    manuscript_template = manuscript_override or default_frontiers_template_docx_path()
    supplementary_template = supplementary_override or default_frontiers_supplementary_template_docx_path()
    if manuscript_template.exists() and supplementary_template.exists():
        return manuscript_template, supplementary_template

    archive_path = frontiers_cache_dir() / "Frontiers_Word_Templates.zip"
    if not archive_path.exists():
        download_to_path(url=FRONTIERS_TEMPLATE_ZIP_URL, output_path=archive_path)

    with zipfile.ZipFile(archive_path) as archive:
        if not manuscript_template.exists():
            manuscript_template.write_bytes(archive.read("Frontiers_Word_Templates/Frontiers_Template.docx"))
        if not supplementary_template.exists():
            supplementary_template.write_bytes(
                archive.read("Frontiers_Word_Templates/Supplementary_Material.docx")
            )
    return manuscript_template, supplementary_template


def ensure_frontiers_harvard_csl_path() -> Path:
    override = resolve_override_path("DEEPSCIENTIST_FRONTIERS_CSL")
    if override is not None:
        return override
    csl_path = default_frontiers_harvard_csl_path()
    if csl_path.exists():
        return csl_path
    return download_to_path(url=FRONTIERS_HARVARD_CSL_URL, output_path=csl_path)


def resolve_publication_profile_config(
    *,
    publication_profile: str,
    citation_style: str | None,
) -> PublicationProfileConfig:
    normalized_publication_profile = normalize_publication_profile(publication_profile)
    normalized_citation_style = str(citation_style or "auto").strip()

    if normalized_publication_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        resolved_citation_style = "AMA" if normalized_citation_style in {"", "auto"} else normalized_citation_style
        if resolved_citation_style != "AMA":
            raise ValueError(
                f"unsupported citation style for {normalized_publication_profile}: {resolved_citation_style}"
            )
        csl_path = default_ama_csl_path()
        if not csl_path.exists():
            raise FileNotFoundError(f"missing AMA CSL file: {csl_path}")
        return PublicationProfileConfig(
            publication_profile=normalized_publication_profile,
            citation_style=resolved_citation_style,
            csl_path=csl_path,
            output_dir_rel=Path("submission_minimal"),
        )

    if normalized_publication_profile == FRONTIERS_FAMILY_HARVARD_PROFILE:
        resolved_citation_style = (
            "FrontiersHarvard" if normalized_citation_style in {"", "auto"} else normalized_citation_style
        )
        if resolved_citation_style != "FrontiersHarvard":
            raise ValueError(
                f"unsupported citation style for {normalized_publication_profile}: {resolved_citation_style}"
            )
        manuscript_template, supplementary_template = ensure_frontiers_word_templates()
        return PublicationProfileConfig(
            publication_profile=normalized_publication_profile,
            citation_style=resolved_citation_style,
            csl_path=ensure_frontiers_harvard_csl_path(),
            output_dir_rel=Path("journal_submissions") / normalized_publication_profile,
            reference_doc_path=manuscript_template,
            supplementary_reference_doc_path=supplementary_template,
            supplementary_docx_name="Supplementary_Material.docx",
            journal_family="Frontiers",
            reference_style_family="FrontiersHarvard",
        )

    raise ValueError(f"unsupported publication profile: {publication_profile}")


def export_docx(
    *,
    compiled_markdown_path: Path,
    paper_root: Path,
    output_docx_path: Path,
    csl_path: Path,
    reference_doc_path: Path | None = None,
) -> None:
    output_docx_path.parent.mkdir(parents=True, exist_ok=True)
    resource_candidates = [
        ".",
        os.path.relpath(paper_root.resolve(), compiled_markdown_path.parent.resolve()),
    ]
    resource_path = os.pathsep.join(dict.fromkeys(resource_candidates))
    command = [
        "pandoc",
        compiled_markdown_path.name,
        "--standalone",
        "--citeproc",
        "--csl",
        str(csl_path.resolve()),
        "--resource-path",
        resource_path,
    ]
    if reference_doc_path is not None:
        command.extend(["--reference-doc", str(reference_doc_path.resolve())])
    command.extend(
        [
            "-o",
            os.path.relpath(output_docx_path.resolve(), compiled_markdown_path.parent.resolve()),
        ]
    )
    subprocess.run(
        command,
        cwd=compiled_markdown_path.parent,
        check=True,
    )


def export_pdf(
    *,
    compiled_markdown_path: Path,
    paper_root: Path,
    output_pdf_path: Path,
    csl_path: Path,
) -> None:
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    resource_candidates = [
        ".",
        os.path.relpath(paper_root.resolve(), compiled_markdown_path.parent.resolve()),
    ]
    resource_path = os.pathsep.join(dict.fromkeys(resource_candidates))
    subprocess.run(
        [
            "pandoc",
            compiled_markdown_path.name,
            "--standalone",
            "--citeproc",
            "--csl",
            str(csl_path.resolve()),
            "--resource-path",
            resource_path,
            "--pdf-engine=xelatex",
            "-o",
            os.path.relpath(output_pdf_path.resolve(), compiled_markdown_path.parent.resolve()),
        ],
        cwd=compiled_markdown_path.parent,
        check=True,
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
    source_path = paper_root / "references.bib"
    if not source_path.exists():
        return None
    target_path = submission_root / "references.bib"
    shutil.copy2(source_path, target_path)
    entry_count = count_bibtex_entries(source_path.read_text(encoding="utf-8"))
    return {
        "source_path": relpath_from_workspace(source_path, workspace_root),
        "output_path": relpath_from_workspace(target_path, workspace_root),
        "entry_count": entry_count,
    }


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
    for relative_path in study_delivery_sync.FORMAL_PAPER_DELIVERY_RELATIVE_PATHS:
        source_path = resolved_paper_root / relative_path
        if source_path.exists():
            add_required(source_path)

    for entry in figure_catalog.get("figures", []) or []:
        if not isinstance(entry, dict):
            continue
        for source_rel in resolve_figure_source_paths(entry):
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


def describe_submission_minimal_authority(
    *,
    paper_root: Path,
    publication_profile: str = GENERAL_MEDICAL_JOURNAL_PROFILE,
) -> dict[str, Any]:
    resolved_paper_root = paper_root.expanduser().resolve()
    workspace_root = workspace_root_from_paper_root(resolved_paper_root)
    normalized_publication_profile = normalize_publication_profile(publication_profile)
    submission_root = resolve_output_root(
        paper_root=resolved_paper_root,
        publication_profile=normalized_publication_profile,
    )
    submission_manifest_path = submission_root / "submission_manifest.json"
    if not submission_manifest_path.exists():
        return {
            "applicable": True,
            "status": "missing",
            "stale_reason": "submission_manifest_missing",
            "submission_root": str(submission_root),
            "submission_manifest_path": None,
            "source_signature": None,
            "recorded_source_signature": None,
            "missing_source_paths": [],
        }

    try:
        submission_manifest = load_json(submission_manifest_path)
    except json.JSONDecodeError:
        return {
            "applicable": True,
            "status": "invalid",
            "stale_reason": "submission_manifest_invalid",
            "submission_root": str(submission_root),
            "submission_manifest_path": str(submission_manifest_path),
            "source_signature": None,
            "recorded_source_signature": None,
            "missing_source_paths": [],
        }
    if not isinstance(submission_manifest, dict):
        return {
            "applicable": True,
            "status": "invalid",
            "stale_reason": "submission_manifest_invalid",
            "submission_root": str(submission_root),
            "submission_manifest_path": str(submission_manifest_path),
            "source_signature": None,
            "recorded_source_signature": None,
            "missing_source_paths": [],
        }

    bundle_manifest_path = resolved_paper_root / "paper_bundle_manifest.json"
    try:
        bundle_manifest = load_json(bundle_manifest_path)
        compile_report_path = resolve_relpath(
            workspace_root,
            resolve_bundle_input_path(
                bundle_manifest=bundle_manifest,
                key="compile_report_path",
            ),
        )
        figure_catalog_path = resolve_relpath(
            workspace_root,
            resolve_bundle_input_path(
                bundle_manifest=bundle_manifest,
                key="figure_catalog_path",
                fallback="paper/figures/figure_catalog.json",
            ),
        )
        table_catalog_path = resolve_relpath(
            workspace_root,
            resolve_bundle_input_path(
                bundle_manifest=bundle_manifest,
                key="table_catalog_path",
                fallback="paper/tables/table_catalog.json",
            ),
        )
        compile_report = load_json(compile_report_path)
        figure_catalog = load_json(figure_catalog_path)
        table_catalog = load_json(table_catalog_path)
        excluded_compiled_source_roots = resolve_submission_compiled_source_excluded_roots(
            paper_root=resolved_paper_root,
            workspace_root=workspace_root,
            submission_root=submission_root,
            bundle_manifest=bundle_manifest,
            compile_report=compile_report,
        )
        compiled_markdown_path = resolve_compiled_markdown_path(
            workspace_root=workspace_root,
            bundle_manifest=bundle_manifest,
            compile_report=compile_report,
            excluded_roots=excluded_compiled_source_roots,
        )
        pack_lock_payload = _load_display_pack_lock_payload(paper_root=resolved_paper_root)
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return {
            "applicable": True,
            "status": "stale_source_missing",
            "stale_reason": "submission_source_inputs_missing",
            "submission_root": str(submission_root),
            "submission_manifest_path": str(submission_manifest_path),
            "source_signature": None,
            "recorded_source_signature": None,
            "missing_source_paths": [],
        }

    source_contract = build_submission_minimal_source_contract(
        paper_root=resolved_paper_root,
        workspace_root=workspace_root,
        compile_report_path=compile_report_path,
        compiled_markdown_path=compiled_markdown_path,
        figure_catalog_path=figure_catalog_path,
        table_catalog_path=table_catalog_path,
        figure_catalog=figure_catalog if isinstance(figure_catalog, dict) else {},
        table_catalog=table_catalog if isinstance(table_catalog, dict) else {},
        pack_lock_path=pack_lock_payload[0] if pack_lock_payload is not None else None,
    )
    recorded_contract = (
        dict(submission_manifest.get("source_contract") or {})
        if isinstance(submission_manifest.get("source_contract"), dict)
        else {}
    )
    recorded_source_signature = _first_nonempty_string(
        submission_manifest.get("source_signature"),
        recorded_contract.get("source_signature"),
    )
    if source_contract["missing_source_paths"]:
        status = "stale_source_missing"
        stale_reason = "submission_source_inputs_missing"
    elif recorded_source_signature:
        status = "current" if recorded_source_signature == source_contract["source_signature"] else "stale_source_changed"
        stale_reason = None if status == "current" else "submission_source_signature_mismatch"
    else:
        manifest_mtime_ns = submission_manifest_path.stat().st_mtime_ns
        status = (
            "current"
            if manifest_mtime_ns >= int(source_contract["latest_source_mtime_ns"])
            else "stale_source_changed"
        )
        stale_reason = None if status == "current" else "submission_source_newer_than_manifest"
    return {
        "applicable": True,
        "status": status,
        "stale_reason": stale_reason,
        "submission_root": str(submission_root),
        "submission_manifest_path": str(submission_manifest_path),
        "source_signature": source_contract["source_signature"],
        "recorded_source_signature": recorded_source_signature,
        "missing_source_paths": list(source_contract["missing_source_paths"]),
        "latest_source_mtime_ns": int(source_contract["latest_source_mtime_ns"]),
    }


def extract_block_between_markers(
    text: str,
    *,
    start_marker: str,
    end_markers: list[str],
    label: str,
) -> str:
    start_index = text.find(start_marker)
    if start_index == -1:
        raise ValueError(f"missing section `{label}` in compiled manuscript")
    content_start = start_index + len(start_marker)
    content_end = len(text)
    for marker in end_markers:
        marker_index = text.find(marker, content_start)
        if marker_index != -1:
            content_end = min(content_end, marker_index)
    return text[content_start:content_end].strip()


def extract_markdown_block(body: str, start_heading: str, end_headings: list[str]) -> str:
    return extract_block_between_markers(
        body,
        start_marker=f"# {start_heading}\n",
        end_markers=[f"\n# {heading}\n" for heading in end_headings],
        label=start_heading,
    )


def extract_optional_block_between_markers(
    text: str,
    *,
    start_marker: str,
    end_markers: list[str],
    label: str,
) -> str:
    try:
        return extract_block_between_markers(
            text,
            start_marker=start_marker,
            end_markers=end_markers,
            label=label,
        )
    except ValueError:
        return ""


def extract_optional_markdown_block(body: str, start_heading: str, end_headings: list[str]) -> str:
    try:
        return extract_markdown_block(body, start_heading, end_headings)
    except ValueError:
        return ""


def build_frontiers_required_sections() -> str:
    return (
        "# Data Availability Statement\n\n"
        "Patient-level clinical data were analyzed in this study. Because the source dataset was derived from hospital "
        "records, public deposition may be restricted by institutional and privacy requirements. "
        "[Please replace this sentence with the authors' approved data-availability statement before submission.]\n\n"
        "# Ethics Statement\n\n"
        "This study was approved by the Clinical Research Ethics Committee of the First Affiliated Hospital of "
        "Sun Yat-sen University (approval `[2024]576`). "
        "[Please add the exact informed-consent or consent-waiver wording approved by the ethics committee before submission.]\n\n"
        "# Author Contributions\n\n"
        "[To be completed before submission.]\n\n"
        "# Funding\n\n"
        "[To be completed before submission.]\n\n"
        "# Acknowledgments\n\n"
        "[Optional; complete if applicable before submission.]\n\n"
        "# Conflict of Interest\n\n"
        "The authors declare that the research was conducted in the absence of any commercial or financial "
        "relationships that could be construed as a potential conflict of interest. "
        "[Revise this statement if any competing interests apply.]\n"
    )


def parse_heading_blocks(text: str, heading_prefix: str) -> list[tuple[str, str]]:
    pattern = re.compile(rf"(?ms)^## ({re.escape(heading_prefix)}[^\n]*)\n\n(.*?)(?=^## |\Z)")
    blocks: list[tuple[str, str]] = []
    for match in pattern.finditer(text.strip()):
        heading = match.group(1).strip()
        body = match.group(2).strip()
        blocks.append((heading, body))
    return blocks


def parse_top_level_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(?ms)^# ([^\n]+)\n\n(.*?)(?=^# |\Z)")
    blocks: list[tuple[str, str]] = []
    for match in pattern.finditer(text.strip()):
        heading = match.group(1).strip()
        body = match.group(2).strip()
        blocks.append((heading, body))
    return blocks


def normalize_markdown_heading_key(heading: str) -> str:
    return re.sub(r"\s+", " ", str(heading or "").strip()).casefold()


def extract_top_level_markdown_block(body: str, *headings: str) -> str:
    heading_keys = {normalize_markdown_heading_key(heading) for heading in headings}
    for heading, block_body in parse_top_level_blocks(body):
        if normalize_markdown_heading_key(heading) in heading_keys:
            return block_body.strip()
    return ""


def parse_second_level_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(?ms)^## ([^\n]+)\n\n(.*?)(?=^## |\Z)")
    blocks: list[tuple[str, str]] = []
    for match in pattern.finditer(text.strip()):
        heading = match.group(1).strip()
        body = match.group(2).strip()
        blocks.append((heading, body))
    return blocks


def parse_third_level_blocks(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(?ms)^### ([^\n]+)\n\n(.*?)(?=^### |\Z)")
    blocks: list[tuple[str, str]] = []
    for match in pattern.finditer(text.strip()):
        heading = match.group(1).strip()
        body = match.group(2).strip()
        blocks.append((heading, body))
    return blocks


def parse_manuscript_shaped_draft(text: str) -> tuple[str | None, dict[str, str]]:
    stripped = text.strip()
    title_match = re.match(r"(?ms)^# ([^\n]+)\n+(.*)$", stripped)
    if title_match is None:
        return None, {}
    title = title_match.group(1).strip()
    if not title or title.lower() == "draft":
        return None, {}
    body = title_match.group(2).strip()
    blocks = {heading: block_body for heading, block_body in parse_second_level_blocks(body)}
    return title, blocks


def first_nonempty_block(section_blocks: dict[str, str], *headings: str) -> str:
    for heading in headings:
        value = section_blocks.get(heading, "")
        if value.strip():
            return value.strip()
    return ""


def parse_figure_id_from_heading(heading: str) -> str | None:
    supplementary_match = re.match(r"^Supplementary Figure S(\d+)\b", heading.strip(), flags=re.IGNORECASE)
    if supplementary_match:
        return f"FS{supplementary_match.group(1)}"
    supplementary_short_match = re.match(r"^FS(\d+)\b", heading.strip(), flags=re.IGNORECASE)
    if supplementary_short_match:
        return f"FS{supplementary_short_match.group(1)}"
    main_match = re.match(r"^Figure (\d+)\b", heading.strip(), flags=re.IGNORECASE)
    if main_match:
        return f"F{main_match.group(1)}"
    main_short_match = re.match(r"^F(\d+)\b", heading.strip(), flags=re.IGNORECASE)
    if main_short_match:
        return f"F{main_short_match.group(1)}"
    return None


def normalize_materialized_figure_heading(heading: str) -> str | None:
    normalized = heading.strip()
    if not normalized:
        return None
    if re.match(r"^Figure \d+\b", normalized, flags=re.IGNORECASE):
        return normalized
    if re.match(r"^Supplementary Figure S\d+\b", normalized, flags=re.IGNORECASE):
        return normalized

    supplementary_match = re.match(r"^FS(\d+)(?:\.\s*(.+))?$", normalized, flags=re.IGNORECASE)
    if supplementary_match:
        suffix = f". {supplementary_match.group(2).strip()}" if supplementary_match.group(2) else ""
        return f"Supplementary Figure S{supplementary_match.group(1)}{suffix}"

    main_match = re.match(r"^F(\d+)(?:\.\s*(.+))?$", normalized, flags=re.IGNORECASE)
    if main_match:
        suffix = f". {main_match.group(2).strip()}" if main_match.group(2) else ""
        return f"Figure {main_match.group(1)}{suffix}"
    return None


def extract_main_figure_blocks(main_figures: str) -> list[tuple[str, str]]:
    figure_blocks = parse_figure_blocks(main_figures)
    if figure_blocks:
        return figure_blocks

    normalized_blocks: list[tuple[str, str]] = []
    for heading, block_body in parse_third_level_blocks(main_figures):
        normalized_heading = normalize_materialized_figure_heading(heading)
        if normalized_heading and normalized_heading.lower().startswith("figure "):
            normalized_blocks.append((normalized_heading, block_body))
    return normalized_blocks


def parse_figure_blocks(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for heading, body in parse_second_level_blocks(text):
        if parse_figure_id_from_heading(heading):
            blocks.append((heading, body))
    return blocks


def normalize_submission_figure_heading(heading: str) -> str:
    normalized_heading = str(heading or "").strip()
    if not normalized_heading:
        return normalized_heading
    supplementary_short_match = re.match(r"^FS(\d+)(\b.*)$", normalized_heading, flags=re.IGNORECASE)
    if supplementary_short_match:
        return f"Supplementary Figure S{supplementary_short_match.group(1)}{supplementary_short_match.group(2)}"
    main_short_match = re.match(r"^F(\d+)(\b.*)$", normalized_heading, flags=re.IGNORECASE)
    if main_short_match:
        return f"Figure {main_short_match.group(1)}{main_short_match.group(2)}"
    return normalized_heading


def figure_id_aliases(figure_id: str) -> set[str]:
    normalized = str(figure_id or "").strip()
    if not normalized:
        return set()
    aliases = {normalized}
    supplementary_match = re.match(r"^SupplementaryFigureS(\d+)$", normalized, flags=re.IGNORECASE)
    if supplementary_match:
        aliases.add(f"FS{supplementary_match.group(1)}")
        return aliases
    supplementary_short_match = re.match(r"^FS(\d+)$", normalized, flags=re.IGNORECASE)
    if supplementary_short_match:
        aliases.add(f"SupplementaryFigureS{supplementary_short_match.group(1)}")
        return aliases
    main_match = re.match(r"^Figure(\d+)$", normalized, flags=re.IGNORECASE)
    if main_match:
        aliases.add(f"F{main_match.group(1)}")
        return aliases
    main_short_match = re.match(r"^F(\d+)$", normalized, flags=re.IGNORECASE)
    if main_short_match:
        aliases.add(f"Figure{main_short_match.group(1)}")
    return aliases


def load_figure_semantics_map(paper_root: Path) -> dict[str, dict[str, Any]]:
    path = paper_root / "figure_semantics_manifest.json"
    payload = load_json(path) if path.exists() else {}
    figures = payload.get("figures") if isinstance(payload, dict) else None
    if not isinstance(figures, list):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for item in figures:
        if not isinstance(item, dict):
            continue
        figure_id = str(item.get("figure_id") or "").strip()
        for alias in figure_id_aliases(figure_id):
            normalized[alias] = item
    return normalized


def _build_catalog_figure_heading(*, figure_id: str, title: str) -> str:
    normalized_id = str(figure_id or "").strip()
    normalized_title = str(title or "").strip()
    match = re.match(r"^F(\d+)$", normalized_id, flags=re.IGNORECASE)
    if match:
        heading = f"Figure {match.group(1)}"
        if normalized_title:
            return f"{heading}. {normalized_title}"
        return heading
    if normalized_title:
        return normalized_title
    return normalized_id


def _select_submission_markdown_figure_source(entry: dict[str, Any]) -> str:
    source_paths = resolve_figure_source_paths(entry)
    if not source_paths:
        return ""
    preferred_suffixes = (".png", ".jpg", ".jpeg", ".webp", ".svg", ".pdf")
    normalized_paths = [str(item).strip() for item in source_paths if str(item).strip()]
    for suffix in preferred_suffixes:
        for candidate in normalized_paths:
            if candidate.lower().endswith(suffix):
                return candidate
    return normalized_paths[0] if normalized_paths else ""


def build_catalog_backed_main_figures(*, paper_root: Path, submission_root: Path) -> str:
    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    if not figure_catalog_path.exists():
        return ""
    payload = load_json(figure_catalog_path)
    figures = payload.get("figures") if isinstance(payload, dict) else None
    if not isinstance(figures, list):
        return ""

    workspace_root = paper_root.parent
    figure_blocks: list[str] = []
    for entry in figures:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("paper_role") or "").strip().lower() != "main_text":
            continue
        figure_id = str(entry.get("figure_id") or "").strip()
        image_source_rel = _select_submission_markdown_figure_source(entry)
        if not figure_id or not image_source_rel:
            continue
        image_source_path = resolve_relpath(workspace_root, image_source_rel)
        if not image_source_path.exists():
            continue
        image_rel = os.path.relpath(image_source_path.resolve(), submission_root.resolve())
        heading = _build_catalog_figure_heading(
            figure_id=figure_id,
            title=str(entry.get("title") or ""),
        )
        legend = str(entry.get("caption") or "").strip()
        block_parts: list[str] = []
        if legend:
            block_parts.append(legend)
        block_parts.append(f"![]({image_rel})")
        figure_blocks.append(f"## {heading}\n\n" + "\n\n".join(block_parts))
    return "\n\n".join(figure_blocks).strip()


def build_catalog_backed_submission_figure_image_map(*, paper_root: Path, submission_root: Path) -> dict[str, str]:
    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    if not figure_catalog_path.exists():
        return {}
    payload = load_json(figure_catalog_path)
    figures = payload.get("figures") if isinstance(payload, dict) else None
    if not isinstance(figures, list):
        return {}

    workspace_root = paper_root.parent
    image_map: dict[str, str] = {}
    for entry in figures:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("paper_role") or "").strip().lower() != "main_text":
            continue
        figure_id = str(entry.get("figure_id") or "").strip()
        image_source_rel = _select_submission_markdown_figure_source(entry)
        if not figure_id or not image_source_rel:
            continue
        image_source_path = resolve_relpath(workspace_root, image_source_rel)
        if not image_source_path.exists():
            continue
        image_map[figure_id] = os.path.relpath(image_source_path.resolve(), submission_root.resolve())
    return image_map


def merge_legend_with_figure_semantics(*, base_legend: str, figure_semantics: dict[str, Any] | None) -> str:
    legend_parts = [base_legend.strip()] if base_legend.strip() else []
    if not figure_semantics:
        return "\n\n".join(legend_parts).strip()

    overall_sentences: list[str] = []
    panel_sentences: list[str] = []
    glossary_sentence = ""
    boundary_sentences: list[str] = []

    def normalize_sentence(value: str) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        if text[-1] not in ".!?":
            return f"{text}."
        return text

    def append_sentence(target: list[str], value: str) -> None:
        sentence = normalize_sentence(value)
        if sentence:
            target.append(sentence)

    append_sentence(overall_sentences, str(figure_semantics.get("direct_message") or ""))
    append_sentence(overall_sentences, str(figure_semantics.get("clinical_implication") or ""))
    append_sentence(overall_sentences, str(figure_semantics.get("interpretation_boundary") or ""))

    panel_messages = figure_semantics.get("panel_messages")
    if isinstance(panel_messages, list) and panel_messages:
        for panel in panel_messages:
            if not isinstance(panel, dict):
                continue
            panel_id = str(panel.get("panel_id") or "").strip()
            message = str(panel.get("message") or "").strip()
            if panel_id and message:
                if re.match(rf"(?i)^panel\s+{re.escape(panel_id)}\b", message):
                    panel_sentences.append(normalize_sentence(message))
                else:
                    panel_sentences.append(normalize_sentence(f"Panel {panel_id}: {message}"))

    legend_glossary = figure_semantics.get("legend_glossary")
    if isinstance(legend_glossary, list) and legend_glossary:
        glossary_parts: list[str] = []
        for item in legend_glossary:
            if not isinstance(item, dict):
                continue
            term = str(item.get("term") or "").strip()
            explanation = str(item.get("explanation") or "").strip().rstrip(".; ")
            if term and explanation:
                glossary_parts.append(f"{term}, {explanation}")
        if glossary_parts:
            glossary_sentence = normalize_sentence(f"Abbreviations: {'; '.join(glossary_parts)}")

    append_sentence(boundary_sentences, str(figure_semantics.get("threshold_semantics") or ""))
    append_sentence(boundary_sentences, str(figure_semantics.get("stratification_basis") or ""))
    append_sentence(boundary_sentences, str(figure_semantics.get("recommendation_boundary") or ""))

    existing_legend = " ".join(legend_parts)
    prose_blocks = [
        " ".join(sentence for sentence in overall_sentences if sentence),
        " ".join(sentence for sentence in panel_sentences if sentence),
        " ".join(
            sentence
            for sentence in [glossary_sentence, *boundary_sentences]
            if sentence
        ),
    ]
    deduped_semantic_lines = [block for block in prose_blocks if block and block not in existing_legend]
    if deduped_semantic_lines:
        legend_parts.extend(deduped_semantic_lines)
    return "\n\n".join(part for part in legend_parts if part).strip()


def build_figure_legend_blocks(
    *,
    main_figures: str,
    figure_semantics_map: dict[str, dict[str, Any]],
) -> list[str]:
    figure_legend_blocks: list[str] = []
    for heading, block_body in extract_main_figure_blocks(main_figures):
        figure_id = parse_figure_id_from_heading(heading)
        legend = merge_legend_with_figure_semantics(
            base_legend=strip_image_lines(block_body),
            figure_semantics=figure_semantics_map.get(figure_id or ""),
        )
        if legend:
            normalized_heading = normalize_submission_figure_heading(heading)
            figure_legend_blocks.append(f"## {normalized_heading}\n\n{legend}")
    return figure_legend_blocks


MARKDOWN_IMAGE_LINE_PATTERN = re.compile(r"^!\[[^\]]*]\([^)]+\)(?:\s*\{[^}]+\})?$")


def is_markdown_image_line(line: str) -> bool:
    return bool(MARKDOWN_IMAGE_LINE_PATTERN.match(line.strip()))


def extract_image_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if is_markdown_image_line(line)]


def rewrite_submission_surface_image_lines(*, image_lines: list[str], figure_id: str | None) -> list[str]:
    normalized_figure_id = str(figure_id or "").strip()
    if not normalized_figure_id:
        return image_lines

    figure_aliases = figure_id_aliases(normalized_figure_id)
    target_basename = build_figure_basename(normalized_figure_id)
    image_pattern = re.compile(r"(!\[[^\]]*]\()([^)]+)(\))")
    rewritten_lines: list[str] = []

    for line in image_lines:
        def replace(match: re.Match[str]) -> str:
            raw_path = match.group(2).strip()
            if raw_path.startswith(("http://", "https://", "/", "../")):
                return match.group(0)
            if "figures/" not in raw_path and not raw_path.startswith("figures"):
                return match.group(0)
            path_obj = Path(raw_path)
            if path_obj.stem not in figure_aliases:
                return match.group(0)
            rewritten_path = path_obj.with_name(f"{target_basename}{path_obj.suffix}").as_posix()
            return f"{match.group(1)}{rewritten_path}{match.group(3)}"

        rewritten_lines.append(image_pattern.sub(replace, line))
    return rewritten_lines


def build_submission_figure_blocks(
    *,
    main_figures: str,
    figure_semantics_map: dict[str, dict[str, Any]],
    catalog_image_map: dict[str, str] | None = None,
) -> list[str]:
    figure_blocks: list[str] = []
    resolved_catalog_image_map = catalog_image_map or {}
    for heading, block_body in extract_main_figure_blocks(main_figures):
        figure_id = parse_figure_id_from_heading(heading)
        image_lines = rewrite_submission_surface_image_lines(
            image_lines=extract_image_lines(block_body),
            figure_id=figure_id,
        )
        if not image_lines and figure_id:
            fallback_image_rel = resolved_catalog_image_map.get(figure_id)
            if fallback_image_rel:
                image_lines = [f"![]({fallback_image_rel})"]
        legend = merge_legend_with_figure_semantics(
            base_legend=strip_image_lines(block_body),
            figure_semantics=figure_semantics_map.get(figure_id or ""),
        )
        content_parts: list[str] = []
        if image_lines:
            content_parts.append("\n".join(image_lines))
        if legend:
            content_parts.append(legend)
        if content_parts:
            normalized_heading = normalize_submission_figure_heading(heading)
            figure_blocks.append(f"## {normalized_heading}\n\n{'\n\n'.join(content_parts)}")
    return figure_blocks


def build_table_blocks(*, main_tables: str) -> list[str]:
    table_blocks: list[str] = []
    for heading, block_body in parse_top_level_blocks(main_tables):
        table_blocks.append(f"## {heading}\n\n{block_body}")
    if not table_blocks and main_tables.strip():
        table_blocks.append(f"## Table 1\n\n{main_tables.strip()}")
    return table_blocks


def strip_image_lines(text: str) -> str:
    cleaned_lines = [line for line in text.splitlines() if not is_markdown_image_line(line)]
    return "\n".join(cleaned_lines).strip()


def rewrite_image_paths(*, markdown_text: str, source_markdown_dir: Path, target_markdown_dir: Path) -> str:
    image_pattern = re.compile(r"(!\[[^\]]*]\()([^)]+)(\))")

    def replace(match: re.Match[str]) -> str:
        image_path = match.group(2).strip()
        if image_path.startswith(("http://", "https://")) or os.path.isabs(image_path):
            return match.group(0)
        resolved_path = (source_markdown_dir / image_path).resolve()
        relative_path = os.path.relpath(resolved_path, target_markdown_dir.resolve())
        return f"{match.group(1)}{relative_path}{match.group(3)}"

    return image_pattern.sub(replace, markdown_text)


def count_main_text_figures_in_catalog(figure_catalog: dict[str, Any]) -> int:
    count = 0
    for item in figure_catalog.get("figures", []) or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("paper_role") or "").strip().lower() == "main_text":
            count += 1
    return count


def parse_independent_figure_legend_map(figure_legends_section: str) -> dict[str, str]:
    legend_by_figure_id: dict[str, str] = {}
    for heading, block_body in parse_figure_blocks(figure_legends_section):
        figure_id = parse_figure_id_from_heading(heading)
        legend = strip_image_lines(block_body).strip()
        if figure_id and legend:
            legend_by_figure_id[figure_id] = legend

    for paragraph in re.split(r"\n\s*\n", figure_legends_section.strip()):
        lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        if not lines:
            continue
        first_line = lines[0].lstrip("#").strip()
        figure_id = parse_figure_id_from_heading(first_line)
        if figure_id and figure_id not in legend_by_figure_id:
            legend_by_figure_id[figure_id] = "\n".join(lines)
    return legend_by_figure_id


def inspect_submission_source_markdown(source_markdown_path: Path) -> dict[str, Any]:
    if not source_markdown_path.exists():
        return {
            "exists": False,
            "figure_block_count": 0,
            "figure_blocks_with_images": 0,
            "figure_blocks_with_legends": 0,
        }
    markdown_text = source_markdown_path.read_text(encoding="utf-8")
    _, body = split_front_matter(markdown_text)
    figures_section = extract_top_level_markdown_block(
        body,
        "Main Figures",
        "Figures",
        "Main-text figures",
    )
    figure_legends_section = extract_top_level_markdown_block(body, "Figure Legends", "Figure Legend")
    independent_legend_by_figure_id = parse_independent_figure_legend_map(figure_legends_section)
    figure_blocks = parse_figure_blocks(figures_section) if figures_section.strip() else []
    figure_blocks_with_images = 0
    figure_blocks_with_legends = 0
    for heading, block_body in figure_blocks:
        figure_id = parse_figure_id_from_heading(heading)
        if extract_image_lines(block_body):
            figure_blocks_with_images += 1
        if strip_image_lines(block_body).strip() or (figure_id and independent_legend_by_figure_id.get(figure_id)):
            figure_blocks_with_legends += 1
    return {
        "exists": True,
        "mtime_ns": source_markdown_path.stat().st_mtime_ns,
        "figure_block_count": len(figure_blocks),
        "figure_blocks_with_images": figure_blocks_with_images,
        "figure_blocks_with_legends": figure_blocks_with_legends,
    }


def inspect_submission_docx_surface(docx_path: Path) -> dict[str, Any]:
    if not docx_path.exists() or docx_path.is_dir():
        return {
            "exists": False,
            "embedded_image_count": 0,
            "drawing_count": 0,
        }
    try:
        with zipfile.ZipFile(docx_path) as archive:
            names = archive.namelist()
            document_xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    except (KeyError, zipfile.BadZipFile):
        return {
            "exists": True,
            "mtime_ns": docx_path.stat().st_mtime_ns,
            "embedded_image_count": 0,
            "drawing_count": 0,
            "unreadable": True,
        }
    return {
        "exists": True,
        "mtime_ns": docx_path.stat().st_mtime_ns,
        "embedded_image_count": len([name for name in names if name.startswith("word/media/")]),
        "drawing_count": document_xml.count("<w:drawing"),
        "unreadable": False,
    }


def inspect_submission_pdf_surface(pdf_path: Path) -> dict[str, Any]:
    if not pdf_path.exists():
        return {
            "exists": False,
            "embedded_image_count": 0,
            "page_count": 0,
        }
    try:
        reader = PdfReader(str(pdf_path))
        embedded_image_count = sum(len(page.images) for page in reader.pages)
    except Exception:
        return {
            "exists": True,
            "mtime_ns": pdf_path.stat().st_mtime_ns,
            "embedded_image_count": 0,
            "page_count": 0,
            "unreadable": True,
        }
    return {
        "exists": True,
        "mtime_ns": pdf_path.stat().st_mtime_ns,
        "embedded_image_count": embedded_image_count,
        "page_count": len(reader.pages),
        "unreadable": False,
    }


def build_submission_manuscript_surface_qc(
    *,
    publication_profile: str,
    source_markdown_path: Path,
    docx_path: Path,
    pdf_path: Path,
    expected_main_figure_count: int,
) -> dict[str, Any]:
    qc_profile = "submission_manuscript_surface"
    if publication_profile != GENERAL_MEDICAL_JOURNAL_PROFILE:
        return {
            "qc_profile": qc_profile,
            "status": "not_applicable",
            "expected_main_figure_count": expected_main_figure_count,
            "failures": [],
        }

    source_stats = inspect_submission_source_markdown(source_markdown_path)
    docx_stats = inspect_submission_docx_surface(docx_path)
    pdf_stats = inspect_submission_pdf_surface(pdf_path)
    failures: list[dict[str, Any]] = []
    source_mtime_ns = int(source_stats.get("mtime_ns") or 0)
    docx_older_than_source_markdown = bool(
        source_stats["exists"]
        and docx_stats["exists"]
        and source_mtime_ns > int(docx_stats.get("mtime_ns") or 0)
    )
    pdf_older_than_source_markdown = bool(
        source_stats["exists"]
        and pdf_stats["exists"]
        and source_mtime_ns > int(pdf_stats.get("mtime_ns") or 0)
    )
    docx_stats["older_than_source_markdown"] = docx_older_than_source_markdown
    pdf_stats["older_than_source_markdown"] = pdf_older_than_source_markdown

    if not source_stats["exists"]:
        failures.append(
            {
                "collection": "manuscript",
                "item_id": "source_markdown",
                "descriptor": source_markdown_path.name,
                "qc_profile": qc_profile,
                "failure_reason": "submission_source_markdown_missing",
                "audit_classes": ["manuscript_surface"],
            }
        )
    else:
        if source_stats["figure_blocks_with_images"] < expected_main_figure_count:
            failures.append(
                {
                    "collection": "manuscript",
                    "item_id": "source_markdown",
                    "descriptor": source_markdown_path.name,
                    "qc_profile": qc_profile,
                    "failure_reason": "submission_source_markdown_missing_inline_figures",
                    "audit_classes": ["manuscript_surface"],
                }
            )
        if source_stats["figure_blocks_with_legends"] < expected_main_figure_count:
            failures.append(
                {
                    "collection": "manuscript",
                    "item_id": "source_markdown",
                    "descriptor": source_markdown_path.name,
                    "qc_profile": qc_profile,
                    "failure_reason": "submission_source_markdown_missing_figure_legends",
                    "audit_classes": ["manuscript_surface"],
                }
            )

    if docx_stats["embedded_image_count"] < expected_main_figure_count:
        failures.append(
            {
                "collection": "manuscript",
                "item_id": "docx",
                "descriptor": docx_path.name,
                "qc_profile": qc_profile,
                "failure_reason": "submission_docx_missing_embedded_figures",
                "audit_classes": ["manuscript_surface"],
            }
        )
    if docx_older_than_source_markdown:
        failures.append(
            {
                "collection": "manuscript",
                "item_id": "docx",
                "descriptor": docx_path.name,
                "qc_profile": qc_profile,
                "failure_reason": "submission_docx_older_than_source_markdown",
                "audit_classes": ["manuscript_surface", "freshness"],
            }
        )
    if pdf_stats["embedded_image_count"] < expected_main_figure_count:
        failures.append(
            {
                "collection": "manuscript",
                "item_id": "pdf",
                "descriptor": pdf_path.name,
                "qc_profile": qc_profile,
                "failure_reason": "submission_pdf_missing_embedded_figures",
                "audit_classes": ["manuscript_surface"],
            }
        )
    if pdf_older_than_source_markdown:
        failures.append(
            {
                "collection": "manuscript",
                "item_id": "pdf",
                "descriptor": pdf_path.name,
                "qc_profile": qc_profile,
                "failure_reason": "submission_pdf_older_than_source_markdown",
                "audit_classes": ["manuscript_surface", "freshness"],
            }
        )

    return {
        "qc_profile": qc_profile,
        "status": "pass" if not failures else "fail",
        "expected_main_figure_count": expected_main_figure_count,
        "source_markdown": source_stats,
        "docx": docx_stats,
        "pdf": pdf_stats,
        "failures": failures,
    }


def should_build_general_medical_submission_markdown(*, compiled_text: str) -> bool:
    metadata, _ = split_front_matter(compiled_text)
    if compiled_text.lstrip().startswith("# Draft"):
        return True
    return not metadata.get("title") or not metadata.get("bibliography")


def build_general_medical_submission_markdown(
    *,
    compiled_markdown_path: Path,
    submission_root: Path,
    compiled_markdown_text: str | None = None,
) -> Path:
    paper_root = compiled_markdown_path.parent if compiled_markdown_path.name == "draft.md" else compiled_markdown_path.parents[1]
    compiled_text = compiled_markdown_text if compiled_markdown_text is not None else compiled_markdown_path.read_text(encoding="utf-8")
    metadata, body = split_front_matter(compiled_text)
    main_tables = ""
    main_figures = ""
    figure_semantics_map: dict[str, dict[str, Any]] = {}
    manuscript_title, manuscript_sections = parse_manuscript_shaped_draft(compiled_text)

    if compiled_text.lstrip().startswith("# Draft"):
        title = extract_block_between_markers(
            compiled_text,
            start_marker="## Title\n\n",
            end_markers=["\n## Abstract\n"],
            label="Title",
        )
        abstract = extract_block_between_markers(
            compiled_text,
            start_marker="## Abstract\n\n",
            end_markers=["\n## Introduction\n", "\n## Methods\n", "\n## Results\n", "\n## Discussion\n", "\n## Conclusion\n"],
            label="Abstract",
        )
        introduction = extract_optional_block_between_markers(
            compiled_text,
            start_marker="\n## Introduction\n\n",
            end_markers=["\n## Methods\n", "\n## Results\n", "\n## Discussion\n", "\n## Conclusion\n"],
            label="Introduction",
        )
        methods = extract_optional_block_between_markers(
            compiled_text,
            start_marker="\n## Methods\n\n",
            end_markers=["\n## Results\n", "\n## Discussion\n", "\n## Conclusion\n"],
            label="Methods",
        )
        results = extract_optional_block_between_markers(
            compiled_text,
            start_marker="\n## Results\n\n",
            end_markers=["\n## Discussion\n", "\n## Conclusion\n"],
            label="Results",
        )
        discussion = extract_optional_block_between_markers(
            compiled_text,
            start_marker="\n## Discussion\n\n",
            end_markers=["\n## Conclusion\n"],
            label="Discussion",
        )
        conclusion = extract_optional_block_between_markers(
            compiled_text,
            start_marker="\n## Conclusion\n\n",
            end_markers=[],
            label="Conclusion",
        )
        bibliography_path = (paper_root / "references.bib").resolve()
    elif manuscript_title and manuscript_sections:
        title = manuscript_title
        abstract = first_nonempty_block(manuscript_sections, "Abstract")
        introduction = first_nonempty_block(manuscript_sections, "Introduction")
        methods = first_nonempty_block(manuscript_sections, "Methods", "Materials and Methods", "Materials & Methods")
        results = first_nonempty_block(manuscript_sections, "Results")
        discussion = first_nonempty_block(manuscript_sections, "Discussion")
        conclusion = first_nonempty_block(manuscript_sections, "Conclusion", "Conclusions")
        main_tables = first_nonempty_block(manuscript_sections, "Main Tables", "Tables")
        main_figures = first_nonempty_block(manuscript_sections, "Main Figures", "Figures", "Main-text figures")
        figure_semantics_map = load_figure_semantics_map(paper_root)
        bibliography_path = (paper_root / "references.bib").resolve()
    else:
        title = metadata.get("title", "Article Title")
        bibliography_value = metadata.get("bibliography", "../references.bib")
        bibliography_path = (compiled_markdown_path.parent / bibliography_value).resolve()
        abstract = extract_optional_markdown_block(
            body,
            "Abstract",
            ["Introduction", "Methods", "Results", "Discussion", "Conclusion", "Main Tables", "Main Figures", "Appendix"],
        )
        introduction = extract_optional_markdown_block(
            body,
            "Introduction",
            ["Methods", "Results", "Discussion", "Conclusion", "Main Tables", "Main Figures", "Appendix"],
        )
        methods = extract_optional_markdown_block(
            body,
            "Methods",
            ["Results", "Discussion", "Conclusion", "Main Tables", "Main Figures", "Appendix"],
        )
        results = extract_optional_markdown_block(
            body,
            "Results",
            ["Discussion", "Conclusion", "Main Tables", "Main Figures", "Appendix"],
        )
        discussion = extract_optional_markdown_block(
            body,
            "Discussion",
            ["Conclusion", "Main Tables", "Main Figures", "Appendix"],
        )
        conclusion = extract_optional_markdown_block(
            body,
            "Conclusion",
            ["Main Tables", "Main Figures", "Appendix"],
        )
        main_tables = extract_optional_markdown_block(body, "Main Tables", ["Main Figures", "Appendix"])
        main_figures = extract_optional_markdown_block(body, "Main Figures", ["Appendix"])
        if not main_figures.strip():
            main_figures = extract_optional_markdown_block(body, "Figures", ["Figure Legends", "Tables", "Appendix"])
        figure_semantics_map = load_figure_semantics_map(paper_root)

    if not main_figures.strip():
        main_figures = build_catalog_backed_main_figures(
            paper_root=paper_root,
            submission_root=submission_root,
        )
        if main_figures.strip() and not figure_semantics_map:
            figure_semantics_map = load_figure_semantics_map(paper_root)

    bibliography_rel = os.path.relpath(bibliography_path, submission_root.resolve())
    catalog_image_map = build_catalog_backed_submission_figure_image_map(
        paper_root=paper_root,
        submission_root=submission_root,
    )
    submission_figure_blocks = build_submission_figure_blocks(
        main_figures=main_figures,
        figure_semantics_map=figure_semantics_map,
        catalog_image_map=catalog_image_map,
    )
    figure_legend_blocks = build_figure_legend_blocks(
        main_figures=main_figures,
        figure_semantics_map=figure_semantics_map,
    )
    table_blocks = build_table_blocks(main_tables=main_tables)
    section_blocks = [
        ("# Abstract", abstract),
        ("# Introduction", introduction),
        ("# Methods", methods),
        ("# Results", results),
        ("# Discussion", discussion),
        ("# Conclusion", conclusion),
    ]
    markdown_parts = [
        "---\n"
        f'title: "{title}"\n'
        f"bibliography: {bibliography_rel}\n"
        "link-citations: true\n"
        "---"
    ]
    for heading, content in section_blocks:
        if content.strip():
            markdown_parts.append(f"{heading}\n\n{content.strip()}")
    if submission_figure_blocks:
        markdown_parts.append(f"# Figures\n\n{'\n\n'.join(submission_figure_blocks).strip()}")
    if figure_legend_blocks:
        markdown_parts.append(f"# Figure Legends\n\n{'\n\n'.join(figure_legend_blocks).strip()}")
    if table_blocks:
        markdown_parts.append(f"# Tables\n\n{'\n\n'.join(table_blocks).strip()}")
    output_path = submission_root / "manuscript_submission.md"
    write_text(output_path, "\n\n".join(markdown_parts).strip() + "\n")
    return output_path


def build_frontiers_manuscript_markdown(
    *,
    compiled_markdown_path: Path,
    submission_root: Path,
    compiled_markdown_text: str | None = None,
) -> Path:
    paper_root = compiled_markdown_path.parents[1]
    compiled_text = compiled_markdown_text if compiled_markdown_text is not None else compiled_markdown_path.read_text(encoding="utf-8")
    metadata, body = split_front_matter(compiled_text)
    title = metadata.get("title", "Article Title")
    bibliography_value = metadata.get("bibliography", "../references.bib")
    bibliography_path = (compiled_markdown_path.parent / bibliography_value).resolve()
    bibliography_rel = os.path.relpath(bibliography_path, submission_root.resolve())

    abstract = extract_markdown_block(
        body,
        "Abstract",
        ["Introduction", "Methods", "Results", "Discussion", "Main Figures", "Main Tables", "Appendix"],
    )
    introduction = extract_optional_markdown_block(
        body,
        "Introduction",
        ["Methods", "Results", "Discussion", "Main Tables", "Main Figures", "Appendix"],
    )
    methods = extract_optional_markdown_block(
        body,
        "Methods",
        ["Results", "Discussion", "Main Tables", "Main Figures", "Appendix"],
    )
    results = extract_optional_markdown_block(
        body,
        "Results",
        ["Discussion", "Main Tables", "Main Figures", "Appendix"],
    )
    discussion = extract_optional_markdown_block(
        body,
        "Discussion",
        ["Main Tables", "Main Figures", "Appendix"],
    )
    main_tables = extract_optional_markdown_block(body, "Main Tables", ["Main Figures"])
    main_figures = extract_optional_markdown_block(body, "Main Figures", ["Appendix"])
    figure_semantics_map = load_figure_semantics_map(paper_root)

    figure_legend_blocks = build_figure_legend_blocks(
        main_figures=main_figures,
        figure_semantics_map=figure_semantics_map,
    )
    table_blocks = build_table_blocks(main_tables=main_tables)

    markdown_text = (
        f"---\n"
        f'title: "{title}"\n'
        f"bibliography: {bibliography_rel}\n"
        f"link-citations: true\n"
        f"---\n\n"
        f"Authors: [To be completed before submission.]\n\n"
        f"Affiliations: [To be completed before submission.]\n\n"
        f"*Correspondence:* [To be completed before submission.]\n\n"
        f"Keywords: {', '.join(FRONTIERS_KEYWORDS)}\n\n"
        f"# Abstract\n\n{abstract}\n\n"
        f"# Introduction\n\n{introduction}\n\n"
        f"# Materials and methods\n\n{methods}\n\n"
        f"# Results\n\n{results}\n\n"
        f"# Discussion\n\n{discussion}\n\n"
        f"{build_frontiers_required_sections()}\n\n"
        f"# Figure Legends\n\n{'\n\n'.join(figure_legend_blocks).strip()}\n\n"
        f"# Tables\n\n{'\n\n'.join(table_blocks).strip()}\n"
    )
    output_path = submission_root / "frontiers_manuscript.md"
    write_text(output_path, markdown_text)
    return output_path


def build_frontiers_supplementary_markdown(
    *,
    compiled_markdown_path: Path,
    submission_root: Path,
    compiled_markdown_text: str | None = None,
) -> Path:
    compiled_text = compiled_markdown_text if compiled_markdown_text is not None else compiled_markdown_path.read_text(encoding="utf-8")
    metadata, body = split_front_matter(compiled_text)
    bibliography_value = metadata.get("bibliography", "../references.bib")
    bibliography_path = (compiled_markdown_path.parent / bibliography_value).resolve()
    bibliography_rel = os.path.relpath(bibliography_path, submission_root.resolve())
    appendix = extract_optional_markdown_block(body, "Appendix", [])
    if not appendix.strip():
        main_figures = extract_optional_markdown_block(body, "Main Figures", ["Appendix", "Main Tables"])
        supplementary_blocks = [
            f"## {heading}\n\n{block_body}"
            for heading, block_body in parse_heading_blocks(main_figures, "Supplementary Figure ")
        ]
        appendix = "\n\n".join(supplementary_blocks).strip()
    rewritten_appendix = rewrite_image_paths(
        markdown_text=appendix,
        source_markdown_dir=compiled_markdown_path.parent,
        target_markdown_dir=submission_root,
    )
    markdown_text = (
        "---\n"
        'title: "Supplementary Material"\n'
        f"bibliography: {bibliography_rel}\n"
        "link-citations: true\n"
        "---\n\n"
        "# Supplementary Material\n\n"
        "This file contains supplementary figures and appendix material prepared for journal submission.\n\n"
        f"{rewritten_appendix.strip()}\n"
    )
    output_path = submission_root / "frontiers_supplementary_material.md"
    write_text(output_path, markdown_text)
    return output_path


def create_submission_minimal_package(
    *,
    paper_root: Path,
    publication_profile: str,
    citation_style: str | None = "auto",
) -> dict[str, Any]:
    paper_root = paper_root.resolve()
    workspace_root = workspace_root_from_paper_root(paper_root)
    requested_publication_profile = str(publication_profile or "").strip()
    profile_config = resolve_publication_profile_config(
        publication_profile=requested_publication_profile,
        citation_style=citation_style,
    )
    resolved_publication_profile = profile_config.publication_profile
    submission_root = resolve_output_root(paper_root=paper_root, publication_profile=resolved_publication_profile)
    figures_output_dir = submission_root / "figures"
    tables_output_dir = submission_root / "tables"

    bundle_manifest = load_json(paper_root / "paper_bundle_manifest.json")
    compile_report_path = resolve_relpath(
        workspace_root,
        resolve_bundle_input_path(
            bundle_manifest=bundle_manifest,
            key="compile_report_path",
        ),
    )
    figure_catalog_path = resolve_relpath(
        workspace_root,
        resolve_bundle_input_path(
            bundle_manifest=bundle_manifest,
            key="figure_catalog_path",
            fallback="paper/figures/figure_catalog.json",
        ),
    )
    table_catalog_path = resolve_relpath(
        workspace_root,
        resolve_bundle_input_path(
            bundle_manifest=bundle_manifest,
            key="table_catalog_path",
            fallback="paper/tables/table_catalog.json",
        ),
    )

    compile_report = load_json(compile_report_path)
    figure_catalog = load_json(figure_catalog_path)
    table_catalog = load_json(table_catalog_path)
    pack_lock_payload = _load_display_pack_lock_payload(paper_root=paper_root)
    pack_lock_path, pack_summary_by_id = (
        pack_lock_payload[0],
        _build_display_pack_summary_by_id(pack_lock_payload[1]),
    ) if pack_lock_payload is not None else (None, {})
    excluded_compiled_source_roots = resolve_submission_compiled_source_excluded_roots(
        paper_root=paper_root,
        workspace_root=workspace_root,
        submission_root=submission_root,
        bundle_manifest=bundle_manifest,
        compile_report=compile_report,
    )

    compiled_markdown_path = resolve_compiled_markdown_path(
        workspace_root=workspace_root,
        bundle_manifest=bundle_manifest,
        compile_report=compile_report,
        excluded_roots=excluded_compiled_source_roots,
    )
    compiled_pdf_path = resolve_compiled_pdf_path(
        workspace_root=workspace_root,
        bundle_manifest=bundle_manifest,
        compile_report=compile_report,
        excluded_roots=excluded_compiled_source_roots,
    )

    if not compiled_markdown_path.exists():
        raise FileNotFoundError(f"missing compiled markdown: {compiled_markdown_path}")
    if not compiled_pdf_path.exists():
        raise FileNotFoundError(f"missing compiled pdf: {compiled_pdf_path}")

    compiled_markdown_text = compiled_markdown_path.read_text(encoding="utf-8")
    preserved_compiled_markdown_rel: Path | None = None
    try:
        preserved_compiled_markdown_rel = compiled_markdown_path.relative_to(submission_root)
    except ValueError:
        preserved_compiled_markdown_rel = None

    if submission_root.exists():
        shutil.rmtree(submission_root)
    submission_root.mkdir(parents=True, exist_ok=True)
    if preserved_compiled_markdown_rel is not None:
        write_text(submission_root / preserved_compiled_markdown_rel, compiled_markdown_text)
    readme_path = submission_root / "README.md"
    output_docx_path = submission_root / "manuscript.docx"
    output_pdf_path = submission_root / "paper.pdf"

    source_markdown_path = compiled_markdown_path
    supplementary_source_markdown_path: Path | None = None
    supplementary_output_docx_path: Path | None = None
    source_markdown_alias_path: Path | None = None

    if resolved_publication_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        source_markdown_path = build_general_medical_submission_markdown(
            compiled_markdown_path=compiled_markdown_path,
            submission_root=submission_root,
            compiled_markdown_text=compiled_markdown_text,
        )
    elif is_frontiers_family_harvard_profile(resolved_publication_profile):
        source_markdown_path = build_frontiers_manuscript_markdown(
            compiled_markdown_path=compiled_markdown_path,
            submission_root=submission_root,
            compiled_markdown_text=compiled_markdown_text,
        )
        supplementary_source_markdown_path = build_frontiers_supplementary_markdown(
            compiled_markdown_path=compiled_markdown_path,
            submission_root=submission_root,
            compiled_markdown_text=compiled_markdown_text,
        )
        supplementary_output_docx_path = submission_root / str(profile_config.supplementary_docx_name)
    if source_markdown_path.name != "manuscript_source.md":
        source_markdown_alias_path = submission_root / "manuscript_source.md"
        if source_markdown_alias_path.resolve() != source_markdown_path.resolve():
            shutil.copy2(source_markdown_path, source_markdown_alias_path)

    figure_entries: list[dict[str, Any]] = []
    figure_naming_map: dict[str, str] = {}
    for entry in figure_catalog.get("figures", []):
        export_paths = resolve_figure_source_paths(entry)
        if not export_paths:
            continue
        missing_paths = find_missing_source_paths(
            workspace_root=workspace_root,
            paper_root=paper_root,
            source_paths=export_paths,
        )
        if missing_paths:
            if is_planned_catalog_entry(entry):
                continue
            missing_paths_text = ", ".join(str(path) for path in missing_paths)
            raise FileNotFoundError(f"missing submission asset(s) for figure `{entry.get('figure_id')}`: {missing_paths_text}")
        basename = build_figure_basename(str(entry["figure_id"]))
        output_paths = copy_with_renamed_targets(
            workspace_root=workspace_root,
            paper_root=paper_root,
            source_paths=export_paths,
            output_dir=figures_output_dir,
            basename=basename,
        )
        figure_naming_map[str(entry["figure_id"])] = basename
        pack_id = _resolve_pack_id(entry, id_field="template_id")
        figure_entry = {
            "figure_id": entry["figure_id"],
            "template_id": entry.get("template_id"),
            "pack_id": pack_id,
            "renderer_family": entry.get("renderer_family"),
            "paper_role": entry.get("paper_role"),
            "input_schema_id": entry.get("input_schema_id"),
            "qc_profile": entry.get("qc_profile"),
            "qc_result": entry.get("qc_result"),
            "source_paths": export_paths,
            "output_paths": output_paths,
        }
        _attach_pack_provenance(
            figure_entry,
            pack_id=pack_id,
            pack_summary_by_id=pack_summary_by_id,
        )
        figure_entries.append(figure_entry)

    table_entries: list[dict[str, Any]] = []
    table_naming_map: dict[str, str] = {}
    for entry in table_catalog.get("tables", []):
        asset_paths = resolve_table_source_paths(entry)
        if not asset_paths:
            continue
        missing_paths = find_missing_source_paths(
            workspace_root=workspace_root,
            paper_root=paper_root,
            source_paths=asset_paths,
        )
        if missing_paths:
            if is_planned_catalog_entry(entry):
                continue
            missing_paths_text = ", ".join(str(path) for path in missing_paths)
            raise FileNotFoundError(f"missing submission asset(s) for table `{entry.get('table_id')}`: {missing_paths_text}")
        basename = build_table_basename(str(entry["table_id"]))
        output_paths = copy_with_renamed_targets(
            workspace_root=workspace_root,
            paper_root=paper_root,
            source_paths=asset_paths,
            output_dir=tables_output_dir,
            basename=basename,
        )
        table_naming_map[str(entry["table_id"])] = basename
        pack_id = _resolve_pack_id(entry, id_field="table_shell_id")
        table_entry = {
            "table_id": entry["table_id"],
            "table_shell_id": entry.get("table_shell_id"),
            "pack_id": pack_id,
            "paper_role": entry.get("paper_role"),
            "input_schema_id": entry.get("input_schema_id"),
            "qc_profile": entry.get("qc_profile"),
            "qc_result": entry.get("qc_result"),
            "source_paths": asset_paths,
            "output_paths": output_paths,
        }
        _attach_pack_provenance(
            table_entry,
            pack_id=pack_id,
            pack_summary_by_id=pack_summary_by_id,
        )
        table_entries.append(table_entry)

    export_docx(
        compiled_markdown_path=source_markdown_path,
        paper_root=paper_root,
        output_docx_path=output_docx_path,
        csl_path=profile_config.csl_path,
        reference_doc_path=profile_config.reference_doc_path,
    )
    export_pdf(
        compiled_markdown_path=source_markdown_path,
        paper_root=paper_root,
        output_pdf_path=output_pdf_path,
        csl_path=profile_config.csl_path,
    )
    if supplementary_source_markdown_path is not None and supplementary_output_docx_path is not None:
        export_docx(
            compiled_markdown_path=supplementary_source_markdown_path,
            paper_root=paper_root,
            output_docx_path=supplementary_output_docx_path,
            csl_path=profile_config.csl_path,
            reference_doc_path=profile_config.supplementary_reference_doc_path,
        )
    references_manifest = materialize_submission_references(
        paper_root=paper_root,
        submission_root=submission_root,
        workspace_root=workspace_root,
    )

    pruned_legacy_paths = prune_legacy_paper_surface_exports(
        paper_root=paper_root,
        figure_catalog=figure_catalog,
        table_catalog=table_catalog,
    )
    manuscript_surface_qc = build_submission_manuscript_surface_qc(
        publication_profile=resolved_publication_profile,
        source_markdown_path=source_markdown_path,
        docx_path=output_docx_path,
        pdf_path=output_pdf_path,
        expected_main_figure_count=count_main_text_figures_in_catalog(figure_catalog),
    )
    source_contract = build_submission_minimal_source_contract(
        paper_root=paper_root,
        workspace_root=workspace_root,
        compile_report_path=compile_report_path,
        compiled_markdown_path=compiled_markdown_path,
        figure_catalog_path=figure_catalog_path,
        table_catalog_path=table_catalog_path,
        figure_catalog=figure_catalog,
        table_catalog=table_catalog,
        pack_lock_path=pack_lock_path,
    )
    submission_root_rel = relpath_from_workspace(submission_root, workspace_root)
    source_markdown_metadata, _ = split_front_matter(source_markdown_path.read_text(encoding="utf-8"))
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "publication_profile": resolved_publication_profile,
        "citation_style": profile_config.citation_style,
        "output_root": submission_root_rel,
        "manuscript": {
            "source_markdown_path": relpath_from_workspace(source_markdown_path, workspace_root),
            "pdf_path": relpath_from_workspace(output_pdf_path, workspace_root),
            "docx_path": relpath_from_workspace(output_docx_path, workspace_root),
            "csl_path": str(profile_config.csl_path.resolve()),
            "surface_qc": manuscript_surface_qc,
        },
        "naming_map": {
            "figures": figure_naming_map,
            "tables": table_naming_map,
        },
        "figures": figure_entries,
        "tables": table_entries,
        "front_matter_placeholders": build_front_matter_placeholders(
            metadata=source_markdown_metadata,
        ),
        "source_signature": source_contract["source_signature"],
        "source_contract": source_contract,
    }
    if references_manifest is not None:
        manifest["references"] = references_manifest
    if source_markdown_alias_path is not None:
        manifest["manuscript"]["source_markdown_alias_path"] = relpath_from_workspace(
            source_markdown_alias_path,
            workspace_root,
        )
    if pack_lock_path is not None:
        manifest["display_pack_lock_path"] = relpath_from_workspace(pack_lock_path, workspace_root)
        manifest["enabled_display_packs"] = list(pack_summary_by_id.values())
    if pruned_legacy_paths:
        manifest["pruned_legacy_paths"] = pruned_legacy_paths
    if requested_publication_profile != resolved_publication_profile:
        manifest["requested_publication_profile"] = requested_publication_profile
    if profile_config.reference_doc_path is not None:
        journal_target = {
            "reference_doc_path": str(profile_config.reference_doc_path.resolve()),
        }
        if profile_config.journal_name is not None:
            journal_target["journal_name"] = profile_config.journal_name
        if profile_config.journal_family is not None:
            journal_target["journal_family"] = profile_config.journal_family
        if profile_config.reference_style_family is not None:
            journal_target["reference_style_family"] = profile_config.reference_style_family
        manifest["journal_target"] = journal_target
    if supplementary_source_markdown_path is not None and supplementary_output_docx_path is not None:
        manifest["supplementary_material"] = {
            "source_markdown_path": relpath_from_workspace(supplementary_source_markdown_path, workspace_root),
            "docx_path": relpath_from_workspace(supplementary_output_docx_path, workspace_root),
            "reference_doc_path": str(profile_config.supplementary_reference_doc_path.resolve()),
        }

    write_text(
        readme_path,
        build_submission_minimal_readme(publication_profile=resolved_publication_profile),
    )
    manifest["readme_path"] = relpath_from_workspace(readme_path, workspace_root)
    submission_manifest_path = submission_root / "submission_manifest.json"
    dump_json(submission_manifest_path, manifest)
    archived_surface_roots = materialize_archived_reference_only_submission_surface_manifests(
        paper_root,
        active_manifest_path=submission_manifest_path,
    )
    if archived_surface_roots:
        manifest["archived_reference_only_submission_surface_roots"] = [
            relpath_from_workspace(surface_root, workspace_root) for surface_root in archived_surface_roots
        ]
        dump_json(submission_manifest_path, manifest)
    delivery_sync_result: dict[str, Any] | None = None
    if study_delivery_sync.can_sync_study_delivery(paper_root=paper_root):
        delivery_sync_result = study_delivery_sync.sync_study_delivery(
            paper_root=paper_root,
            stage="submission_minimal",
            publication_profile=resolved_publication_profile,
        )
    if delivery_sync_result is not None:
        return {
            **manifest,
            "delivery_sync": delivery_sync_result,
        }
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a submission-minimal manuscript package.")
    parser.add_argument("--paper-root", type=Path, required=True)
    parser.add_argument("--publication-profile", default="general_medical_journal")
    parser.add_argument("--citation-style", default="auto")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    create_submission_minimal_package(
        paper_root=args.paper_root,
        publication_profile=args.publication_profile,
        citation_style=args.citation_style,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
