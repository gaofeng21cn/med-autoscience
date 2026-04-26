from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from med_autoscience.controllers import gate_clearing_batch_submission


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            items.append(text)
    return items


def _gate_blockers(gate_report: dict[str, Any]) -> set[str]:
    return {
        str(item or "").strip()
        for item in (gate_report.get("blockers") or [])
        if str(item or "").strip()
    }


def catalog_asset_fingerprints(
    *,
    workspace_root: Path,
    catalog_payload: dict[str, Any],
    item_key: str,
    resolve_source_paths: Callable[[dict[str, Any]], list[str]],
    submission_minimal_controller: Any,
    path_fingerprint: Callable[[Path | None], dict[str, Any] | None],
    limit: int = 128,
) -> list[dict[str, Any]]:
    items = catalog_payload.get(item_key)
    if not isinstance(items, list):
        return []
    fingerprints: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        for raw_path in resolve_source_paths(item):
            normalized = str(raw_path or "").strip()
            if not normalized:
                continue
            resolved = submission_minimal_controller.resolve_relpath(workspace_root, normalized).expanduser().resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            fingerprint = path_fingerprint(resolved)
            if fingerprint is not None:
                fingerprints.append(fingerprint)
            if len(fingerprints) >= limit:
                return fingerprints
    return fingerprints


def submission_minimal_fingerprint_payload(
    *,
    paper_root: Path,
    gate_report: dict[str, Any],
    profile: Any | None,
    submission_minimal_controller: Any,
    path_fingerprint: Callable[[Path | None], dict[str, Any] | None],
    path_fingerprints: Callable[..., list[dict[str, Any]]],
) -> dict[str, Any]:
    bundle_manifest_path = paper_root / "paper_bundle_manifest.json"
    payload: dict[str, Any] = {
        "unit_id": "create_submission_minimal_package",
        "current_required_action": _non_empty_text(gate_report.get("current_required_action")),
        "gate_blockers": sorted(_gate_blockers(gate_report)),
        "paper_bundle_manifest": path_fingerprint(bundle_manifest_path),
        "display_pack_lock": path_fingerprint(paper_root / "build" / "display_pack_lock.json"),
    }
    if profile is not None:
        payload["requested_publication_profile"] = profile.default_publication_profile
        payload["requested_citation_style"] = profile.default_citation_style
    workspace_root = submission_minimal_controller.workspace_root_from_paper_root(paper_root)
    if not bundle_manifest_path.exists():
        return payload
    try:
        bundle_manifest = submission_minimal_controller.load_json(bundle_manifest_path)
    except Exception as exc:
        payload["bundle_manifest_error"] = str(exc)
        return payload

    try:
        requested_publication_profile = (
            profile.default_publication_profile
            if profile is not None
            else submission_minimal_controller.GENERAL_MEDICAL_JOURNAL_PROFILE
        )
        requested_citation_style = profile.default_citation_style if profile is not None else "auto"
        profile_config = submission_minimal_controller.resolve_publication_profile_config(
            publication_profile=requested_publication_profile,
            citation_style=requested_citation_style,
        )
        payload["resolved_publication_profile"] = profile_config.publication_profile
        payload["profile_artifacts"] = path_fingerprints(
            profile_config.csl_path,
            profile_config.reference_doc_path,
            profile_config.supplementary_reference_doc_path,
        )
    except Exception as exc:
        payload["profile_config_error"] = str(exc)
        return payload

    try:
        compile_report_path = submission_minimal_controller.resolve_relpath(
            workspace_root,
            submission_minimal_controller.resolve_bundle_input_path(
                bundle_manifest=bundle_manifest,
                key="compile_report_path",
            ),
        )
        figure_catalog_path = submission_minimal_controller.resolve_relpath(
            workspace_root,
            submission_minimal_controller.resolve_bundle_input_path(
                bundle_manifest=bundle_manifest,
                key="figure_catalog_path",
                fallback="paper/figures/figure_catalog.json",
            ),
        )
        table_catalog_path = submission_minimal_controller.resolve_relpath(
            workspace_root,
            submission_minimal_controller.resolve_bundle_input_path(
                bundle_manifest=bundle_manifest,
                key="table_catalog_path",
                fallback="paper/tables/table_catalog.json",
            ),
        )
    except Exception as exc:
        payload["bundle_inputs_error"] = str(exc)
        return payload
    payload["compile_report"] = path_fingerprint(compile_report_path)
    payload["figure_catalog"] = path_fingerprint(figure_catalog_path)
    payload["table_catalog"] = path_fingerprint(table_catalog_path)

    compile_report: dict[str, Any] = {}
    figure_catalog: dict[str, Any] = {}
    table_catalog: dict[str, Any] = {}
    try:
        compile_report = submission_minimal_controller.load_json(compile_report_path)
    except Exception as exc:
        payload["compile_report_error"] = str(exc)
    try:
        figure_catalog = submission_minimal_controller.load_json(figure_catalog_path)
    except Exception as exc:
        payload["figure_catalog_error"] = str(exc)
    try:
        table_catalog = submission_minimal_controller.load_json(table_catalog_path)
    except Exception as exc:
        payload["table_catalog_error"] = str(exc)

    try:
        submission_root = submission_minimal_controller.resolve_output_root(
            paper_root=paper_root,
            publication_profile=profile_config.publication_profile,
        )
        payload["submission_root"] = path_fingerprint(submission_root)
        payload["submission_outputs"] = path_fingerprints(
            submission_root / "manuscript.docx",
            submission_root / "paper.pdf",
            submission_root / "submission_manifest.json",
            submission_root / "README.md",
        )
        excluded_compiled_source_roots = (
            submission_minimal_controller.resolve_submission_compiled_source_excluded_roots(
                paper_root=paper_root,
                workspace_root=workspace_root,
                submission_root=submission_root,
                bundle_manifest=bundle_manifest,
                compile_report=compile_report,
                exclude_live_submission_root_for_markdown_candidates=True,
            )
        )
        compiled_markdown_path = submission_minimal_controller.resolve_compiled_markdown_path(
            workspace_root=workspace_root,
            bundle_manifest=bundle_manifest,
            compile_report=compile_report,
            excluded_roots=excluded_compiled_source_roots,
        )
        compiled_pdf_path = submission_minimal_controller.resolve_compiled_pdf_path(
            workspace_root=workspace_root,
            bundle_manifest=bundle_manifest,
            compile_report=compile_report,
            excluded_roots=excluded_compiled_source_roots,
        )
        payload["compiled_markdown"] = path_fingerprint(compiled_markdown_path)
        payload["compiled_pdf"] = path_fingerprint(compiled_pdf_path)
    except Exception as exc:
        payload["compiled_surface_error"] = str(exc)

    payload["figure_assets"] = catalog_asset_fingerprints(
        workspace_root=workspace_root,
        catalog_payload=figure_catalog,
        item_key="figures",
        resolve_source_paths=submission_minimal_controller.resolve_figure_source_paths,
        submission_minimal_controller=submission_minimal_controller,
        path_fingerprint=path_fingerprint,
    )
    payload["table_assets"] = catalog_asset_fingerprints(
        workspace_root=workspace_root,
        catalog_payload=table_catalog,
        item_key="tables",
        resolve_source_paths=submission_minimal_controller.resolve_table_source_paths,
        submission_minimal_controller=submission_minimal_controller,
        path_fingerprint=path_fingerprint,
    )
    return payload


def repair_unit_fingerprint(
    *,
    unit_id: str,
    paper_root: Path,
    gate_report: dict[str, Any],
    profile: Any | None = None,
    submission_minimal_controller: Any,
    path_fingerprint: Callable[[Path | None], dict[str, Any] | None],
    path_fingerprints: Callable[..., list[dict[str, Any]]],
    globbed_path_fingerprints: Callable[..., list[dict[str, Any]]],
) -> str | None:
    payload: dict[str, Any] | None
    if unit_id == "materialize_display_surface":
        payload = {
            "unit_id": unit_id,
            "medical_publication_surface_status": _non_empty_text(
                gate_report.get("medical_publication_surface_status")
            ),
            "medical_publication_surface_named_blockers": sorted(
                str(item or "").strip()
                for item in (gate_report.get("medical_publication_surface_named_blockers") or [])
                if str(item or "").strip()
            ),
            "display_registry": path_fingerprint(paper_root / "display_registry.json"),
            "manuscript_assets": globbed_path_fingerprints(
                paper_root,
                "figures/*.json",
                "tables/*.json",
                "figures/*.csv",
                "tables/*.csv",
                "results/*.json",
            ),
        }
    elif unit_id == "workspace_display_repair_script":
        payload = {
            "unit_id": unit_id,
            "medical_publication_surface_status": _non_empty_text(
                gate_report.get("medical_publication_surface_status")
            ),
            "medical_publication_surface_named_blockers": sorted(
                str(item or "").strip()
                for item in (gate_report.get("medical_publication_surface_named_blockers") or [])
                if str(item or "").strip()
            ),
            "script": path_fingerprint(paper_root / "build" / "generate_display_exports.py"),
            "display_registry": path_fingerprint(paper_root / "display_registry.json"),
        }
    elif unit_id == "sync_submission_minimal_delivery":
        payload = {
            "unit_id": unit_id,
            "study_delivery_status": gate_clearing_batch_submission.study_delivery_status(gate_report),
            "study_delivery_stale_reason": gate_clearing_batch_submission.study_delivery_stale_reason(gate_report),
            "study_delivery_manifest_path": _non_empty_text(gate_report.get("study_delivery_manifest_path")),
            "study_delivery_current_package_root": _non_empty_text(
                gate_report.get("study_delivery_current_package_root")
            ),
            "study_delivery_current_package_zip": _non_empty_text(
                gate_report.get("study_delivery_current_package_zip")
            ),
            "study_delivery_missing_source_paths": _string_list(gate_report.get("study_delivery_missing_source_paths")),
            "submission_minimal_manifest": path_fingerprint(
                paper_root / "submission_minimal" / "submission_manifest.json"
            ),
            "submission_minimal_assets": globbed_path_fingerprints(
                paper_root / "submission_minimal",
                "*.docx",
                "*.pdf",
                "*.json",
                "*.zip",
            ),
        }
    elif unit_id == "create_submission_minimal_package":
        payload = submission_minimal_fingerprint_payload(
            paper_root=paper_root,
            gate_report=gate_report,
            profile=profile,
            submission_minimal_controller=submission_minimal_controller,
            path_fingerprint=path_fingerprint,
            path_fingerprints=path_fingerprints,
        )
    else:
        payload = None
    if payload is None:
        return None
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
