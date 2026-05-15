from __future__ import annotations

from dataclasses import dataclass

import pytest

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


@dataclass(frozen=True)
class WorkUnitTransitionCase:
    case_id: str
    gate_report: dict[str, object]
    expected_actionability_status: str
    expected_unit_id: str
    expected_lane: str


@pytest.mark.parametrize(
    "case",
    (
        WorkUnitTransitionCase(
            case_id="clear_bundle_stage_moves_to_submission_authority_sync",
            gate_report={
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "current_required_action": "continue_bundle_stage",
                "medical_publication_surface_status": "clear",
                "study_delivery_status": "current",
                "submission_minimal_authority_status": "current",
            },
            expected_actionability_status="controller_bundle_stage_required",
            expected_unit_id="submission_authority_sync_closure",
            expected_lane="controller",
        ),
        WorkUnitTransitionCase(
            case_id="blocked_bundle_stage_stale_authority_moves_to_submission_authority_sync",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["stale_submission_minimal_authority"],
                "current_required_action": "complete_bundle_stage",
                "supervisor_phase": "bundle_stage_blocked",
                "study_delivery_status": "current",
                "submission_minimal_authority_status": "stale_source_changed",
                "submission_minimal_evaluated_source_signature": "source::new",
                "submission_minimal_authority_source_signature": "source::old",
            },
            expected_actionability_status="controller_authority_sync_required",
            expected_unit_id="submission_authority_sync_closure",
            expected_lane="controller",
        ),
        WorkUnitTransitionCase(
            case_id="publishability_gate_blocked_claim_evidence_stays_analysis_repair",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
                "current_required_action": "return_to_publishability_gate",
                "supervisor_phase": "publishability_gate_blocked",
                "medical_publication_surface_status": "blocked",
                "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
                "blocking_artifact_refs": [{"source_path": "paper/evidence_ledger.json"}],
            },
            expected_actionability_status="actionable",
            expected_unit_id="analysis_claim_evidence_repair",
            expected_lane="analysis-campaign",
        ),
        WorkUnitTransitionCase(
            case_id="publishability_gate_blocked_label_only_claim_requires_specificity",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["medical_publication_surface_blocked"],
                "current_required_action": "return_to_publishability_gate",
                "supervisor_phase": "publishability_gate_blocked",
                "medical_publication_surface_status": "blocked",
                "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
            },
            expected_actionability_status="blocked_by_non_actionable_gate",
            expected_unit_id="gate_needs_specificity",
            expected_lane="controller",
        ),
    ),
    ids=lambda case: case.case_id,
)
def test_publication_gate_report_to_work_unit_transition_matrix(case: WorkUnitTransitionCase) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(case.gate_report)

    assert result["actionability_status"] == case.expected_actionability_status
    assert result["next_work_unit"]["unit_id"] == case.expected_unit_id
    assert result["next_work_unit"]["lane"] == case.expected_lane


@dataclass(frozen=True)
class OuterLoopTransitionCase:
    case_id: str
    gate_report: dict[str, object]
    publication_eval_action: dict[str, object]
    publication_eval_verdict: str
    publication_supervisor_state: dict[str, object]
    expected_decision_type: str
    expected_route_target: str
    expected_controller_action_type: str
    expected_unit_id: str
    task_intake_action: dict[str, object] | None = None
    assessment_provenance: dict[str, object] | None = None
    quality_assessment: dict[str, object] | None = None


def _publication_eval_payload(
    *,
    study_root: Path,
    quest_root: Path,
    action: dict[str, object],
    verdict: str,
    assessment_provenance: dict[str, object] | None = None,
    quality_assessment: dict[str, object] | None = None,
) -> dict[str, object]:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    default_quality_dimension = {
        "status": "ready",
        "summary": "Transition matrix fixture quality dimension is ready.",
        "evidence_refs": [str(publication_eval_path)],
    }
    payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::transition-matrix",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-05-14T09:30:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(
                quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
            ),
            "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": assessment_provenance
        or {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [str(study_root / "paper" / "manuscript.md")],
            "ai_reviewer_required": False,
        },
        "verdict": {
            "overall_verdict": verdict,
            "primary_claim_status": "supported" if verdict == "promising" else "partial",
            "summary": "Transition-matrix publication evaluation fixture.",
            "stop_loss_pressure": "none" if verdict == "promising" else "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-transition-matrix",
                "gap_type": "delivery" if action.get("route_target") == "finalize" else "evidence",
                "severity": "important",
                "summary": "Transition matrix gap fixture.",
                "evidence_refs": [str(publication_eval_path)],
            }
        ],
        "quality_assessment": quality_assessment
        or {
            "clinical_significance": dict(default_quality_dimension),
            "evidence_strength": dict(default_quality_dimension),
            "novelty_positioning": dict(default_quality_dimension),
            "human_review_readiness": dict(default_quality_dimension),
            "medical_journal_prose_quality": {
                **default_quality_dimension,
                "summary": "AI reviewer judged the medical-journal prose quality ready.",
            },
        },
        "recommended_actions": [action],
    }
    return payload


def _finalize_review_only_action(study_root: Path) -> dict[str, object]:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    return {
        "action_id": "action-finalize-review-only",
        "action_type": "continue_same_line",
        "priority": "now",
        "reason": "Bundle-stage work is unlocked and should continue on the finalize lane.",
        "route_target": "finalize",
        "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
        "route_rationale": "Only bundle-stage controller work remains.",
        "evidence_refs": [str(publication_eval_path)],
        "work_unit_fingerprint": "publication-blockers::review",
        "next_work_unit": {
            "unit_id": "publication_gate_blocker_review",
            "lane": "review",
            "summary": "Review the current publication gate blockers and select the narrowest repair unit.",
        },
        "blocking_work_units": [
            {
                "unit_id": "publication_gate_blocker_review",
                "lane": "review",
                "summary": "Review the current publication gate blockers and select the narrowest repair unit.",
            }
        ],
        "requires_controller_decision": True,
    }


def _bounded_analysis_action(study_root: Path) -> dict[str, object]:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    return {
        "action_id": "action-analysis-repair",
        "action_type": "bounded_analysis",
        "priority": "now",
        "reason": "Claim-evidence blockers require bounded analysis repair before publication packaging.",
        "route_target": "analysis-campaign",
        "route_key_question": "Which claim-evidence repair is still blocking publishability?",
        "route_rationale": "Publication gate selected a claim-evidence repair work unit.",
        "evidence_refs": [str(publication_eval_path)],
        "requires_controller_decision": True,
        "next_work_unit": {
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
        },
        "blocking_work_units": [
            {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
                "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
            }
        ],
        "work_unit_fingerprint": "publication-blockers::analysis",
    }


def _stale_write_task_intake_action() -> dict[str, object]:
    return {
        "action_id": "task-intake::001-risk::write",
        "action_type": "continue_same_line",
        "priority": "now",
        "reason": "Stale write task intake should yield once bundle-stage is authoritative.",
        "route_target": "write",
        "route_key_question": "旧 manuscript revision work unit。",
        "route_rationale": "Old write task intake residue.",
        "requires_controller_decision": True,
        "controller_action_type": "ensure_study_runtime",
        "next_work_unit": {
            "unit_id": "manuscript_story_repair",
            "lane": "write",
            "summary": "Repair the paper story around the current evidence and claim boundary.",
        },
        "work_unit_fingerprint": "publication-blockers::stale-write",
    }


@pytest.mark.parametrize(
    "case_factory",
    (
        lambda study_root: OuterLoopTransitionCase(
            case_id="domain_transition_bundle_finalize_preempts_stale_rebuttal_task_intake",
            gate_report={
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "current_required_action": "continue_bundle_stage",
                "medical_publication_surface_status": "clear",
                "study_delivery_status": "current",
                "submission_minimal_authority_status": "current",
            },
            publication_eval_action={
                "action_id": "action-stale-rebuttal-coverage",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": "Stale rebuttal coverage closeout should yield to bundle-stage authority.",
                "route_target": "analysis-campaign",
                "route_key_question": "paper/rebuttal/review_matrix.md and action_plan.md coverage closeout",
                "route_rationale": "Old analysis-campaign route residue.",
                "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                "requires_controller_decision": True,
                "next_work_unit": {
                    "unit_id": "rebuttal_coverage_closeout",
                    "lane": "analysis-campaign",
                    "summary": "Confirm reviewer feedback coverage.",
                },
                "blocking_work_units": [
                    {
                        "unit_id": "rebuttal_coverage_closeout",
                        "lane": "analysis-campaign",
                        "summary": "Confirm reviewer feedback coverage.",
                    }
                ],
            },
            publication_eval_verdict="promising",
            publication_supervisor_state={
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
                "publication_gate_allows_direct_write": True,
            },
            task_intake_action={
                "action_id": "task-intake::001-risk::rebuttal",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": "Old rebuttal coverage task intake residue.",
                "route_target": "analysis-campaign",
                "route_key_question": "paper/rebuttal/review_matrix.md and action_plan.md coverage closeout",
                "route_rationale": "Old analysis-campaign route residue.",
                "requires_controller_decision": True,
                "controller_action_type": "ensure_study_runtime",
                "next_work_unit": {
                    "unit_id": "rebuttal_coverage_closeout",
                    "lane": "analysis-campaign",
                    "summary": "Confirm reviewer feedback coverage.",
                },
                "work_unit_fingerprint": "publication-blockers::stale-rebuttal",
            },
            expected_decision_type="continue_same_line",
            expected_route_target="finalize",
            expected_controller_action_type="ensure_study_runtime",
            expected_unit_id="submission_authority_sync_closure",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="domain_transition_ai_reviewer_required_preempts_stale_write_task_intake",
            gate_report={
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "current_required_action": "continue_bundle_stage",
                "medical_publication_surface_status": "clear",
            },
            publication_eval_action={
                "action_id": "action-stale-write",
                "action_type": "continue_same_line",
                "priority": "now",
                "reason": "Old manuscript write task should yield to AI reviewer assessment.",
                "route_target": "write",
                "route_key_question": "MAS/MDS-supervised revised manuscript package",
                "route_rationale": "Old write route residue.",
                "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                "requires_controller_decision": True,
                "next_work_unit": {
                    "unit_id": "revised_manuscript_package",
                    "lane": "write",
                    "summary": "Continue canonical manuscript revisions.",
                },
            },
            publication_eval_verdict="promising",
            assessment_provenance={
                "owner": "mechanical_projection",
                "source_kind": "publication_gate_report",
                "policy_id": "publication_gate_projection_v1",
                "source_refs": [str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
                "ai_reviewer_required": True,
            },
            publication_supervisor_state={
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
                "publication_gate_allows_direct_write": True,
            },
            task_intake_action=_stale_write_task_intake_action(),
            expected_decision_type="continue_same_line",
            expected_route_target="review",
            expected_controller_action_type="return_to_ai_reviewer_workflow",
            expected_unit_id="ai_reviewer_recheck",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="ai_reviewer_underdefined_medical_prose_preempts_bundle_finalize",
            gate_report={
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "current_required_action": "continue_bundle_stage",
                "medical_publication_surface_status": "clear",
                "study_delivery_status": "current",
                "submission_minimal_authority_status": "current",
            },
            publication_eval_action=_finalize_review_only_action(study_root),
            publication_eval_verdict="promising",
            publication_supervisor_state={
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
                "publication_gate_allows_direct_write": True,
            },
            quality_assessment={
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical significance is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Evidence strength is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Novelty positioning is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human review readiness is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": (
                        "AI reviewer has not yet closed medical-journal prose quality for this manuscript."
                    ),
                    "evidence_refs": [str(study_root / "paper")],
                }
            },
            expected_decision_type="continue_same_line",
            expected_route_target="review",
            expected_controller_action_type="return_to_ai_reviewer_workflow",
            expected_unit_id="ai_reviewer_medical_prose_quality_review",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="domain_transition_gate_blocker_replays_gate_after_terminal_analysis_handoff",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
                "current_required_action": "return_to_publishability_gate",
                "supervisor_phase": "publishability_gate_blocked",
                "bundle_tasks_downstream_only": True,
                "medical_publication_surface_status": "blocked",
                "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
            },
            publication_eval_action={
                "action_id": "action-stale-terminal-analysis",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": "Old terminal analysis repair should not be redriven without gate replay.",
                "route_target": "analysis-campaign",
                "route_key_question": "analysis_claim_evidence_repair",
                "route_rationale": "Old terminal repair route residue.",
                "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                "requires_controller_decision": True,
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence blockers.",
                },
            },
            publication_eval_verdict="blocked",
            publication_supervisor_state={
                "supervisor_phase": "publishability_gate_blocked",
                "current_required_action": "return_to_publishability_gate",
                "bundle_tasks_downstream_only": True,
                "publication_gate_allows_direct_write": False,
            },
            expected_decision_type="bounded_analysis",
            expected_route_target="review",
            expected_controller_action_type="run_gate_clearing_batch",
            expected_unit_id="publication_gate_replay",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="clear_bundle_stage_preempts_stale_write_task_intake",
            gate_report={
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "current_required_action": "continue_bundle_stage",
                "medical_publication_surface_status": "clear",
                "study_delivery_status": "current",
                "submission_minimal_authority_status": "current",
            },
            publication_eval_action=_finalize_review_only_action(study_root),
            publication_eval_verdict="promising",
            publication_supervisor_state={
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
                "publication_gate_allows_direct_write": True,
            },
            task_intake_action=_stale_write_task_intake_action(),
            expected_decision_type="continue_same_line",
            expected_route_target="finalize",
            expected_controller_action_type="ensure_study_runtime",
            expected_unit_id="submission_authority_sync_closure",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="blocked_bundle_stage_preempts_stale_write_task_intake",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["stale_submission_minimal_authority"],
                "current_required_action": "complete_bundle_stage",
                "supervisor_phase": "bundle_stage_blocked",
                "study_delivery_status": "current",
                "submission_minimal_authority_status": "stale_source_changed",
                "submission_minimal_evaluated_source_signature": "source::new",
                "submission_minimal_authority_source_signature": "source::old",
            },
            publication_eval_action=_finalize_review_only_action(study_root),
            publication_eval_verdict="promising",
            publication_supervisor_state={
                "supervisor_phase": "bundle_stage_blocked",
                "current_required_action": "complete_bundle_stage",
                "publication_gate_allows_direct_write": False,
            },
            task_intake_action=_stale_write_task_intake_action(),
            expected_decision_type="continue_same_line",
            expected_route_target="finalize",
            expected_controller_action_type="ensure_study_runtime",
            expected_unit_id="submission_authority_sync_closure",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="publishability_gate_blocked_routes_analysis_repair_not_finalize",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
                "current_required_action": "return_to_publishability_gate",
                "supervisor_phase": "publishability_gate_blocked",
                "bundle_tasks_downstream_only": True,
                "medical_publication_surface_status": "blocked",
                "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
                "blocking_artifact_refs": [{"source_path": "paper/evidence_ledger.json"}],
            },
            publication_eval_action=_bounded_analysis_action(study_root),
            publication_eval_verdict="blocked",
            publication_supervisor_state={
                "supervisor_phase": "publishability_gate_blocked",
                "current_required_action": "return_to_publishability_gate",
                "bundle_tasks_downstream_only": True,
                "publication_gate_allows_direct_write": False,
            },
            expected_decision_type="bounded_analysis",
            expected_route_target="analysis-campaign",
            expected_controller_action_type="ensure_study_runtime",
            expected_unit_id="analysis_claim_evidence_repair",
        ),
    ),
    ids=lambda factory: factory(Path("/tmp/study")).case_id,
)
def test_runtime_watch_outer_loop_controller_transition_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case_factory,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    case = case_factory(study_root)
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _publication_eval_payload(
            study_root=study_root,
            quest_root=quest_root,
            action=case.publication_eval_action,
            verdict=case.publication_eval_verdict,
            assessment_provenance=case.assessment_provenance,
            quality_assessment=case.quality_assessment,
        ),
    )
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(module.publication_gate_controller, "build_gate_report", lambda state: dict(case.gate_report))
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "build_gate_clearing_batch_recommended_action",
        lambda **_: None,
    )
    monkeypatch.setattr(
        module.quality_repair_batch,
        "build_quality_repair_batch_recommended_action",
        lambda **_: None,
    )
    monkeypatch.setattr(module, "recommended_task_intake_action", lambda **_: case.task_intake_action)

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "mas-run-001",
            "reason": "quest_already_running",
            "publication_supervisor_state": case.publication_supervisor_state,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == case.expected_decision_type
    assert request["route_target"] == case.expected_route_target
    assert request["controller_actions"][0]["action_type"] == case.expected_controller_action_type
    assert request["next_work_unit"]["unit_id"] == case.expected_unit_id
