from __future__ import annotations

import importlib
import json
from pathlib import Path


MODULE_NAME = "med_autoscience.quality.study_quality"


def _load_module() -> object:
    return importlib.import_module(MODULE_NAME)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _charter_payload() -> dict[str, object]:
    return {
        "charter_id": "charter::001-risk::v1",
        "study_id": "001-risk",
        "publication_objective": "risk stratification external validation",
        "paper_quality_contract": {
            "bounded_analysis": {
                "default_owner": "mas",
                "allowed_scenarios": [
                    "close_predeclared_evidence_gap_within_locked_direction",
                    "answer_predeclared_reviewer_method_question",
                ],
                "allowed_targets": [
                    "minimum_sci_ready_evidence_package",
                    "scientific_followup_questions",
                ],
                "completion_boundary": {
                    "return_to_main_gate": "publication_eval",
                    "return_to_mainline_action": "return_to_controller",
                    "completion_criteria": [
                        "all_requested_targets_closed",
                        "budget_boundary_reached",
                        "major_boundary_signal_detected",
                    ],
                    "required_updates": [
                        "evidence_ledger",
                        "review_ledger",
                        "publication_eval",
                    ],
                },
            }
        },
    }


def test_build_study_quality_truth_explains_bounded_analysis_gap_and_contract() -> None:
    module = _load_module()

    truth = module.build_study_quality_truth(
        study_id="001-risk",
        charter_payload=_charter_payload(),
        publication_eval={
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "evidence",
                    "severity": "must_fix",
                    "summary": "External validation cohort is still missing.",
                    "evidence_refs": ["/tmp/runtime/main_result.json"],
                }
            ],
        },
        promotion_gate_payload={
            "current_required_action": "return_to_publishability_gate",
            "controller_stage_note": "route back to analysis-campaign to close claim-evidence consistency gaps",
            "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
        },
        route_repair_plan={
            "action_id": "action-002",
            "action_type": "bounded_analysis",
            "priority": "next",
            "route_target": "analysis-campaign",
            "route_key_question": "What is the narrowest supplementary analysis needed to restore endpoint provenance support?",
            "route_rationale": "The study direction remains valid; only a bounded analysis-campaign repair is needed.",
        },
        quality_closure_truth={
            "state": "quality_repair_required",
            "summary": "核心科学质量还没有闭环；当前应先回到 analysis-campaign 完成最窄补充修复。",
            "current_required_action": "return_to_publishability_gate",
            "route_target": "analysis-campaign",
        },
        quality_closure_basis={
            "clinical_significance": {
                "status": "partial",
                "summary": "Clinical framing is frozen, but the result surface is still incomplete.",
                "evidence_refs": ["/tmp/gate.json"],
            },
            "evidence_strength": {
                "status": "blocked",
                "summary": "The current claim-evidence surface is still missing external validation support.",
                "evidence_refs": ["/tmp/gate.json"],
            },
            "novelty_positioning": {
                "status": "partial",
                "summary": "Novelty framing exists, but contribution boundaries still need tightening.",
                "evidence_refs": ["/tmp/charter.json"],
            },
            "human_review_readiness": {
                "status": "partial",
                "summary": "Current package still needs reviewer-facing cleanup.",
                "evidence_refs": ["/tmp/gate.json"],
            },
            "publication_gate": {
                "status": "blocked",
                "summary": "Publication gate still requires same-line repair first.",
                "evidence_refs": ["/tmp/promotion_gate.json"],
            },
        },
        quality_execution_lane={
            "lane_id": "claim_evidence",
            "lane_label": "claim-evidence 修复",
            "repair_mode": "bounded_analysis",
            "route_target": "analysis-campaign",
            "route_key_question": "What is the narrowest supplementary analysis needed to restore endpoint provenance support?",
            "summary": "当前质量执行线聚焦 claim-evidence 修复；先进入 analysis-campaign，回答“What is the narrowest supplementary analysis needed to restore endpoint provenance support?”。",
            "why_now": "The study direction remains valid; only a bounded analysis-campaign repair is needed.",
        },
        review_ledger_payload={
            "schema_version": 1,
            "concerns": [
                {
                    "concern_id": "RC1",
                    "reviewer_id": "reviewer-1",
                    "summary": "Clarify the endpoint boundary in Results.",
                    "severity": "major",
                    "status": "open",
                    "owner_action": "rewrite_results_boundary_paragraph",
                    "revision_links": [
                        {
                            "revision_id": "rev-001",
                            "revision_log_path": "paper/review/revision_log.md",
                        }
                    ],
                }
            ],
        },
        review_ledger_path="/tmp/workspace/studies/001-risk/paper/review/review_ledger.json",
    )

    assert truth["contract_state"] == "quality_repair_required"
    assert truth["contract_closed"] is False
    assert truth["reviewer_first"] == {
        "required": True,
        "status": "blocked",
        "ready": False,
        "source": "review_ledger",
        "summary": "review ledger 仍有 1 个未关闭 concern，reviewer-first readiness 不能视为已闭环。",
        "open_concern_count": 1,
        "resolved_concern_count": 0,
        "evidence_refs": ["/tmp/workspace/studies/001-risk/paper/review/review_ledger.json"],
    }
    assert truth["bounded_analysis"] == {
        "contract_defined": True,
        "required_now": True,
        "entry_state": "ready_to_enter",
        "completion_state": "pending_required_updates",
        "route_target": "analysis-campaign",
        "route_key_question": "What is the narrowest supplementary analysis needed to restore endpoint provenance support?",
        "allowed_scenarios": [
            "close_predeclared_evidence_gap_within_locked_direction",
            "answer_predeclared_reviewer_method_question",
        ],
        "allowed_targets": [
            "minimum_sci_ready_evidence_package",
            "scientific_followup_questions",
        ],
        "completion_criteria": [
            "all_requested_targets_closed",
            "budget_boundary_reached",
            "major_boundary_signal_detected",
        ],
        "required_updates": [
            "evidence_ledger",
            "review_ledger",
            "publication_eval",
        ],
    }
    assert truth["narrowest_scientific_gap"] == {
        "state": "bounded_analysis_required",
        "gap_id": "gap-001",
        "severity": "must_fix",
        "summary": "External validation cohort is still missing.",
        "route_target": "analysis-campaign",
        "route_key_question": "What is the narrowest supplementary analysis needed to restore endpoint provenance support?",
        "why_now": "The study direction remains valid; only a bounded analysis-campaign repair is needed.",
    }
    assert truth["finalize_bundle_readiness"] == {
        "status": "quality_repair_required",
        "ready_for_finalize": False,
        "reviewer_first_ready": False,
        "summary": "当前还在质量修复阶段，finalize / bundle readiness 不能提前视为稳定。",
        "why_stable": "当前最窄 scientific gap 仍未闭环，先完成同线质量修复再进入 finalize / bundle。",
        "basis_dimensions": [],
    }


def test_build_study_quality_truth_marks_bundle_only_remaining_as_same_contract_truth() -> None:
    module = _load_module()

    truth = module.build_study_quality_truth(
        study_id="001-risk",
        charter_payload=_charter_payload(),
        publication_eval={
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "optional",
                    "summary": "Only submission bundle alignment remains.",
                    "evidence_refs": ["/tmp/runtime/main_result.json"],
                }
            ],
        },
        promotion_gate_payload={
            "current_required_action": "complete_bundle_stage",
            "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
            "medical_publication_surface_named_blockers": ["submission_hardening_incomplete"],
        },
        route_repair_plan={
            "action_id": "action-003",
            "action_type": "route_back_same_line",
            "priority": "now",
            "route_target": "finalize",
            "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
            "route_rationale": "The paper itself is ready for human review and only finalize-level cleanup remains.",
        },
        quality_closure_truth={
            "state": "bundle_only_remaining",
            "summary": "核心科学质量已经闭环；剩余工作收口在 finalize / submission bundle，同一论文线可以继续自动推进。",
            "current_required_action": "complete_bundle_stage",
            "route_target": "finalize",
        },
        quality_closure_basis={
            "clinical_significance": {
                "status": "ready",
                "summary": "Clinical framing is already stable.",
                "evidence_refs": ["/tmp/gate.json"],
            },
            "evidence_strength": {
                "status": "ready",
                "summary": "Core evidence is already closed.",
                "evidence_refs": ["/tmp/gate.json"],
            },
            "novelty_positioning": {
                "status": "ready",
                "summary": "Novelty boundary is already fixed.",
                "evidence_refs": ["/tmp/charter.json"],
            },
            "human_review_readiness": {
                "status": "ready",
                "summary": "Human review package is synchronized.",
                "evidence_refs": ["/tmp/review_ledger.json"],
            },
            "publication_gate": {
                "status": "partial",
                "summary": "Only finalize-level bundle cleanup remains.",
                "evidence_refs": ["/tmp/promotion_gate.json"],
            },
        },
        quality_execution_lane={
            "lane_id": "submission_hardening",
            "lane_label": "submission hardening 收口",
            "repair_mode": "same_line_route_back",
            "route_target": "finalize",
            "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
            "summary": "当前质量执行线聚焦 submission hardening 收口；先回到 finalize，回答“What is the narrowest finalize or submission-bundle step still required on the current paper line?”。",
            "why_now": "The paper itself is ready for human review and only finalize-level cleanup remains.",
        },
        review_ledger_payload={
            "schema_version": 1,
            "concerns": [
                {
                    "concern_id": "RC1",
                    "reviewer_id": "reviewer-1",
                    "summary": "Clarify the endpoint boundary in Results.",
                    "severity": "major",
                    "status": "resolved",
                    "owner_action": "rewrite_results_boundary_paragraph",
                    "revision_links": [
                        {
                            "revision_id": "rev-001",
                            "revision_log_path": "paper/review/revision_log.md",
                        }
                    ],
                }
            ],
        },
        review_ledger_path="/tmp/workspace/studies/001-risk/paper/review/review_ledger.json",
    )

    assert truth["contract_state"] == "bundle_only_remaining"
    assert truth["contract_closed"] is True
    assert truth["narrowest_scientific_gap"] == {
        "state": "closed",
        "gap_id": None,
        "severity": None,
        "summary": "Open scientific gap is already closed; only finalize / submission-bundle stabilization remains.",
        "route_target": "finalize",
        "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
        "why_now": "The paper itself is ready for human review and only finalize-level cleanup remains.",
    }
    assert truth["finalize_bundle_readiness"] == {
        "status": "bundle_only_remaining",
        "ready_for_finalize": True,
        "reviewer_first_ready": True,
        "summary": "核心科学面、reviewer-first readiness 和 publication gate 已经落在同一组 quality truth 上；当前只剩 finalize / bundle 收口。",
        "why_stable": "clinical_significance、evidence_strength、novelty_positioning 已达到 ready，reviewer-first 也已具备常规放行条件。",
        "basis_dimensions": [
            "clinical_significance",
            "evidence_strength",
            "novelty_positioning",
            "human_review_readiness",
        ],
    }


def test_evaluation_summary_materializes_study_quality_truth_on_durable_surface(tmp_path: Path) -> None:
    summary_module = importlib.import_module("med_autoscience.evaluation_summary")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    runtime_escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    review_ledger_path = study_root / "paper" / "review" / "review_ledger.json"

    _write_json(charter_path, _charter_payload())
    _write_json(
        review_ledger_path,
        {
            "schema_version": 1,
            "concerns": [
                {
                    "concern_id": "RC1",
                    "reviewer_id": "reviewer-1",
                    "summary": "Clarify the endpoint boundary in Results.",
                    "severity": "major",
                    "status": "resolved",
                    "owner_action": "rewrite_results_boundary_paragraph",
                    "revision_links": [
                        {
                            "revision_id": "rev-001",
                            "revision_log_path": "paper/review/revision_log.md",
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T06:00:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(charter_path),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "risk stratification external validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(runtime_escalation_path),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "supported",
                "summary": "Core science is closed; remaining work is finalize-stage package hardening.",
                "stop_loss_pressure": "none",
            },
            "quality_assessment": {
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical framing is already stable.",
                    "evidence_refs": [str(gate_report_path)],
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Core evidence is already closed.",
                    "evidence_refs": [str(gate_report_path)],
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Novelty boundary is already fixed.",
                    "evidence_refs": [str(charter_path)],
                },
                "human_review_readiness": {
                    "status": "partial",
                    "summary": "Human review package is nearly synchronized.",
                    "evidence_refs": [str(gate_report_path)],
                },
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "optional",
                    "summary": "Only submission bundle alignment remains.",
                    "evidence_refs": [str(gate_report_path)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-003",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "Return to finalize for last-mile bundle stabilization.",
                    "route_target": "finalize",
                    "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
                    "route_rationale": "The paper itself is ready for human review and only finalize-level cleanup remains.",
                    "evidence_refs": [str(gate_report_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    _write_json(
        runtime_escalation_path,
        {
            "schema_version": 1,
            "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "trigger": {"trigger_id": "publishability_gate_blocked", "source": "publication_gate"},
            "scope": "quest",
            "severity": "study",
            "reason": "publishability_gate_blocked",
            "recommended_actions": ["return_to_controller", "review_publishability_gate"],
            "evidence_refs": [str(gate_report_path)],
            "runtime_context_refs": {
                "launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
            "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            "artifact_path": str(runtime_escalation_path),
        },
    )
    _write_json(
        gate_report_path,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-05T06:05:00+00:00",
            "quest_id": "quest-001",
            "status": "blocked",
            "allow_write": False,
            "recommended_action": "complete_bundle_stage",
            "latest_gate_path": str(gate_report_path),
            "supervisor_phase": "bundle_stage_blocked",
            "current_required_action": "complete_bundle_stage",
            "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
            "blockers": ["missing_submission_minimal"],
            "medical_publication_surface_named_blockers": ["submission_hardening_incomplete"],
        },
    )

    summary_module.materialize_evaluation_summary_artifacts(
        study_root=study_root,
        runtime_escalation_ref=str(runtime_escalation_path),
        publishability_gate_report_ref=gate_report_path,
    )

    summary = summary_module.read_evaluation_summary(study_root=study_root)

    assert summary["study_quality_truth"] == {
        "study_id": "001-risk",
        "contract_state": "bundle_only_remaining",
        "contract_closed": True,
        "summary": "核心科学质量已经闭环；剩余工作收口在 finalize / submission bundle，同一论文线可以继续自动推进。",
        "narrowest_scientific_gap": {
            "state": "closed",
            "gap_id": None,
            "severity": None,
            "summary": "Open scientific gap is already closed; only finalize / submission-bundle stabilization remains.",
            "route_target": "finalize",
            "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
            "why_now": "The paper itself is ready for human review and only finalize-level cleanup remains.",
        },
        "reviewer_first": {
            "required": True,
            "status": "ready",
            "ready": True,
            "source": "review_ledger",
            "summary": "review ledger 已把 1 个 concern 全部收口，reviewer-first readiness 已具备常规放行条件。",
            "open_concern_count": 0,
            "resolved_concern_count": 1,
            "evidence_refs": [str(review_ledger_path)],
        },
        "bounded_analysis": {
            "contract_defined": True,
            "required_now": False,
            "entry_state": "not_required",
            "completion_state": "satisfied",
            "route_target": "finalize",
            "route_key_question": "What is the narrowest finalize or submission-bundle step still required on the current paper line?",
            "allowed_scenarios": [
                "close_predeclared_evidence_gap_within_locked_direction",
                "answer_predeclared_reviewer_method_question",
            ],
            "allowed_targets": [
                "minimum_sci_ready_evidence_package",
                "scientific_followup_questions",
            ],
            "completion_criteria": [
                "all_requested_targets_closed",
                "budget_boundary_reached",
                "major_boundary_signal_detected",
            ],
            "required_updates": [
                "evidence_ledger",
                "review_ledger",
                "publication_eval",
            ],
        },
        "finalize_bundle_readiness": {
            "status": "bundle_only_remaining",
            "ready_for_finalize": True,
            "reviewer_first_ready": True,
            "summary": "核心科学面、reviewer-first readiness 和 publication gate 已经落在同一组 quality truth 上；当前只剩 finalize / bundle 收口。",
            "why_stable": "clinical_significance、evidence_strength、novelty_positioning 已达到 ready，reviewer-first 也已具备常规放行条件。",
            "basis_dimensions": [
                "clinical_significance",
                "evidence_strength",
                "novelty_positioning",
                "human_review_readiness",
            ],
        },
        "publication_gate_required_action": "complete_bundle_stage",
    }
