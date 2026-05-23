from __future__ import annotations

import argparse
import hashlib
from importlib import import_module
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import journal_package as journal_package_controller, study_delivery_sync, submission_minimal
from med_autoscience.journal_requirements import (
    describe_journal_submission_package,
    journal_requirements_json_path,
    load_journal_requirements,
    slugify_journal_name,
)
from med_autoscience.policies import publication_gate as publication_gate_policy
from med_autoscience.policies.medical_reporting_checklist import REPORTING_CHECKLIST_BLOCKER_KEYS
from med_autoscience.runtime_protocol import (
    paper_artifacts,
    quest_state,
    resolve_paper_root_context,
    user_message,
)
from med_autoscience.runtime_protocol import report_store as runtime_protocol_report_store
from med_autoscience.controllers.submission_package_layout import resolve_submission_manifest_path

from .blocking_artifact_refs import build_blocking_artifact_refs
from .deterministic_quality_gates import build_deterministic_quality_gate_projection_from_state
from .discovery_and_drift import (
    PUBLICATION_SUPERVISOR_KEYS,
    _NON_SCIENTIFIC_HANDOFF_BLOCKING_ITEM_KEYS,
    _BUNDLE_STAGE_ONLY_BLOCKERS,
    _MEDICAL_PUBLICATION_SURFACE_REVIEWER_FIRST_BLOCKERS,
    _MEDICAL_PUBLICATION_SURFACE_CLAIM_EVIDENCE_BLOCKERS,
    _MEDICAL_PUBLICATION_SURFACE_SUBMISSION_HARDENING_BLOCKERS,
    _MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_RECOMMENDATIONS,
    _MEDICAL_PUBLICATION_SURFACE_ROUTE_BACK_NOTE_CLAUSES,
    _DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES,
    _append_unique,
    GateState,
    utc_now,
)
from .discovery_and_drift import (
    load_json,
    dump_json,
    _non_empty_text,
    _normalized_blocker_set,
    find_latest,
    find_latest_parseable_json,
    _normalize_medical_surface_paper_root,
    _medical_surface_report_matches_paper_root,
    _medical_surface_report_matches_study_root,
    find_latest_gate_report,
    find_latest_medical_publication_surface_report,
    _write_drift_text_surfaces,
)
from .discovery_and_drift import (
    detect_write_drift,
    _paper_line_open_supplementary_count,
    _paper_line_recommended_action,
    _paper_line_blocking_reasons,
    _paper_line_requires_required_supplementary,
    _medical_publication_surface_named_blockers,
    _medical_publication_surface_expectation_gaps,
    _medical_publication_surface_route_back_recommendation,
    _medical_publication_surface_stage_note,
    _dedupe_resolved_paths,
    _bundle_manifest_branch,
    _paper_line_branch,
)
from .discovery_and_drift import (
    _projected_bundle_manifest_path,
    _resolve_worktree_bundle_manifest_by_branch,
    resolve_bundle_authority_paper_root,
    resolve_submission_checklist_path,
    load_submission_checklist,
    resolve_submission_minimal_manifest,
    resolve_submission_minimal_output_paths,
    classify_deliverables,
    resolve_paper_root,
    collect_manuscript_surface_paths,
    detect_manuscript_terminology_violations,
    _load_catalog_entries,
)
from .discovery_and_drift import (
    active_manuscript_figure_count,
    active_main_text_figure_count,
    infer_submission_publication_profile,
    collect_submission_surface_qc_failures,
    gate_allows_write,
)



def resolve_write_drift_stdout_path(
    *,
    quest_root: Path,
    runtime_state: dict[str, Any],
    main_result: dict[str, Any] | None,
) -> Path | None:
    main_result_run_id = _non_empty_text((main_result or {}).get("run_id"))
    active_run_id = _non_empty_text(runtime_state.get("active_run_id"))
    if main_result is not None and (main_result_run_id is None or active_run_id != main_result_run_id):
        return None
    return quest_state.resolve_active_stdout_path(quest_root=quest_root, runtime_state=runtime_state)


def medical_publication_surface_report_current(
    *,
    latest_surface_path: Path | None,
    anchor_path: Path,
) -> bool:
    if latest_surface_path is None or not latest_surface_path.exists():
        return False
    return latest_surface_path.stat().st_mtime >= anchor_path.stat().st_mtime


def medical_publication_surface_currentness_anchor(state: GateState) -> Path:
    if state.anchor_kind == "paper_bundle" and state.paper_root is not None:
        authoritative_bundle_manifest = state.paper_root / "paper_bundle_manifest.json"
        if authoritative_bundle_manifest.exists():
            return authoritative_bundle_manifest
    return state.anchor_path


def resolve_compile_report_path(
    *,
    paper_bundle_manifest_path: Path | None,
    paper_bundle_manifest: dict[str, Any] | None,
) -> Path | None:
    if paper_bundle_manifest_path is None or paper_bundle_manifest is None:
        return None
    paper_root = paper_bundle_manifest_path.resolve().parent
    worktree_root = paper_root.parent
    candidates = [
        str(paper_bundle_manifest.get("compile_report_path") or "").strip(),
        str((paper_bundle_manifest.get("bundle_inputs") or {}).get("compile_report_path") or "").strip(),
        "paper/build/compile_report.json",
        "paper/compile_report.json",
        "paper/submission_minimal/compile_report.json",
        "build/compile_report.json",
        "compile_report.json",
        "submission_minimal/compile_report.json",
    ]
    candidate_roots = (worktree_root, paper_root)
    seen: set[Path] = set()
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        raw_paths = [path] if path.is_absolute() else [root / path for root in candidate_roots]
        for raw_path in raw_paths:
            try:
                resolved = raw_path.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                if resolved.exists():
                    return resolved
            except OSError:
                continue
    return None


def _resolve_gate_study_root(*, paper_root: Path | None) -> Path | None:
    if paper_root is None:
        return None
    try:
        context = study_delivery_sync._resolve_delivery_context(paper_root.resolve())
    except (FileNotFoundError, ValueError):
        return None
    return Path(context["study_root"]).expanduser().resolve()


def resolve_primary_journal_target(*, paper_root: Path | None) -> dict[str, Any] | None:
    if paper_root is None:
        return None
    payload = load_json(paper_root / "submission_targets.resolved.json", default=None)
    if not isinstance(payload, dict):
        return None
    primary = payload.get("primary_target")
    if not isinstance(primary, dict):
        return None
    journal_name = _non_empty_text(primary.get("journal_name"))
    official_guidelines_url = _non_empty_text(primary.get("official_guidelines_url"))
    if journal_name is None and official_guidelines_url is None:
        return None
    journal_slug = _non_empty_text(primary.get("journal_slug"))
    if journal_slug is None and journal_name is not None:
        journal_slug = slugify_journal_name(journal_name)
    if journal_slug is None:
        return None
    return {
        "journal_name": journal_name,
        "journal_slug": journal_slug,
        "official_guidelines_url": official_guidelines_url,
        "publication_profile": _non_empty_text(primary.get("exporter_profile")),
        "citation_style": _non_empty_text(primary.get("citation_style")),
        "package_required": bool(primary.get("package_required", True)),
        "resolution_status": _non_empty_text(primary.get("resolution_status")),
    }


def _resolved_optional_path(value: object) -> Path | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return Path(text).expanduser().resolve()


def _resolve_current_journal_source_manifest_path(
    *,
    paper_root: Path | None,
    primary_target: dict[str, Any] | None,
) -> Path | None:
    if paper_root is None or primary_target is None:
        return None
    publication_profile = (
        _non_empty_text(primary_target.get("publication_profile"))
        or submission_minimal.GENERAL_MEDICAL_JOURNAL_PROFILE
    )
    try:
        source_root = study_delivery_sync.build_submission_source_root(
            paper_root=paper_root,
            publication_profile=publication_profile,
        )
    except ValueError:
        return None
    manifest_path = resolve_submission_manifest_path(source_root)
    return manifest_path.resolve() if manifest_path.exists() else None


def resolve_journal_requirement_state(*, paper_root: Path | None) -> dict[str, Any]:
    study_root = _resolve_gate_study_root(paper_root=paper_root)
    primary_target = resolve_primary_journal_target(paper_root=paper_root)
    if study_root is None or primary_target is None or primary_target["package_required"] is not True:
        return {
            "status": "not_applicable",
            "study_root": str(study_root) if study_root is not None else None,
            "requirements_path": None,
        }
    requirements = load_journal_requirements(
        study_root=study_root,
        journal_slug=str(primary_target["journal_slug"]),
    )
    requirements_path = journal_requirements_json_path(
        study_root=study_root,
        journal_slug=str(primary_target["journal_slug"]),
    )
    return {
        "status": "resolved" if requirements is not None else "missing",
        "study_root": str(study_root),
        "requirements_path": str(requirements_path),
    }


def resolve_journal_package_state(*, paper_root: Path | None) -> dict[str, Any]:
    study_root = _resolve_gate_study_root(paper_root=paper_root)
    primary_target = resolve_primary_journal_target(paper_root=paper_root)
    if study_root is None or primary_target is None or primary_target["package_required"] is not True:
        return {
            "status": "not_applicable",
            "package_root": None,
            "submission_manifest_path": None,
            "zip_path": None,
        }
    package_state = describe_journal_submission_package(
        study_root=study_root,
        journal_slug=str(primary_target["journal_slug"]),
    )
    current_source_manifest_path = _resolve_current_journal_source_manifest_path(
        paper_root=paper_root,
        primary_target=primary_target,
    )
    if package_state["status"] != "current":
        return {
            **package_state,
            "stale_reason": None,
            "current_source_submission_manifest_path": (
                str(current_source_manifest_path) if current_source_manifest_path is not None else None
            ),
        }
    package_manifest_path = _resolved_optional_path(package_state.get("submission_manifest_path"))
    try:
        package_manifest = load_json(package_manifest_path, default=None) if package_manifest_path is not None else None
    except json.JSONDecodeError:
        return {
            **package_state,
            "status": "incomplete",
            "stale_reason": "journal_package_manifest_invalid",
            "current_source_submission_manifest_path": (
                str(current_source_manifest_path) if current_source_manifest_path is not None else None
            ),
        }
    recorded_source_manifest_path = _resolved_optional_path(
        (package_manifest or {}).get("source_submission_manifest_path")
    )
    recorded_source_root = _resolved_optional_path((package_manifest or {}).get("source_submission_root"))
    current_source_root = current_source_manifest_path.parent if current_source_manifest_path is not None else None
    status = str(package_state["status"])
    stale_reason: str | None = None
    if current_source_manifest_path is not None:
        if (
            recorded_source_manifest_path is not None
            and recorded_source_manifest_path != current_source_manifest_path
        ):
            status = "stale_source_mismatch"
            stale_reason = "source_submission_manifest_mismatch"
        elif recorded_source_root is not None and current_source_root is not None and recorded_source_root != current_source_root:
            status = "stale_source_mismatch"
            stale_reason = "source_submission_root_mismatch"
        elif package_manifest_path is not None and package_manifest_path.exists():
            if package_manifest_path.stat().st_mtime < current_source_manifest_path.stat().st_mtime:
                status = "stale_source_changed"
                stale_reason = "source_submission_manifest_newer"
    return {
        **package_state,
        "status": status,
        "stale_reason": stale_reason,
        "current_source_submission_manifest_path": (
            str(current_source_manifest_path) if current_source_manifest_path is not None else None
        ),
    }


def resolve_primary_anchor(
    *,
    quest_root: Path,
    paper_bundle_manifest_path: Path | None,
    paper_bundle_manifest: dict[str, Any] | None,
) -> tuple[str, Path, Path | None, dict[str, Any] | None]:
    try:
        main_result_path = quest_state.find_latest_main_result_path(quest_root)
    except FileNotFoundError:
        main_result_path = None
    if main_result_path is not None:
        return "main_result", main_result_path, main_result_path, load_json(main_result_path)
    if paper_bundle_manifest_path is not None and paper_bundle_manifest is not None:
        return "paper_bundle", paper_bundle_manifest_path, None, None
    return "missing", quest_root, None, None


def build_gate_state(quest_root: Path) -> GateState:
    runtime_state = quest_state.load_runtime_state(quest_root)
    paper_bundle_manifest_path = paper_artifacts.resolve_paper_bundle_manifest(quest_root)
    paper_bundle_manifest = load_json(paper_bundle_manifest_path) if paper_bundle_manifest_path else None
    projected_paper_line_state_path = (
        paper_bundle_manifest_path.parent / "paper_line_state.json"
        if paper_bundle_manifest_path is not None
        else None
    )
    projected_paper_line_state = (
        load_json(projected_paper_line_state_path)
        if projected_paper_line_state_path is not None and projected_paper_line_state_path.exists()
        else None
    )
    anchor_kind, anchor_path, main_result_path, main_result = resolve_primary_anchor(
        quest_root=quest_root,
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_bundle_manifest=paper_bundle_manifest,
    )
    paper_root = resolve_paper_root(
        quest_root=quest_root,
        main_result=main_result,
        paper_line_state=projected_paper_line_state,
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_bundle_manifest=paper_bundle_manifest,
    )
    study_root = _resolve_gate_study_root(paper_root=paper_root)
    charter_contract_linkage = study_delivery_sync.build_charter_contract_linkage(
        study_root=study_root,
        evidence_ledger_path=None,
        review_ledger_path=None,
    )
    authoritative_paper_line_state_path = paper_root / "paper_line_state.json" if paper_root is not None else None
    authoritative_paper_line_state = (
        load_json(authoritative_paper_line_state_path)
        if authoritative_paper_line_state_path is not None and authoritative_paper_line_state_path.exists()
        else None
    )
    paper_line_state_path = authoritative_paper_line_state_path or projected_paper_line_state_path
    paper_line_state = (
        authoritative_paper_line_state
        if authoritative_paper_line_state is not None
        else projected_paper_line_state
    )
    compile_report_path = resolve_compile_report_path(
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_bundle_manifest=paper_bundle_manifest,
    )
    compile_report = load_json(compile_report_path) if compile_report_path else None
    latest_gate_path = find_latest_gate_report(quest_root)
    latest_gate = load_json(latest_gate_path) if latest_gate_path else None
    latest_medical_publication_surface_path = find_latest_medical_publication_surface_report(
        quest_root,
        paper_root=paper_root,
        study_root=study_root,
    )
    latest_medical_publication_surface = (
        load_json(latest_medical_publication_surface_path) if latest_medical_publication_surface_path else None
    )
    stdout_path = resolve_write_drift_stdout_path(
        quest_root=quest_root,
        runtime_state=runtime_state,
        main_result=main_result if anchor_kind == "main_result" else None,
    )
    recent_lines = quest_state.read_recent_stdout_lines(stdout_path)
    if main_result_path is not None and main_result is not None:
        present_deliverables, missing_deliverables = classify_deliverables(main_result_path, main_result)
    else:
        present_deliverables, missing_deliverables = [], []
    submission_checklist_path = resolve_submission_checklist_path(paper_root=paper_root)
    submission_checklist = load_submission_checklist(paper_root=paper_root)
    submission_minimal_manifest_path = resolve_submission_minimal_manifest(paper_root=paper_root)
    submission_minimal_manifest = (
        load_json(submission_minimal_manifest_path) if submission_minimal_manifest_path else None
    )
    submission_minimal_docx_path, submission_minimal_pdf_path = resolve_submission_minimal_output_paths(
        paper_root=paper_root,
        submission_minimal_manifest=submission_minimal_manifest,
    )
    submission_surface_qc_failures = collect_submission_surface_qc_failures(
        submission_minimal_manifest,
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_root=paper_root,
    )
    archived_submission_surface_roots = (
        [str(path) for path in paper_artifacts.resolve_archived_submission_surface_roots(paper_root)]
        if paper_root is not None
        else []
    )
    unmanaged_submission_surface_roots = (
        [str(path) for path in paper_artifacts.find_unmanaged_submission_surface_roots(paper_root)]
        if paper_root is not None
        else []
    )
    manuscript_terminology_violations = detect_manuscript_terminology_violations(paper_root)
    study_delivery = (
        study_delivery_sync.describe_submission_delivery(paper_root=paper_root)
        if paper_root is not None and study_delivery_sync.can_sync_study_delivery(paper_root=paper_root)
        else None
    )
    draft_handoff_delivery = (
        study_delivery_sync.describe_draft_handoff_delivery(paper_root=paper_root)
        if paper_root is not None and study_delivery_sync.can_sync_study_delivery(paper_root=paper_root)
        else None
    )
    return GateState(
        quest_root=quest_root,
        runtime_state=runtime_state,
        study_root=study_root,
        charter_contract_linkage=charter_contract_linkage,
        anchor_kind=anchor_kind,
        anchor_path=anchor_path,
        paper_line_state_path=paper_line_state_path if paper_line_state is not None else None,
        paper_line_state=paper_line_state,
        main_result_path=main_result_path,
        main_result=main_result,
        paper_root=paper_root,
        compile_report_path=compile_report_path,
        compile_report=compile_report,
        latest_gate_path=latest_gate_path,
        latest_gate=latest_gate,
        latest_medical_publication_surface_path=latest_medical_publication_surface_path,
        latest_medical_publication_surface=latest_medical_publication_surface,
        active_run_stdout_path=stdout_path,
        recent_stdout_lines=recent_lines,
        write_drift_detected=detect_write_drift(recent_lines),
        missing_deliverables=missing_deliverables,
        present_deliverables=present_deliverables,
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        paper_bundle_manifest=paper_bundle_manifest,
        submission_checklist_path=submission_checklist_path,
        submission_checklist=submission_checklist,
        submission_minimal_manifest_path=submission_minimal_manifest_path,
        submission_minimal_manifest=submission_minimal_manifest,
        submission_minimal_docx_present=bool(submission_minimal_docx_path and submission_minimal_docx_path.exists()),
        submission_minimal_pdf_present=bool(submission_minimal_pdf_path and submission_minimal_pdf_path.exists()),
        submission_surface_qc_failures=submission_surface_qc_failures,
        archived_submission_surface_roots=archived_submission_surface_roots,
        unmanaged_submission_surface_roots=unmanaged_submission_surface_roots,
        manuscript_terminology_violations=manuscript_terminology_violations,
        study_delivery=study_delivery,
        draft_handoff_delivery=draft_handoff_delivery,
    )




__all__ = [name for name in globals() if not name.startswith("__")]
