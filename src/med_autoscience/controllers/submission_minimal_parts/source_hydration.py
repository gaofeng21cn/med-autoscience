from __future__ import annotations

import filecmp
import re
import shutil

from .shared_base import Any, Path, dump_json, load_json, resolve_relpath, utc_now


_BODY_AUTHORITY_CURRENT_BODY_PAPER_REL = (
    "artifacts/stage_outputs/_body_authority/paper_authority_cutover/current_body/paper"
)

_DELIVERY_REQUIRED_SOURCE_RELS = (
    "draft.md",
    "build/review_manuscript.md",
    "references.bib",
    "evidence_ledger.json",
    "figure_catalog.json",
    "figure_semantics_manifest.json",
    "figures/figure_catalog.json",
    "figures/figure_semantics_manifest.json",
    "review/review_ledger.json",
    "table_catalog.json",
    "tables/table_catalog.json",
)

_DELIVERY_REQUIRED_SOURCE_DIRS = (
    "figures/generated",
    "tables/generated",
)

_SOURCE_DECLARATION_COLLECTIONS = (
    "figures",
    "main_text_figures",
    "deferred_figures",
    "tables",
)


def _current_body_paper_root(*, paper_root: Path) -> Path:
    resolved = paper_root.resolve()
    current_body_parts = Path(_BODY_AUTHORITY_CURRENT_BODY_PAPER_REL).parts
    if tuple(resolved.parts[-len(current_body_parts) :]) == current_body_parts:
        return resolved
    return resolved.parent / _BODY_AUTHORITY_CURRENT_BODY_PAPER_REL


def _copy_if_source_changed(
    *,
    source_root: Path,
    paper_root: Path,
    rel_path: str,
) -> Path | None:
    source_path = source_root / rel_path
    if not source_path.exists():
        return None
    target_path = paper_root / rel_path
    if target_path.exists():
        if filecmp.cmp(source_path, target_path, shallow=False):
            return None
        try:
            if target_path.stat().st_mtime_ns > source_path.stat().st_mtime_ns:
                return None
        except OSError:
            pass
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)
    return target_path


def _copy_tree_changed(
    *,
    source_root: Path,
    paper_root: Path,
    rel_path: str,
) -> list[Path]:
    source_dir = source_root / rel_path
    if not source_dir.is_dir():
        return []
    copied: list[Path] = []
    for source_path in sorted(path for path in source_dir.rglob("*") if path.is_file()):
        nested_rel = source_path.relative_to(source_root).as_posix()
        copied_path = _copy_if_source_changed(
            source_root=source_root,
            paper_root=paper_root,
            rel_path=nested_rel,
        )
        if copied_path is not None:
            copied.append(copied_path)
    return copied


def _filter_nested_figure_catalog_to_canonical_main_figures(
    *,
    source_root: Path,
    paper_root: Path,
) -> Path | None:
    canonical_path = source_root / "figure_catalog.json"
    nested_path = paper_root / "figures" / "figure_catalog.json"
    if not canonical_path.exists() or not nested_path.exists():
        return None
    canonical_payload = load_json(canonical_path)
    nested_payload = load_json(nested_path)
    canonical_figures = canonical_payload.get("figures") or []
    nested_figures = nested_payload.get("figures") or []
    if not isinstance(canonical_figures, list) or not isinstance(nested_figures, list):
        return None

    allowed_titles = {
        str(item.get("title") or "").strip()
        for item in canonical_figures
        if isinstance(item, dict) and str(item.get("title") or "").strip()
    }
    allowed_ids = {
        re.sub(r"^figure\s+", "F", str(item.get("figure_id") or "").strip(), flags=re.IGNORECASE)
        for item in canonical_figures
        if isinstance(item, dict) and str(item.get("figure_id") or "").strip()
    }
    def _matches_canonical(entry: Any) -> bool:
        if not isinstance(entry, dict):
            return False
        return (
            str(entry.get("title") or "").strip() in allowed_titles
            or str(entry.get("figure_id") or "").strip() in allowed_ids
        )

    filtered_figures = [item for item in nested_figures if _matches_canonical(item)]
    deferred_figures = nested_payload.get("deferred_figures") or []
    filtered_deferred_figures = [item for item in deferred_figures if _matches_canonical(item)]
    main_text_figures = nested_payload.get("main_text_figures") or []
    filtered_main_text_figures = [item for item in main_text_figures if _matches_canonical(item)]

    if (
        len(filtered_figures) == len(nested_figures)
        and len(filtered_deferred_figures) == len(deferred_figures)
        and len(filtered_main_text_figures) == len(main_text_figures)
    ):
        return None

    filtered_payload = dict(nested_payload)
    filtered_payload["figures"] = filtered_figures
    if isinstance(deferred_figures, list):
        filtered_payload["deferred_figures"] = filtered_deferred_figures
    if isinstance(main_text_figures, list):
        filtered_payload["main_text_figures"] = filtered_main_text_figures
    dump_json(nested_path, filtered_payload)
    return nested_path


def _relpath_from_paper(path: Path, *, paper_root: Path) -> str:
    return f"paper/{path.resolve().relative_to(paper_root.resolve()).as_posix()}"


def _normalize_paper_relative_source_path(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.startswith("paper/"):
        return normalized.removeprefix("paper/")
    return None


def _catalog_declared_source_paths(payload: dict[str, Any]) -> set[str]:
    declared_paths: set[str] = set()
    for collection_name in _SOURCE_DECLARATION_COLLECTIONS:
        entries = payload.get(collection_name)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            source_paths = entry.get("source_paths")
            if not isinstance(source_paths, list):
                continue
            for value in source_paths:
                normalized = _normalize_paper_relative_source_path(value)
                if normalized is not None:
                    declared_paths.add(normalized)
    return declared_paths


def _normalized_render_request_ids(payload: dict[str, Any]) -> set[str]:
    figure_ids: set[str] = set()
    for collection_name in ("figures", "main_text_figures", "deferred_figures"):
        entries = payload.get(collection_name)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for raw_value in (
                entry.get("figure_id"),
                entry.get("catalog_id"),
            ):
                if not isinstance(raw_value, str):
                    continue
                normalized = raw_value.strip()
                if not normalized:
                    continue
                normalized = re.sub(r"^figure\s+", "F", normalized, flags=re.IGNORECASE)
                figure_ids.add(normalized)
    return figure_ids


def _hydrate_catalog_declared_sources(
    *,
    source_root: Path,
    paper_root: Path,
) -> list[Path]:
    hydrated: list[Path] = []
    declared_relpaths: set[str] = set()
    render_request_ids: set[str] = set()
    for rel_path in (
        "figure_catalog.json",
        "figures/figure_catalog.json",
        "table_catalog.json",
        "tables/table_catalog.json",
    ):
        catalog_path = source_root / rel_path
        if not catalog_path.exists():
            continue
        try:
            payload = load_json(catalog_path)
        except Exception:
            continue
        declared_relpaths.update(_catalog_declared_source_paths(payload))
        render_request_ids.update(_normalized_render_request_ids(payload))

    for rel_path in sorted(declared_relpaths):
        copied_path = _copy_if_source_changed(
            source_root=source_root,
            paper_root=paper_root,
            rel_path=rel_path,
        )
        if copied_path is not None:
            hydrated.append(copied_path)

    for figure_id in sorted(render_request_ids):
        copied_path = _copy_if_source_changed(
            source_root=source_root,
            paper_root=paper_root,
            rel_path=f"build/display_pack_render_requests/{figure_id}.render_request.json",
        )
        if copied_path is not None:
            hydrated.append(copied_path)

    return hydrated


def _first_existing_current_body_compile_report(*, source_root: Path) -> Path | None:
    for rel_path in ("build/compile_report.json", "compile_report.json"):
        candidate = source_root / rel_path
        if candidate.exists():
            return candidate
    return None


def _compile_report_has_current_source_locator(payload: dict[str, Any]) -> bool:
    return any(
        isinstance(payload.get(key), str) and str(payload.get(key)).strip()
        for key in ("source_markdown_path", "source_markdown", "entry_path")
    )


def _source_path_values(payload: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("source_markdown_path", "source_markdown", "entry_path", "pdf_path", "output_pdf"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    return values


def _hydrate_source_paths_from_compile_report(
    *,
    source_root: Path,
    paper_root: Path,
    compile_report: dict[str, Any],
) -> list[Path]:
    hydrated: list[Path] = []
    for value in _source_path_values(compile_report):
        if not value.startswith("paper/"):
            continue
        rel_path = value.removeprefix("paper/")
        copied_path = _copy_if_source_changed(
            source_root=source_root,
            paper_root=paper_root,
            rel_path=rel_path,
        )
        if copied_path is not None:
            hydrated.append(copied_path)
    return hydrated


def _hydrate_delivery_required_sources(
    *,
    source_root: Path,
    paper_root: Path,
) -> list[Path]:
    hydrated: list[Path] = []
    for rel_path in _DELIVERY_REQUIRED_SOURCE_RELS:
        copied_path = _copy_if_source_changed(
            source_root=source_root,
            paper_root=paper_root,
            rel_path=rel_path,
        )
        if copied_path is not None:
            hydrated.append(copied_path)
    for rel_path in _DELIVERY_REQUIRED_SOURCE_DIRS:
        hydrated.extend(
            _copy_tree_changed(
                source_root=source_root,
                paper_root=paper_root,
                rel_path=rel_path,
            )
        )
    filtered_catalog_path = _filter_nested_figure_catalog_to_canonical_main_figures(
        source_root=source_root,
        paper_root=paper_root,
    )
    if filtered_catalog_path is not None:
        hydrated.append(filtered_catalog_path)
    hydrated.extend(
        _hydrate_catalog_declared_sources(
            source_root=source_root,
            paper_root=paper_root,
        )
    )
    return hydrated


def _build_compile_report_from_current_draft(*, paper_root: Path) -> dict[str, Any] | None:
    draft_path = paper_root / "draft.md"
    if not draft_path.exists():
        return None
    return {
        "schema_version": 1,
        "status": "current_draft_compile_source_hydrated",
        "created_at": utc_now(),
        "source_markdown_path": "paper/draft.md",
        "source_markdown_hydration": {
            "status": "current_paper_root_draft_used",
            "source": "paper/draft.md",
        },
        "output_pdf": "paper/paper.pdf",
        "notes": [
            "Generated by submission-minimal source hydration so package export rebuilds PDF from the current paper draft."
        ],
    }


def _sync_review_manuscript_from_current_draft(*, paper_root: Path) -> Path | None:
    draft_path = paper_root / "draft.md"
    if not draft_path.exists():
        return None
    review_manuscript_path = paper_root / "build" / "review_manuscript.md"
    if review_manuscript_path.exists() and filecmp.cmp(draft_path, review_manuscript_path, shallow=False):
        return None
    review_manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(draft_path, review_manuscript_path)
    return review_manuscript_path


def _source_markdown_values(payload: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("source_markdown_path", "source_markdown", "entry_path"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
    return values


def _source_points_to_current_draft(payload: dict[str, Any]) -> bool:
    return any(
        value in {"draft.md", "paper/draft.md"} or value.endswith("/paper/draft.md")
        for value in _source_markdown_values(payload)
    )


def _compile_report_needs_current_draft_refresh(
    *,
    paper_root: Path,
    compile_report_path: Path,
    bundle_manifest: dict[str, Any],
) -> bool:
    draft_path = paper_root / "draft.md"
    if not draft_path.exists():
        return False
    if not compile_report_path.exists():
        return True
    try:
        compile_report = load_json(compile_report_path)
    except (OSError, ValueError):
        compile_report = {}
    try:
        draft_mtime = draft_path.stat().st_mtime
        compile_report_mtime = compile_report_path.stat().st_mtime
    except OSError:
        return True
    explicit_draft_path = bundle_manifest.get("draft_path")
    if (
        _compile_report_has_current_source_locator(compile_report)
        and not _source_points_to_current_draft(compile_report)
        and isinstance(explicit_draft_path, str)
        and explicit_draft_path.strip()
    ):
        return False
    if _source_points_to_current_draft(compile_report) and compile_report_mtime >= draft_mtime:
        return False
    return draft_mtime > compile_report_mtime


def hydrate_submission_package_sources_from_current_body(
    *,
    paper_root: Path,
    bundle_manifest: dict[str, Any],
) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    workspace_root = resolved_paper_root.parent
    source_root = _current_body_paper_root(paper_root=resolved_paper_root)
    target_compile_report_path = resolved_paper_root / "build" / "compile_report.json"
    hydrated_files: list[Path] = []
    source_compile_report_path: Path | None = None
    source_compile_report_status = "not_used"
    target_compile_report_existed = target_compile_report_path.exists()

    if source_root.exists():
        hydrated_files.extend(
            _hydrate_delivery_required_sources(
                source_root=source_root,
                paper_root=resolved_paper_root,
            )
        )
        source_compile_report_path = _first_existing_current_body_compile_report(source_root=source_root)
        if source_compile_report_path is not None:
            source_compile_report = load_json(source_compile_report_path)
            if _compile_report_has_current_source_locator(source_compile_report):
                source_compile_report_status = "hydrated_from_current_body"
                rel_path = source_compile_report_path.relative_to(source_root).as_posix()
                copied_path = _copy_if_source_changed(
                    source_root=source_root,
                    paper_root=resolved_paper_root,
                    rel_path=rel_path,
                )
                if copied_path is not None:
                    hydrated_files.append(copied_path)
                if rel_path != "build/compile_report.json":
                    target_compile_report_path.parent.mkdir(parents=True, exist_ok=True)
                    dump_json(target_compile_report_path, source_compile_report)
                    hydrated_files.append(target_compile_report_path)
                hydrated_files.extend(
                    _hydrate_source_paths_from_compile_report(
                        source_root=source_root,
                        paper_root=resolved_paper_root,
                        compile_report=source_compile_report,
                    )
                )
            else:
                source_compile_report_status = "ignored_no_current_source_locator"

    if _compile_report_needs_current_draft_refresh(
        paper_root=resolved_paper_root,
        compile_report_path=target_compile_report_path,
        bundle_manifest=bundle_manifest,
    ):
        generated_compile_report = _build_compile_report_from_current_draft(paper_root=resolved_paper_root)
        if generated_compile_report is not None:
            dump_json(target_compile_report_path, generated_compile_report)
            hydrated_files.append(target_compile_report_path)
            source_compile_report_status = (
                "refreshed_from_current_draft"
                if target_compile_report_existed or source_compile_report_status != "not_used"
                else "generated_from_current_draft"
            )

    try:
        effective_compile_report = load_json(target_compile_report_path)
    except (OSError, ValueError):
        effective_compile_report = {}
    if _source_points_to_current_draft(effective_compile_report):
        synced_review_path = _sync_review_manuscript_from_current_draft(paper_root=resolved_paper_root)
        if synced_review_path is not None:
            hydrated_files.append(synced_review_path)

    bundle_inputs = bundle_manifest.get("bundle_inputs")
    compile_report_ref = None
    if isinstance(bundle_inputs, dict):
        compile_report_ref = bundle_inputs.get("compile_report_path")
    if compile_report_ref is None:
        compile_report_ref = bundle_manifest.get("compile_report_path")
    resolved_compile_report = (
        resolve_relpath(workspace_root, str(compile_report_ref))
        if isinstance(compile_report_ref, str) and compile_report_ref.strip()
        else target_compile_report_path
    )
    return {
        "status": "hydrated" if hydrated_files else "current",
        "source_root": str(source_root),
        "source_compile_report_path": str(source_compile_report_path) if source_compile_report_path else None,
        "source_compile_report_status": source_compile_report_status,
        "compile_report_path": str(resolved_compile_report.resolve()),
        "hydrated_files": [
            _relpath_from_paper(path, paper_root=resolved_paper_root)
            for path in sorted(set(hydrated_files))
        ],
    }


__all__ = [
    "hydrate_submission_package_sources_from_current_body",
]
