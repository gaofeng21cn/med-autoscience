from __future__ import annotations

import argparse
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
from med_autoscience.runtime_protocol import (
    paper_artifacts,
    quest_state,
    resolve_paper_root_context,
    user_message,
)
from med_autoscience.runtime_protocol import report_store as runtime_protocol_report_store

from .chunk_01 import (
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
from .chunk_01 import (
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
from .chunk_01 import (
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
from .chunk_01 import (
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
from .chunk_01 import (
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
    candidates = [
        str(paper_bundle_manifest.get("compile_report_path") or "").strip(),
        str((paper_bundle_manifest.get("bundle_inputs") or {}).get("compile_report_path") or "").strip(),
    ]
    worktree_root = paper_bundle_manifest_path.resolve().parent.parent
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if not path.is_absolute():
            path = worktree_root / path
        resolved = path.resolve()
        if resolved.exists():
            return resolved
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
        "publication_profile": _non_empty_text(primary.get("publication_profile")),
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
    manifest_path = source_root / "submission_manifest.json"
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


def build_gate_report(state: GateState) -> dict[str, Any]:
    baseline_items = (state.main_result or {}).get("baseline_comparisons", {}).get("items") or []
    primary_delta = None
    for item in baseline_items:
        if item.get("metric_id") == "roc_auc":
            primary_delta = item.get("delta")
            break
    latest_gate_up_to_date = (
        state.latest_gate_path is not None and state.latest_gate_path.stat().st_mtime >= state.anchor_path.stat().st_mtime
    )
    medical_publication_surface_current = medical_publication_surface_report_current(
        latest_surface_path=state.latest_medical_publication_surface_path,
        anchor_path=medical_publication_surface_currentness_anchor(state),
    )
    charter_contract_linkage_status = str((state.charter_contract_linkage or {}).get("status") or "").strip()
    submission_checklist_blocking_items = list(
        paper_artifacts.normalize_submission_checklist_blocking_item_keys(state.submission_checklist)
    )
    submission_checklist_handoff_ready = bool(
        isinstance(state.submission_checklist, dict) and state.submission_checklist.get("handoff_ready") is True
    )
    non_scientific_handoff_gaps = [
        item for item in submission_checklist_blocking_items if item in _NON_SCIENTIFIC_HANDOFF_BLOCKING_ITEM_KEYS
    ]
    submission_checklist_unclassified_blocking_items = [
        item for item in submission_checklist_blocking_items if item not in _NON_SCIENTIFIC_HANDOFF_BLOCKING_ITEM_KEYS
    ]
    closure_bundle_ready = submission_checklist_handoff_ready and not submission_checklist_unclassified_blocking_items
    study_delivery = state.study_delivery or {}
    study_delivery_status = str(study_delivery.get("status") or "").strip() or "not_applicable"
    draft_handoff_delivery = state.draft_handoff_delivery or {}
    submission_minimal_authority = (
        submission_minimal.describe_submission_minimal_authority(
            paper_root=state.paper_root,
            publication_profile=infer_submission_publication_profile(state.submission_minimal_manifest),
        )
        if state.paper_root is not None and isinstance(state.submission_minimal_manifest, dict)
        else {}
    )
    submission_minimal_authority_status = (
        str(submission_minimal_authority.get("status") or "").strip() or "not_applicable"
    )
    submission_minimal_authority_stale_reason = _non_empty_text(
        submission_minimal_authority.get("stale_reason")
    )
    primary_journal_target = resolve_primary_journal_target(paper_root=state.paper_root)
    journal_requirements_state = resolve_journal_requirement_state(paper_root=state.paper_root)
    journal_package_state = resolve_journal_package_state(paper_root=state.paper_root)
    paper_line_open_supplementary_count = _paper_line_open_supplementary_count(state.paper_line_state)
    paper_line_recommended_action = _paper_line_recommended_action(state.paper_line_state)
    paper_line_blocking_reasons = _paper_line_blocking_reasons(state.paper_line_state)
    active_figure_count = active_manuscript_figure_count(state.paper_root)
    prebundle_display_advisories: list[str] = []
    prebundle_display_floor_pending = False
    prebundle_display_floor_gap: int | None = None
    if active_figure_count is not None and active_figure_count < _DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES:
        prebundle_display_floor_pending = True
        prebundle_display_floor_gap = _DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES - active_figure_count
        prebundle_display_advisories.append("submission_grade_active_figure_floor_unmet")
    draft_handoff_delivery_required = bool(
        submission_checklist_handoff_ready
        and state.submission_minimal_manifest is None
        and draft_handoff_delivery.get("applicable") is True
    )
    draft_handoff_delivery_status = (
        str(draft_handoff_delivery.get("status") or "").strip() or "not_applicable"
    )
    blockers: list[str] = []
    bundle_stage_ready = bool(
        state.paper_bundle_manifest_path is not None
        and state.paper_bundle_manifest is not None
        and state.compile_report_path is not None
        and state.compile_report is not None
        and (
            closure_bundle_ready
            or (
                state.submission_minimal_manifest is not None
                and state.submission_minimal_docx_present
                and state.submission_minimal_pdf_present
            )
        )
    )
    if state.anchor_kind == "main_result":
        prior_gate_allows_write = gate_allows_write(state.latest_gate, state.latest_gate_path, state.main_result_path)
        allow_write = prior_gate_allows_write
        if not latest_gate_up_to_date:
            blockers.append("missing_post_main_publishability_gate")
        if state.missing_deliverables:
            blockers.append("missing_required_non_scalar_deliverables")
        if state.write_drift_detected and not prior_gate_allows_write:
            blockers.append("active_run_drifting_into_write_without_gate_approval")
    elif state.anchor_kind == "paper_bundle":
        allow_write = (
            state.compile_report_path is not None
            and state.compile_report is not None
            and (
                closure_bundle_ready
                or (
                    state.submission_minimal_manifest is not None
                    and state.submission_minimal_docx_present
                    and state.submission_minimal_pdf_present
                )
            )
        )
        if state.compile_report_path is None or state.compile_report is None:
            blockers.append("missing_paper_compile_report")
        if submission_checklist_handoff_ready and submission_checklist_unclassified_blocking_items:
            blockers.append("submission_checklist_contains_unclassified_blocking_items")
        if (
            not closure_bundle_ready
            and (
                state.submission_minimal_manifest is None
                or not state.submission_minimal_docx_present
                or not state.submission_minimal_pdf_present
            )
        ):
            blockers.append("missing_submission_minimal")
        if not medical_publication_surface_current and not closure_bundle_ready:
            blockers.append("missing_current_medical_publication_surface_report")
        if _paper_line_requires_required_supplementary(state.paper_line_state):
            blockers.append("paper_line_required_supplementary_pending")
        if (
            active_figure_count is not None
            and active_figure_count < _DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES
        ):
            blockers.append("submission_grade_active_figure_floor_unmet")
    else:
        allow_write = False
        blockers.append("missing_publication_anchor")

    results_summary = None
    conclusion = None
    if state.main_result is not None:
        results_summary = state.main_result.get("results_summary")
        conclusion = state.main_result.get("conclusion")
    if not results_summary:
        results_summary = (state.compile_report or {}).get("summary") or (state.paper_bundle_manifest or {}).get("summary")
    if not conclusion:
        conclusion = (state.paper_bundle_manifest or {}).get("summary") or (state.compile_report or {}).get("summary")
    if state.unmanaged_submission_surface_roots:
        blockers.append("unmanaged_submission_surface_present")
    if (
        state.submission_minimal_manifest is not None
        and submission_minimal_authority_status != "current"
    ):
        blockers.append("stale_submission_minimal_authority")
    if charter_contract_linkage_status in {"study_charter_missing", "study_charter_invalid"}:
        blockers.append(charter_contract_linkage_status)
    if study_delivery_status.startswith("stale"):
        blockers.append("stale_study_delivery_mirror")
    medical_publication_surface_status = str((state.latest_medical_publication_surface or {}).get("status") or "").strip()
    if medical_publication_surface_current:
        medical_publication_surface_expectation_gaps = _medical_publication_surface_expectation_gaps(
            state.latest_medical_publication_surface
        )
        medical_publication_surface_named_blockers = _medical_publication_surface_named_blockers(
            state.latest_medical_publication_surface
        )
        medical_publication_surface_route_back_recommendation = _medical_publication_surface_route_back_recommendation(
            medical_publication_surface_named_blockers
        )
    else:
        medical_publication_surface_expectation_gaps = []
        medical_publication_surface_named_blockers = []
        medical_publication_surface_route_back_recommendation = None
    if medical_publication_surface_current and medical_publication_surface_status and medical_publication_surface_status != "clear":
        blockers.append("medical_publication_surface_blocked")
        if medical_publication_surface_expectation_gaps:
            blockers.append("charter_expectation_closure_incomplete")
        blockers.extend(medical_publication_surface_named_blockers)
    if state.submission_surface_qc_failures:
        blockers.append("submission_surface_qc_failure_present")
    if state.manuscript_terminology_violations:
        blockers.append("forbidden_manuscript_terminology")
    if primary_journal_target is not None and primary_journal_target["package_required"] is True:
        if journal_requirements_state["status"] == "missing":
            blockers.append("missing_journal_requirements")
        elif journal_package_state["status"] != "current":
            blockers.append("missing_journal_package")
    if state.anchor_kind == "main_result":
        allow_write = not blockers
    else:
        allow_write = allow_write and not blockers
    if allow_write:
        paper_line_recommended_action = publication_gate_policy.CLEAR_RECOMMENDED_ACTION
        paper_line_blocking_reasons = []
    supervisor_state = build_publication_supervisor_state(
        anchor_kind=state.anchor_kind,
        allow_write=allow_write,
        blockers=blockers,
        bundle_stage_ready=bundle_stage_ready,
    )
    if charter_contract_linkage_status == "study_charter_missing":
        supervisor_state = {
            **supervisor_state,
            "controller_stage_note": (
                "stable study charter artifact is missing; restore the controller-owned paper-direction contract "
                "before autonomous publication work continues"
            ),
        }
    elif charter_contract_linkage_status == "study_charter_invalid":
        supervisor_state = {
            **supervisor_state,
            "controller_stage_note": (
                "stable study charter artifact is invalid; repair the controller-owned paper-direction contract "
                "before autonomous publication work continues"
            ),
        }
    controller_stage_note = _medical_publication_surface_stage_note(
        base_note=str(supervisor_state["controller_stage_note"]),
        named_blockers=medical_publication_surface_named_blockers,
        route_back_recommendation=medical_publication_surface_route_back_recommendation,
    )

    return {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": utc_now(),
        "anchor_kind": state.anchor_kind,
        "anchor_path": str(state.anchor_path),
        "quest_id": (state.main_result or {}).get("quest_id") or state.quest_root.name,
        "run_id": (
            (state.main_result or {}).get("run_id")
            or (state.paper_line_state or {}).get("paper_line_id")
            or state.runtime_state.get("active_run_id")
        ),
        "main_result_path": str(state.main_result_path) if state.main_result_path else None,
        "paper_line_state_path": str(state.paper_line_state_path) if state.paper_line_state_path else None,
        "paper_root": str(state.paper_root) if state.paper_root else None,
        "compile_report_path": str(state.compile_report_path) if state.compile_report_path else None,
        "latest_gate_path": str(state.latest_gate_path) if state.latest_gate_path else None,
        "medical_publication_surface_report_path": (
            str(state.latest_medical_publication_surface_path) if state.latest_medical_publication_surface_path else None
        ),
        "medical_publication_surface_current": medical_publication_surface_current,
        "allow_write": allow_write,
        "recommended_action": (
            publication_gate_policy.BLOCKED_RECOMMENDED_ACTION
            if blockers
            else publication_gate_policy.CLEAR_RECOMMENDED_ACTION
        ),
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "write_drift_detected": state.write_drift_detected,
        "required_non_scalar_deliverables": list(
            (state.main_result or {}).get("metric_contract", {}).get("required_non_scalar_deliverables") or []
        ),
        "present_non_scalar_deliverables": state.present_deliverables,
        "missing_non_scalar_deliverables": state.missing_deliverables,
        "paper_bundle_manifest_path": str(state.paper_bundle_manifest_path) if state.paper_bundle_manifest_path else None,
        "submission_checklist_path": str(state.submission_checklist_path) if state.submission_checklist_path else None,
        "submission_checklist_present": state.submission_checklist is not None,
        "submission_checklist_overall_status": (
            str((state.submission_checklist or {}).get("overall_status") or "").strip() or None
        ),
        "submission_checklist_handoff_ready": submission_checklist_handoff_ready,
        "submission_checklist_blocking_items": submission_checklist_blocking_items,
        "submission_checklist_unclassified_blocking_items": submission_checklist_unclassified_blocking_items,
        "non_scientific_handoff_gaps": non_scientific_handoff_gaps,
        "closure_bundle_ready": closure_bundle_ready,
        "submission_minimal_manifest_path": (
            str(state.submission_minimal_manifest_path) if state.submission_minimal_manifest_path else None
        ),
        "submission_minimal_present": state.submission_minimal_manifest is not None,
        "submission_minimal_docx_present": state.submission_minimal_docx_present,
        "submission_minimal_pdf_present": state.submission_minimal_pdf_present,
        "submission_minimal_authority_status": submission_minimal_authority_status,
        "submission_minimal_authority_stale_reason": submission_minimal_authority_stale_reason,
        "study_delivery_status": study_delivery_status,
        "study_delivery_stale_reason": _non_empty_text(study_delivery.get("stale_reason")),
        "study_delivery_manifest_path": _non_empty_text(study_delivery.get("delivery_manifest_path")),
        "study_delivery_current_package_root": _non_empty_text(study_delivery.get("current_package_root")),
        "study_delivery_current_package_zip": _non_empty_text(study_delivery.get("current_package_zip")),
        "study_delivery_missing_source_paths": list(study_delivery.get("missing_source_paths") or []),
        "primary_journal_target": primary_journal_target,
        "journal_requirements_status": journal_requirements_state["status"],
        "journal_requirements_path": journal_requirements_state.get("requirements_path"),
        "journal_requirements_study_root": journal_requirements_state.get("study_root"),
        "journal_package_status": journal_package_state["status"],
        "journal_package_stale_reason": journal_package_state.get("stale_reason"),
        "journal_package_root": journal_package_state.get("package_root"),
        "journal_package_manifest_path": journal_package_state.get("submission_manifest_path"),
        "journal_package_zip_path": journal_package_state.get("zip_path"),
        "journal_package_current_source_submission_manifest_path": journal_package_state.get(
            "current_source_submission_manifest_path"
        ),
        "draft_handoff_delivery_required": draft_handoff_delivery_required,
        "draft_handoff_delivery_status": draft_handoff_delivery_status,
        "draft_handoff_delivery_manifest_path": _non_empty_text(draft_handoff_delivery.get("delivery_manifest_path")),
        "draft_handoff_current_package_root": _non_empty_text(draft_handoff_delivery.get("current_package_root")),
        "draft_handoff_current_package_zip": _non_empty_text(draft_handoff_delivery.get("current_package_zip")),
        "paper_line_open_supplementary_count": paper_line_open_supplementary_count,
        "paper_line_recommended_action": paper_line_recommended_action,
        "paper_line_blocking_reasons": paper_line_blocking_reasons,
        "active_manuscript_figure_count": active_figure_count,
        "submission_grade_min_active_figures": _DEFAULT_SUBMISSION_GRADE_MIN_ACTIVE_FIGURES,
        "prebundle_display_floor_pending": prebundle_display_floor_pending,
        "prebundle_display_floor_gap": prebundle_display_floor_gap,
        "prebundle_display_advisories": prebundle_display_advisories,
        "medical_publication_surface_status": medical_publication_surface_status or None,
        "charter_contract_linkage": dict(state.charter_contract_linkage or {}),
        "charter_contract_linkage_status": charter_contract_linkage_status or None,
        "medical_publication_surface_expectation_gaps": medical_publication_surface_expectation_gaps,
        "medical_publication_surface_named_blockers": medical_publication_surface_named_blockers,
        "medical_publication_surface_route_back_recommendation": medical_publication_surface_route_back_recommendation,
        "submission_surface_qc_failures": list(state.submission_surface_qc_failures),
        "archived_submission_surface_roots": list(state.archived_submission_surface_roots),
        "unmanaged_submission_surface_roots": list(state.unmanaged_submission_surface_roots),
        "manuscript_terminology_violations": list(state.manuscript_terminology_violations),
        "headline_metrics": (state.main_result or {}).get("metrics_summary") or {},
        "primary_metric_delta_vs_baseline": primary_delta,
        "results_summary": results_summary,
        "conclusion": conclusion,
        "controller_note": publication_gate_policy.CONTROLLER_NOTE,
        **supervisor_state,
        "controller_stage_note": controller_stage_note,
    }


def _bundle_stage_is_on_critical_path(*, blockers: list[str]) -> bool:
    normalized_blockers = {str(item or "").strip() for item in blockers if str(item or "").strip()}
    return bool(normalized_blockers) and normalized_blockers.issubset(_BUNDLE_STAGE_ONLY_BLOCKERS)
