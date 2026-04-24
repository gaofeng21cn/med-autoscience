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
from .state_and_reports import (
    resolve_write_drift_stdout_path,
    medical_publication_surface_report_current,
    medical_publication_surface_currentness_anchor,
    resolve_compile_report_path,
    _resolve_gate_study_root,
    resolve_primary_journal_target,
    _resolved_optional_path,
    _resolve_current_journal_source_manifest_path,
    resolve_journal_requirement_state,
    resolve_journal_package_state,
    resolve_primary_anchor,
    build_gate_state,
)
from .state_and_reports import (
    build_gate_report,
    _bundle_stage_is_on_critical_path,
)



def build_publication_supervisor_state(
    *,
    anchor_kind: str,
    allow_write: bool,
    blockers: list[str],
    medical_publication_surface_named_blockers: list[str] | None = None,
    bundle_stage_ready: bool = False,
) -> dict[str, Any]:
    deferred_downstream_actions: list[str] = []
    if anchor_kind == "missing":
        return {
            "supervisor_phase": "scientific_anchor_missing",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": False,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": deferred_downstream_actions,
            "controller_stage_note": (
                "bundle suggestions are downstream-only until the publication gate allows write"
            ),
        }
    if anchor_kind == "main_result":
        if allow_write:
            if bundle_stage_ready:
                return {
                    "supervisor_phase": "bundle_stage_ready",
                    "phase_owner": "publication_gate",
                    "upstream_scientific_anchor_ready": True,
                    "bundle_tasks_downstream_only": False,
                    "current_required_action": "continue_bundle_stage",
                    "deferred_downstream_actions": deferred_downstream_actions,
                    "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
                }
            return {
                "supervisor_phase": "write_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_write_stage",
                "deferred_downstream_actions": deferred_downstream_actions,
                "controller_stage_note": "the publication gate allows write; writing-stage work is now on the critical path",
            }
        if _bundle_stage_is_on_critical_path(
            blockers=blockers,
            medical_publication_surface_named_blockers=medical_publication_surface_named_blockers,
        ):
            return {
                "supervisor_phase": "bundle_stage_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "complete_bundle_stage",
                "deferred_downstream_actions": deferred_downstream_actions,
                "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
            }
        return {
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": deferred_downstream_actions,
            "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
        }
    if allow_write:
        return {
            "supervisor_phase": "bundle_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_bundle_stage",
            "deferred_downstream_actions": deferred_downstream_actions,
            "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
        }
    if not _bundle_stage_is_on_critical_path(
        blockers=blockers,
        medical_publication_surface_named_blockers=medical_publication_surface_named_blockers,
    ):
        return {
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": deferred_downstream_actions,
            "controller_stage_note": (
                "paper bundle exists, but the active blockers still belong to the publishability surface; "
                "bundle suggestions stay downstream-only until the gate clears"
            ),
        }
    return {
        "supervisor_phase": "bundle_stage_blocked",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "bundle_tasks_downstream_only": False,
        "current_required_action": "complete_bundle_stage",
        "deferred_downstream_actions": deferred_downstream_actions,
        "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
    }


def extract_publication_supervisor_state(report: dict[str, Any]) -> dict[str, Any]:
    return {key: report[key] for key in PUBLICATION_SUPERVISOR_KEYS}


def render_gate_markdown(report: dict[str, Any]) -> str:
    blockers = report.get("blockers") or []
    medical_surface_named_blockers = report.get("medical_publication_surface_named_blockers") or []
    medical_surface_route_back_recommendation = report.get("medical_publication_surface_route_back_recommendation")
    medical_surface_expectation_gaps = report.get("medical_publication_surface_expectation_gaps") or []
    missing = report.get("missing_non_scalar_deliverables") or []
    metrics = report.get("headline_metrics") or {}
    terminology_violations = report.get("manuscript_terminology_violations") or []
    submission_surface_qc_failures = report.get("submission_surface_qc_failures") or []
    non_scientific_handoff_gaps = report.get("non_scientific_handoff_gaps") or []
    submission_checklist_unclassified = report.get("submission_checklist_unclassified_blocking_items") or []
    lines = [
        "# Publishability Gate Control Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- quest_id: `{report['quest_id']}`",
        f"- run_id: `{report['run_id']}`",
        f"- status: `{report['status']}`",
        f"- allow_write: `{str(report['allow_write']).lower()}`",
        f"- recommended_action: `{report['recommended_action']}`",
        "",
        "## Why Blocked" if blockers else "## Status",
        "",
    ]
    if blockers:
        lines.extend(f"- `{item}`" for item in blockers)
    else:
        lines.append("- No controller-level blocker detected.")
    if medical_surface_named_blockers:
        lines.extend(
            [
                "",
                "## Medical Publication Surface Route-Back",
                "",
            ]
        )
        lines.extend(f"- `{item}`" for item in medical_surface_named_blockers)
        lines.append(
            f"- route_back_recommendation: `{medical_surface_route_back_recommendation or 'return_to_publishability_gate'}`"
        )
    if medical_surface_expectation_gaps:
        lines.extend(
            [
                "",
                "## Medical Publication Surface Expectation Gaps",
                "",
            ]
        )
        for item in medical_surface_expectation_gaps:
            note_clause = f"; note={item['note']}" if item.get("note") else ""
            lines.append(
                f"- `{item['expectation_text']}` (expectation_key=`{item['expectation_key']}`, "
                f"ledger=`{item['ledger_name']}`, closure_status=`{item['closure_status']}`, "
                f"record_count=`{item['record_count']}`, "
                f"contract_json_pointer=`{item['contract_json_pointer']}`{note_clause})"
            )
    lines.extend(
        [
            "",
            "## Headline Metrics",
            "",
            f"- `roc_auc`: `{metrics.get('roc_auc')}`",
            f"- `average_precision`: `{metrics.get('average_precision')}`",
            f"- `brier_score`: `{metrics.get('brier_score')}`",
            f"- `calibration_intercept`: `{metrics.get('calibration_intercept')}`",
            f"- `calibration_slope`: `{metrics.get('calibration_slope')}`",
            "",
            "## Missing Contract Deliverables",
            "",
        ]
    )
    if missing:
        lines.extend(f"- `{item}`" for item in missing)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Paper Package Status",
            "",
            f"- `anchor_kind`: `{report.get('anchor_kind')}`",
            f"- `anchor_path`: `{report.get('anchor_path')}`",
            f"- `paper_root`: `{report.get('paper_root')}`",
            f"- `paper_bundle_manifest_path`: `{report.get('paper_bundle_manifest_path')}`",
            f"- `submission_checklist_path`: `{report.get('submission_checklist_path')}`",
            f"- `submission_checklist_handoff_ready`: `{str(report.get('submission_checklist_handoff_ready')).lower()}`",
            f"- `closure_bundle_ready`: `{str(report.get('closure_bundle_ready')).lower()}`",
            f"- `compile_report_path`: `{report.get('compile_report_path')}`",
            f"- `submission_minimal_manifest_path`: `{report.get('submission_minimal_manifest_path')}`",
            f"- `submission_minimal_present`: `{str(report.get('submission_minimal_present')).lower()}`",
            f"- `submission_minimal_docx_present`: `{str(report.get('submission_minimal_docx_present')).lower()}`",
            f"- `submission_minimal_pdf_present`: `{str(report.get('submission_minimal_pdf_present')).lower()}`",
            f"- `submission_minimal_authority_status`: `{report.get('submission_minimal_authority_status')}`",
            f"- `submission_minimal_authority_stale_reason`: `{report.get('submission_minimal_authority_stale_reason')}`",
            f"- `draft_handoff_delivery_required`: `{str(report.get('draft_handoff_delivery_required')).lower()}`",
            f"- `draft_handoff_delivery_status`: `{report.get('draft_handoff_delivery_status')}`",
            f"- `draft_handoff_delivery_manifest_path`: `{report.get('draft_handoff_delivery_manifest_path')}`",
            f"- `draft_handoff_current_package_root`: `{report.get('draft_handoff_current_package_root')}`",
            f"- `paper_line_open_supplementary_count`: `{report.get('paper_line_open_supplementary_count')}`",
            f"- `paper_line_recommended_action`: `{report.get('paper_line_recommended_action')}`",
            f"- `active_manuscript_figure_count`: `{report.get('active_manuscript_figure_count')}`",
            f"- `submission_grade_min_active_figures`: `{report.get('submission_grade_min_active_figures')}`",
            f"- `study_delivery_current_package_root`: `{report.get('study_delivery_current_package_root')}`",
            f"- `medical_publication_surface_report_path`: `{report.get('medical_publication_surface_report_path')}`",
            f"- `medical_publication_surface_status`: `{report.get('medical_publication_surface_status')}`",
            f"- `medical_publication_surface_current`: `{str(report.get('medical_publication_surface_current')).lower()}`",
        ]
    )
    paper_line_blocking_reasons = report.get("paper_line_blocking_reasons") or []
    if paper_line_blocking_reasons:
        lines.extend(
            [
                "",
                "## Paper-Line Scientific Blockers",
                "",
                *[f"- `{item}`" for item in paper_line_blocking_reasons],
            ]
        )
    if non_scientific_handoff_gaps:
        lines.extend(
            [
                "",
                "## Non-Scientific Handoff Gaps",
                "",
                *[f"- `{item}`" for item in non_scientific_handoff_gaps],
            ]
        )
    if submission_checklist_unclassified:
        lines.extend(
            [
                "",
                "## Unclassified Submission Checklist Gaps",
                "",
                *[f"- `{item}`" for item in submission_checklist_unclassified],
            ]
        )
    unmanaged_roots = report.get("unmanaged_submission_surface_roots") or []
    archived_roots = report.get("archived_submission_surface_roots") or []
    if archived_roots:
        lines.extend(
            [
                "",
                "## Archived Legacy Submission Surfaces",
                "",
                *[f"- `{item}`" for item in archived_roots],
            ]
        )
    if unmanaged_roots:
        lines.extend(
            [
                "",
                "## Unmanaged Submission Surfaces",
                "",
                *[f"- `{item}`" for item in unmanaged_roots],
            ]
        )
    if submission_surface_qc_failures:
        lines.extend(
            [
                "",
                "## Submission Surface QC Failures",
                "",
            ]
        )
        lines.extend(
            "- `{collection}` `{item_id}` ({descriptor}) failed `{qc_profile}` with `{failure_reason}` audit classes {audit_classes}".format(
                collection=item.get("collection"),
                item_id=item.get("item_id"),
                descriptor=item.get("descriptor") or "unlabeled",
                qc_profile=item.get("qc_profile") or "unknown_qc_profile",
                failure_reason=item.get("failure_reason") or "unspecified_failure",
                audit_classes=item.get("audit_classes") or [],
            )
            for item in submission_surface_qc_failures
        )
    else:
        lines.extend(
            [
                "",
                "## Submission Surface QC Failures",
                "",
                "- None",
            ]
        )
    if terminology_violations:
        lines.extend(
            [
                "",
                "## Forbidden Manuscript Terminology",
                "",
            ]
        )
        lines.extend(
            f"- `{item['label']}` matched `{item['match']}` in `{item['path']}`" for item in terminology_violations
        )
    else:
        lines.extend(
            [
                "",
                "## Forbidden Manuscript Terminology",
                "",
                "- None",
            ]
        )
    lines.extend(
        [
            "",
            "## Result Context",
            "",
            f"- {report.get('results_summary')}",
            f"- {report.get('conclusion')}",
            "",
            "## Controller Scope",
            "",
            f"- {report.get('controller_note')}",
            "",
        ]
    )
    return "\n".join(lines)


def write_gate_files(quest_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    return runtime_protocol_report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="publishability_gate",
        timestamp=str(report["generated_at"]),
        report=report,
        markdown=render_gate_markdown(report),
    )


def _materialize_publication_eval_latest(
    *,
    state: GateState,
    report: dict[str, Any],
) -> dict[str, str] | None:
    if state.paper_root is None:
        return None
    try:
        paper_context = resolve_paper_root_context(state.paper_root)
    except (FileNotFoundError, ValueError):
        return None
    decision_module = import_module("med_autoscience.controllers.study_runtime_decision")
    return decision_module._materialize_publication_eval_from_gate_report(
        study_root=paper_context.study_root,
        study_id=paper_context.study_id,
        quest_root=state.quest_root,
        quest_id=paper_context.quest_id,
        publication_gate_report=report,
    )


def run_controller(
    *,
    quest_root: Path,
    apply: bool,
    source: str = "codex-publication-gate",
    enqueue_intervention: bool = True,
) -> dict[str, Any]:
    state = build_gate_state(quest_root)
    report = build_gate_report(state)
    draft_handoff_delivery_sync = None
    study_delivery_stale_sync = None
    journal_package_sync = None
    if (
        apply
        and report.get("draft_handoff_delivery_required") is True
        and report.get("draft_handoff_delivery_status") in {"missing", "stale", "invalid"}
        and state.paper_root is not None
        and study_delivery_sync.can_sync_study_delivery(paper_root=state.paper_root)
    ):
        draft_handoff_delivery_sync = study_delivery_sync.sync_study_delivery(
            paper_root=state.paper_root,
            stage="draft_handoff",
        )
        state = build_gate_state(quest_root)
        report = build_gate_report(state)
    if (
        apply
        and str(report.get("study_delivery_status") or "").strip().startswith("stale")
        and state.paper_root is not None
        and study_delivery_sync.can_sync_study_delivery(paper_root=state.paper_root)
    ):
        stale_reason = str(report.get("study_delivery_stale_reason") or "current_submission_source_missing")
        if stale_reason in {
            "delivery_projection_missing",
            "delivery_manifest_source_changed",
            "delivery_manifest_source_mismatch",
        }:
            study_delivery_stale_sync = study_delivery_sync.sync_study_delivery(
                paper_root=state.paper_root,
                stage="submission_minimal",
            )
        else:
            study_delivery_stale_sync = study_delivery_sync.materialize_submission_delivery_stale_notice(
                paper_root=state.paper_root,
                stale_reason=stale_reason,
                missing_source_paths=list(report.get("study_delivery_missing_source_paths") or []),
        )
        state = build_gate_state(quest_root)
        report = build_gate_report(state)
    if (
        apply
        and state.paper_root is not None
        and isinstance(report.get("primary_journal_target"), dict)
        and str(report.get("journal_requirements_status") or "").strip() == "resolved"
        and str(report.get("journal_package_status") or "").strip() != "current"
        and _non_empty_text(report.get("journal_requirements_study_root"))
    ):
        primary_journal_target = report["primary_journal_target"]
        journal_package_sync = journal_package_controller.materialize_journal_package(
            paper_root=state.paper_root,
            study_root=Path(str(report["journal_requirements_study_root"])),
            journal_slug=str(primary_journal_target["journal_slug"]),
            publication_profile=_non_empty_text(primary_journal_target.get("publication_profile")),
        )
        state = build_gate_state(quest_root)
        report = build_gate_report(state)
    json_path, md_path = write_gate_files(quest_root, report)
    if apply:
        _materialize_publication_eval_latest(
            state=state,
            report={
                **report,
                "latest_gate_path": str(json_path),
            },
        )
    intervention = None
    if apply and enqueue_intervention and report["blockers"]:
        intervention = user_message.enqueue_user_message(
            quest_root=state.quest_root,
            runtime_state=state.runtime_state,
            message=publication_gate_policy.build_intervention_message(report),
            source=source,
        )
    return {
        "report_json": str(json_path),
        "report_markdown": str(md_path),
        "status": report["status"],
        "allow_write": report["allow_write"],
        "blockers": report["blockers"],
        "missing_non_scalar_deliverables": report["missing_non_scalar_deliverables"],
        "submission_minimal_present": report["submission_minimal_present"],
        "draft_handoff_delivery_required": report["draft_handoff_delivery_required"],
        "draft_handoff_delivery_status": report["draft_handoff_delivery_status"],
        "draft_handoff_delivery_manifest_path": report["draft_handoff_delivery_manifest_path"],
        "draft_handoff_delivery_sync": draft_handoff_delivery_sync,
        "study_delivery_stale_sync": study_delivery_stale_sync,
        "journal_package_sync": journal_package_sync,
        "intervention_enqueued": bool(intervention),
        "message_id": intervention.get("message_id") if intervention else None,
        "source": source,
        **extract_publication_supervisor_state(report),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run_controller(quest_root=args.quest_root, apply=args.apply), ensure_ascii=False, indent=2))
