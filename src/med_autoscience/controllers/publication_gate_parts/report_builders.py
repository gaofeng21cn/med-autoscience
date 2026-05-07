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



from .state_resolvers import (
    medical_publication_surface_currentness_anchor,
    medical_publication_surface_report_current,
    resolve_journal_package_state,
    resolve_journal_requirement_state,
    resolve_primary_journal_target,
)
def _publication_gate_fingerprint(
    *,
    blockers: list[str],
    authority_source_signature: str | None,
    evaluated_source_signature: str | None,
    study_delivery_source_signature: str | None,
) -> str:
    payload = {
        "blockers": sorted(str(item or "").strip() for item in blockers if str(item or "").strip()),
        "authority_source_signature": authority_source_signature,
        "evaluated_source_signature": evaluated_source_signature,
        "study_delivery_source_signature": study_delivery_source_signature,
    }
    digest = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return f"publication-gate::{digest}"


def _build_blocker_taxonomy(
    *,
    blockers: list[str],
    medical_publication_surface_named_blockers: list[str],
    medical_publication_surface_raw_blockers: list[str],
    non_scientific_handoff_gaps: list[str],
) -> dict[str, list[str]]:
    science_reporting_blockers: list[str] = []
    bundle_package_blockers: list[str] = []
    for blocker in blockers:
        if blocker in _BUNDLE_STAGE_ONLY_BLOCKERS:
            _append_unique(bundle_package_blockers, blocker)
        else:
            _append_unique(science_reporting_blockers, blocker)
    for blocker in medical_publication_surface_named_blockers:
        _append_unique(science_reporting_blockers, blocker)
    for blocker in medical_publication_surface_raw_blockers:
        if blocker in REPORTING_CHECKLIST_BLOCKER_KEYS:
            _append_unique(science_reporting_blockers, blocker)
    return {
        "science_reporting_blockers": science_reporting_blockers,
        "bundle_package_blockers": bundle_package_blockers,
        "human_metadata_admin_todos": list(non_scientific_handoff_gaps),
    }


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
    from .supervisor_and_cli import build_publication_supervisor_state

    supervisor_state = build_publication_supervisor_state(
        anchor_kind=state.anchor_kind,
        allow_write=allow_write,
        blockers=blockers,
        medical_publication_surface_named_blockers=medical_publication_surface_named_blockers,
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
    medical_publication_surface_raw_blockers = list((state.latest_medical_publication_surface or {}).get("blockers") or [])
    blocker_taxonomy = _build_blocker_taxonomy(
        blockers=blockers,
        medical_publication_surface_named_blockers=medical_publication_surface_named_blockers,
        medical_publication_surface_raw_blockers=medical_publication_surface_raw_blockers,
        non_scientific_handoff_gaps=non_scientific_handoff_gaps,
    )
    publication_reporting_checklist = (state.latest_medical_publication_surface or {}).get("structured_reporting_checklist")
    if not isinstance(publication_reporting_checklist, dict):
        publication_reporting_checklist = None
    controller_stage_note = _medical_publication_surface_stage_note(
        base_note=str(supervisor_state["controller_stage_note"]),
        named_blockers=medical_publication_surface_named_blockers,
        route_back_recommendation=medical_publication_surface_route_back_recommendation,
    )
    submission_minimal_evaluated_source_signature = _non_empty_text(
        submission_minimal_authority.get("source_signature")
    )
    submission_minimal_authority_source_signature = _non_empty_text(
        submission_minimal_authority.get("recorded_source_signature")
    )
    study_delivery_source_signature = _non_empty_text(study_delivery.get("source_signature")) or _non_empty_text(
        study_delivery.get("delivery_source_signature")
    )
    blocking_artifact_refs = build_blocking_artifact_refs(
        blockers=blockers,
        paper_root=state.paper_root,
        submission_minimal_manifest_path=state.submission_minimal_manifest_path,
        submission_minimal_authority_stale_reason=submission_minimal_authority_stale_reason,
        study_delivery=study_delivery,
        medical_publication_surface_named_blockers=medical_publication_surface_named_blockers,
        submission_surface_qc_failures=list(state.submission_surface_qc_failures),
    )
    gate_fingerprint = _publication_gate_fingerprint(
        blockers=blockers,
        authority_source_signature=submission_minimal_authority_source_signature,
        evaluated_source_signature=submission_minimal_evaluated_source_signature,
        study_delivery_source_signature=study_delivery_source_signature,
    )
    deterministic_quality_gates = build_deterministic_quality_gate_projection_from_state(
        state=state,
        blockers=blockers,
        medical_publication_surface_named_blockers=medical_publication_surface_named_blockers,
        publication_reporting_checklist=publication_reporting_checklist,
        blocking_artifact_refs=blocking_artifact_refs,
        active_figure_count=active_figure_count,
        prebundle_display_advisories=prebundle_display_advisories,
    )

    return {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": utc_now(),
        "gate_fingerprint": gate_fingerprint,
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
        "blocker_taxonomy": blocker_taxonomy,
        "publication_reporting_checklist": publication_reporting_checklist,
        "closure_bundle_ready": closure_bundle_ready,
        "submission_minimal_manifest_path": (
            str(state.submission_minimal_manifest_path) if state.submission_minimal_manifest_path else None
        ),
        "submission_minimal_present": state.submission_minimal_manifest is not None,
        "submission_minimal_docx_present": state.submission_minimal_docx_present,
        "submission_minimal_pdf_present": state.submission_minimal_pdf_present,
        "submission_minimal_authority_status": submission_minimal_authority_status,
        "submission_minimal_authority_stale_reason": submission_minimal_authority_stale_reason,
        "submission_minimal_evaluated_source_signature": submission_minimal_evaluated_source_signature,
        "submission_minimal_authority_source_signature": submission_minimal_authority_source_signature,
        "authority_source_signature": submission_minimal_authority_source_signature,
        "study_delivery_status": study_delivery_status,
        "study_delivery_stale_reason": _non_empty_text(study_delivery.get("stale_reason")),
        "study_delivery_source_signature": study_delivery_source_signature,
        "study_delivery_evaluated_source_signature": _non_empty_text(study_delivery.get("evaluated_source_signature")),
        "study_delivery_authority_source_signature": _non_empty_text(study_delivery.get("authority_source_signature")),
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
        "deterministic_quality_gates": deterministic_quality_gates,
        "blocking_artifact_refs": blocking_artifact_refs,
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


def _bundle_stage_is_on_critical_path(
    *,
    blockers: list[str],
    medical_publication_surface_named_blockers: list[str] | None = None,
) -> bool:
    normalized_blockers = {str(item or "").strip() for item in blockers if str(item or "").strip()}
    named_blockers = {
        str(item or "").strip()
        for item in (medical_publication_surface_named_blockers or [])
        if str(item or "").strip()
    }
    bundle_stage_blockers = set(_BUNDLE_STAGE_ONLY_BLOCKERS) | {"submission_hardening_incomplete"}
    if "medical_publication_surface_blocked" in normalized_blockers:
        if named_blockers != {"submission_hardening_incomplete"}:
            return False
        normalized_blockers = normalized_blockers - {"medical_publication_surface_blocked"}
        if "submission_hardening_incomplete" not in normalized_blockers:
            return False
    return bool(normalized_blockers) and normalized_blockers.issubset(bundle_stage_blockers)


__all__ = [name for name in globals() if not name.startswith("__")]
