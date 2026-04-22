from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


MODULE_NAME = "med_autoscience.evaluation_summary"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _stable_inputs(tmp_path: Path) -> dict[str, object]:
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    runtime_escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"

    charter_payload = {
        "schema_version": 1,
        "charter_id": "charter::001-risk::v1",
        "study_id": "001-risk",
        "publication_objective": "risk stratification external validation",
    }
    runtime_escalation_payload = {
        "schema_version": 1,
        "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-05T05:58:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T05:58:00+00:00",
        "trigger": {
            "trigger_id": "publishability_gate_blocked",
            "source": "publication_gate",
        },
        "scope": "quest",
        "severity": "study",
        "reason": "publishability_gate_blocked",
        "recommended_actions": ["return_to_controller", "review_publishability_gate"],
        "evidence_refs": [
            str(gate_report_path),
            str(quest_root / "artifacts" / "results" / "main_result.json"),
        ],
        "runtime_context_refs": {
            "launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        },
        "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        "artifact_path": str(runtime_escalation_path),
    }
    publication_eval_payload = {
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
            "primary_claim_status": "partial",
            "summary": "Primary claim still lacks external validation support.",
            "stop_loss_pressure": "watch",
        },
        "quality_assessment": {
            "clinical_significance": {
                "status": "partial",
                "summary": "Clinical framing is frozen, but the current result surface is still incomplete.",
                "evidence_refs": [str(gate_report_path)],
            },
            "evidence_strength": {
                "status": "blocked",
                "summary": "The current claim-evidence surface is still missing external validation support.",
                "evidence_refs": [str(gate_report_path)],
            },
            "novelty_positioning": {
                "status": "partial",
                "summary": "Novelty framing exists, but reviewer-facing contribution boundaries still need tightening.",
                "evidence_refs": [str(charter_path)],
            },
            "human_review_readiness": {
                "status": "blocked",
                "summary": "The draft is not yet honest enough to release as a human review package.",
                "evidence_refs": [str(gate_report_path)],
            },
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "evidence",
                "severity": "must_fix",
                "summary": "External validation cohort is still missing.",
                "evidence_refs": [
                    str(quest_root / "artifacts" / "results" / "main_result.json"),
                ],
            },
            {
                "gap_id": "gap-002",
                "gap_type": "reporting",
                "severity": "important",
                "summary": "Methods section still lacks endpoint provenance note.",
                "evidence_refs": [
                    str(gate_report_path),
                ],
            },
        ],
        "recommended_actions": [
            {
                "action_id": "action-001",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "Controller must decide whether to invest in external validation.",
                "evidence_refs": [
                    str(runtime_escalation_path),
                ],
                "requires_controller_decision": True,
            },
            {
                "action_id": "action-002",
                "action_type": "bounded_analysis",
                "priority": "next",
                "reason": "Prepare the missing endpoint provenance note before the next gate pass.",
                "route_target": "analysis-campaign",
                "route_key_question": "What is the narrowest supplementary analysis needed to restore endpoint provenance support?",
                "route_rationale": "The study direction remains valid; only a bounded analysis-campaign repair is needed.",
                "evidence_refs": [
                    str(gate_report_path),
                ],
                "requires_controller_decision": True,
            },
        ],
    }
    gate_report_payload = {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": "2026-04-05T06:05:00+00:00",
        "quest_id": "quest-001",
        "status": "blocked",
        "allow_write": False,
        "recommended_action": "return_to_publishability_gate",
        "latest_gate_path": str(gate_report_path),
        "supervisor_phase": "publishability_gate_blocked",
        "current_required_action": "return_to_publishability_gate",
        "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
        "blockers": ["missing_post_main_publishability_gate"],
        "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
        "medical_publication_surface_route_back_recommendation": "return_to_analysis_campaign",
    }

    _write_json(charter_path, charter_payload)
    _write_json(publication_eval_path, publication_eval_payload)
    _write_json(runtime_escalation_path, runtime_escalation_payload)
    _write_json(gate_report_path, gate_report_payload)

    return {
        "study_root": study_root,
        "quest_root": quest_root,
        "charter_path": charter_path,
        "publication_eval_path": publication_eval_path,
        "runtime_escalation_path": runtime_escalation_path,
        "gate_report_path": gate_report_path,
        "charter_payload": charter_payload,
        "publication_eval_payload": publication_eval_payload,
        "runtime_escalation_payload": runtime_escalation_payload,
        "gate_report_payload": gate_report_payload,
    }


def test_resolve_evaluation_summary_ref_defaults_to_eval_hygiene_latest_surface(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    resolved = module.resolve_evaluation_summary_ref(study_root=study_root)

    assert resolved == (study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json").resolve()


def test_resolve_promotion_gate_ref_defaults_to_eval_hygiene_latest_surface(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    resolved = module.resolve_promotion_gate_ref(study_root=study_root)

    assert resolved == (study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json").resolve()


def test_resolve_promotion_gate_ref_rejects_controller_publishability_gate_projection(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    projected_ref = study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"

    with pytest.raises(ValueError, match="eval hygiene-owned promotion gate artifact"):
        module.resolve_promotion_gate_ref(study_root=study_root, ref=projected_ref)


def test_materialize_evaluation_summary_artifacts_writes_typed_stable_surfaces(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    runtime_escalation_payload = inputs["runtime_escalation_payload"]
    gate_report_path = inputs["gate_report_path"]

    written_refs = module.materialize_evaluation_summary_artifacts(
        study_root=study_root,
        runtime_escalation_ref={
            "record_id": runtime_escalation_payload["record_id"],
            "artifact_path": runtime_escalation_payload["artifact_path"],
            "summary_ref": runtime_escalation_payload["summary_ref"],
        },
        publishability_gate_report_ref=gate_report_path,
    )

    promotion_gate_path = study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json"
    evaluation_summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    promotion_gate_payload = json.loads(promotion_gate_path.read_text(encoding="utf-8"))
    evaluation_summary_payload = json.loads(evaluation_summary_path.read_text(encoding="utf-8"))

    assert written_refs == {
        "evaluation_summary_ref": {
            "summary_id": "evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            "artifact_path": str(evaluation_summary_path.resolve()),
        },
        "promotion_gate_ref": {
            "gate_id": "promotion-gate::001-risk::quest-001::2026-04-05T06:05:00+00:00",
            "artifact_path": str(promotion_gate_path.resolve()),
        },
    }
    assert promotion_gate_payload == {
        "schema_version": 1,
        "gate_id": "promotion-gate::001-risk::quest-001::2026-04-05T06:05:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:05:00+00:00",
        "source_gate_report_ref": str(gate_report_path.resolve()),
        "publication_eval_ref": {
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            "artifact_path": str((study_root / "artifacts" / "publication_eval" / "latest.json").resolve()),
        },
        "runtime_escalation_ref": {
            "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-05T05:58:00+00:00",
            "artifact_path": str(
                (
                    inputs["quest_root"]
                    / "artifacts"
                    / "reports"
                    / "escalation"
                    / "runtime_escalation_record.json"
                ).resolve()
            ),
            "summary_ref": str((study_root / "artifacts" / "runtime" / "last_launch_report.json").resolve()),
        },
        "overall_verdict": "blocked",
        "primary_claim_status": "partial",
        "stop_loss_pressure": "watch",
        "status": "blocked",
        "allow_write": False,
        "recommended_action": "return_to_publishability_gate",
        "current_required_action": "return_to_publishability_gate",
        "supervisor_phase": "publishability_gate_blocked",
        "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
        "blockers": ["missing_post_main_publishability_gate"],
        "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
        "medical_publication_surface_route_back_recommendation": "return_to_analysis_campaign",
    }
    assert evaluation_summary_payload == {
        "schema_version": 1,
        "summary_id": "evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "charter_ref": {
            "charter_id": "charter::001-risk::v1",
            "artifact_path": str((study_root / "artifacts" / "controller" / "study_charter.json").resolve()),
            "publication_objective": "risk stratification external validation",
        },
        "publication_eval_ref": {
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            "artifact_path": str((study_root / "artifacts" / "publication_eval" / "latest.json").resolve()),
        },
        "runtime_escalation_ref": {
            "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-05T05:58:00+00:00",
            "artifact_path": str(
                (
                    inputs["quest_root"]
                    / "artifacts"
                    / "reports"
                    / "escalation"
                    / "runtime_escalation_record.json"
                ).resolve()
            ),
            "summary_ref": str((study_root / "artifacts" / "runtime" / "last_launch_report.json").resolve()),
        },
        "promotion_gate_ref": {
            "gate_id": "promotion-gate::001-risk::quest-001::2026-04-05T06:05:00+00:00",
            "artifact_path": str(promotion_gate_path.resolve()),
        },
        "evaluation_scope": "publication",
        "overall_verdict": "blocked",
        "primary_claim_status": "partial",
        "verdict_summary": "Primary claim still lacks external validation support.",
        "stop_loss_pressure": "watch",
        "publication_objective": "risk stratification external validation",
        "gap_counts": {
            "must_fix": 1,
            "important": 1,
            "optional": 0,
            "total": 2,
        },
        "recommended_action_types": ["return_to_controller", "bounded_analysis"],
        "route_repair_plan": {
            "action_id": "action-002",
            "action_type": "bounded_analysis",
            "priority": "next",
            "route_target": "analysis-campaign",
            "route_key_question": "What is the narrowest supplementary analysis needed to restore endpoint provenance support?",
            "route_rationale": "The study direction remains valid; only a bounded analysis-campaign repair is needed.",
        },
        "quality_closure_truth": {
            "state": "quality_repair_required",
            "summary": "核心科学质量还没有闭环；当前应先回到 analysis-campaign 完成最窄补充修复。",
            "current_required_action": "return_to_publishability_gate",
            "route_target": "analysis-campaign",
        },
        "quality_execution_lane": {
            "lane_id": "claim_evidence",
            "lane_label": "claim-evidence 修复",
            "repair_mode": "bounded_analysis",
            "route_target": "analysis-campaign",
            "route_key_question": "What is the narrowest supplementary analysis needed to restore endpoint provenance support?",
            "summary": "当前质量执行线聚焦 claim-evidence 修复；先进入 analysis-campaign，回答“What is the narrowest supplementary analysis needed to restore endpoint provenance support?”。",
            "why_now": "The study direction remains valid; only a bounded analysis-campaign repair is needed.",
        },
        "quality_closure_basis": {
            "clinical_significance": {
                "status": "partial",
                "summary": "Clinical framing is frozen, but the current result surface is still incomplete.",
                "evidence_refs": [str(gate_report_path.resolve())],
            },
            "evidence_strength": {
                "status": "blocked",
                "summary": "The current claim-evidence surface is still missing external validation support.",
                "evidence_refs": [str(gate_report_path.resolve())],
            },
            "novelty_positioning": {
                "status": "partial",
                "summary": "Novelty framing exists, but reviewer-facing contribution boundaries still need tightening.",
                "evidence_refs": [str((study_root / "artifacts" / "controller" / "study_charter.json").resolve())],
            },
            "human_review_readiness": {
                "status": "blocked",
                "summary": "The draft is not yet honest enough to release as a human review package.",
                "evidence_refs": [str(gate_report_path.resolve())],
            },
            "publication_gate": {
                "status": "blocked",
                "summary": "发表门控仍未放行当前论文线；系统应先沿 analysis-campaign 修复质量缺口。",
                "evidence_refs": [str(promotion_gate_path.resolve())],
            },
        },
        "quality_review_agenda": {
            "top_priority_issue": "必须优先修复：External validation cohort is still missing.",
            "suggested_revision": "Controller must decide whether to invest in external validation.",
            "next_review_focus": "What is the narrowest supplementary analysis needed to restore endpoint provenance support?",
            "agenda_summary": (
                "优先修复：必须优先修复：External validation cohort is still missing.；"
                "建议修订：Controller must decide whether to invest in external validation.；"
                "下一轮复评重点：What is the narrowest supplementary analysis needed to restore endpoint provenance support?"
            ),
        },
        "quality_revision_plan": {
            "policy_id": "medical_publication_critique_v1",
            "plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            "execution_status": "planned",
            "overall_diagnosis": "核心科学质量还没有闭环；当前应先回到 analysis-campaign 完成最窄补充修复。",
            "weight_contract": {
                "clinical_significance": 25,
                "evidence_strength": 35,
                "novelty_positioning": 20,
                "human_review_readiness": 20,
            },
            "items": [
                {
                    "item_id": "quality-revision-item-1",
                    "priority": "p0",
                    "dimension": "evidence_strength",
                    "action_type": "close_evidence_gap",
                    "action": "Controller must decide whether to invest in external validation.",
                    "rationale": "必须优先修复：External validation cohort is still missing.",
                    "done_criteria": (
                        "下一轮复评能够明确确认："
                        "What is the narrowest supplementary analysis needed to restore endpoint provenance support?"
                    ),
                    "route_target": "analysis-campaign",
                }
            ],
            "next_review_focus": [
                "What is the narrowest supplementary analysis needed to restore endpoint provenance support?"
            ],
        },
        "quality_review_loop": {
            "policy_id": "medical_publication_critique_v1",
            "loop_id": "quality-review-loop::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            "closure_state": "quality_repair_required",
            "lane_id": "claim_evidence",
            "current_phase": "revision_required",
            "current_phase_label": "修订待执行",
            "recommended_next_phase": "revision",
            "recommended_next_phase_label": "执行修订",
            "active_plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            "active_plan_execution_status": "planned",
            "blocking_issue_count": 1,
            "blocking_issues": ["必须优先修复：External validation cohort is still missing."],
            "next_review_focus": ["What is the narrowest supplementary analysis needed to restore endpoint provenance support?"],
            "re_review_ready": False,
            "summary": "当前已经形成结构化质量修订计划，下一步应先执行修订，再回到 MAS 做复评。",
            "recommended_next_action": "Controller must decide whether to invest in external validation.",
        },
        "requires_controller_decision": True,
        "promotion_gate_status": {
            "status": "blocked",
            "allow_write": False,
            "current_required_action": "return_to_publishability_gate",
            "blockers": ["missing_post_main_publishability_gate"],
            "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
            "medical_publication_surface_route_back_recommendation": "return_to_analysis_campaign",
        },
    }
    assert module.read_promotion_gate(study_root=study_root) == promotion_gate_payload
    assert module.read_evaluation_summary(study_root=study_root) == evaluation_summary_payload


def test_materialize_evaluation_summary_artifacts_rejects_runtime_escalation_ref_mismatch(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    gate_report_path = inputs["gate_report_path"]

    with pytest.raises(ValueError, match="runtime escalation ref mismatch"):
        module.materialize_evaluation_summary_artifacts(
            study_root=study_root,
            runtime_escalation_ref={
                "record_id": "runtime-escalation::wrong",
                "artifact_path": str(inputs["runtime_escalation_path"]),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "wrong_launch_report.json"),
            },
            publishability_gate_report_ref=gate_report_path,
        )


def test_materialize_evaluation_summary_artifacts_rejects_charter_context_drift(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    gate_report_path = inputs["gate_report_path"]
    publication_eval_path = inputs["publication_eval_path"]
    publication_eval_payload = dict(inputs["publication_eval_payload"])
    publication_eval_payload["charter_context_ref"] = {
        "ref": str(inputs["charter_path"]),
        "charter_id": "charter::001-risk::v1",
        "publication_objective": "mismatched objective",
    }
    _write_json(publication_eval_path, publication_eval_payload)

    with pytest.raises(ValueError, match="publication objective mismatch"):
        module.materialize_evaluation_summary_artifacts(
            study_root=study_root,
            runtime_escalation_ref=str(inputs["runtime_escalation_path"]),
            publishability_gate_report_ref=gate_report_path,
        )


def test_read_evaluation_summary_rejects_non_object_payload(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    evaluation_summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    _write_json(evaluation_summary_path, ["not", "an", "object"])

    with pytest.raises(ValueError, match="JSON object"):
        module.read_evaluation_summary(study_root=study_root)


def test_materialize_evaluation_summary_artifacts_prefers_now_priority_route_repair_plan(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    publication_eval_path = inputs["publication_eval_path"]
    gate_report_path = inputs["gate_report_path"]
    publication_eval_payload = dict(inputs["publication_eval_payload"])
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "action-010",
            "action_type": "bounded_analysis",
            "priority": "next",
            "reason": "Prepare sensitivity analysis after the main repair.",
            "route_target": "analysis-campaign",
            "route_key_question": "What bounded robustness check should run after the main repair?",
            "route_rationale": "This remains a next-step bounded analysis.",
            "evidence_refs": [str(gate_report_path)],
            "requires_controller_decision": True,
        },
        {
            "action_id": "action-011",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Repair the manuscript claim-evidence surface first.",
            "route_target": "write",
            "route_key_question": "What is the narrowest paper-writing repair needed before any follow-up analysis?",
            "route_rationale": "The current blocker sits on the write surface, so same-line repair should start there.",
            "evidence_refs": [str(inputs["runtime_escalation_path"])],
            "requires_controller_decision": True,
        },
    ]
    _write_json(publication_eval_path, publication_eval_payload)

    module.materialize_evaluation_summary_artifacts(
        study_root=study_root,
        runtime_escalation_ref=str(inputs["runtime_escalation_path"]),
        publishability_gate_report_ref=gate_report_path,
    )

    evaluation_summary_payload = module.read_evaluation_summary(study_root=study_root)

    assert evaluation_summary_payload["route_repair_plan"] == {
        "action_id": "action-011",
        "action_type": "route_back_same_line",
        "priority": "now",
        "route_target": "write",
        "route_key_question": "What is the narrowest paper-writing repair needed before any follow-up analysis?",
        "route_rationale": "The current blocker sits on the write surface, so same-line repair should start there.",
    }


def test_materialize_evaluation_summary_artifacts_prefers_reviewer_style_agenda_fields(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    publication_eval_path = inputs["publication_eval_path"]
    gate_report_path = inputs["gate_report_path"]
    publication_eval_payload = dict(inputs["publication_eval_payload"])
    quality_assessment = dict(publication_eval_payload["quality_assessment"])
    quality_assessment["evidence_strength"] = {
        "status": "blocked",
        "summary": "The current claim-evidence surface is still missing external validation support.",
        "evidence_refs": [str(gate_report_path)],
        "reviewer_reason": "证据链仍有硬缺口：外部验证结果还未进入可复核闭环。",
        "reviewer_revision_advice": "先补齐外部验证并重写对应结果段，再做下一轮门控复评。",
        "reviewer_next_round_focus": "复评时重点核对外部验证结果与主结论是否一一对应。",
    }
    publication_eval_payload["quality_assessment"] = quality_assessment
    monkeypatch.setattr(
        module,
        "read_publication_eval_latest",
        lambda *, study_root: publication_eval_payload,
    )

    module.materialize_evaluation_summary_artifacts(
        study_root=study_root,
        runtime_escalation_ref=str(inputs["runtime_escalation_path"]),
        publishability_gate_report_ref=gate_report_path,
    )

    summary = module.read_evaluation_summary(study_root=study_root)

    assert summary["quality_review_agenda"] == {
        "top_priority_issue": "证据链仍有硬缺口：外部验证结果还未进入可复核闭环。",
        "suggested_revision": "先补齐外部验证并重写对应结果段，再做下一轮门控复评。",
        "next_review_focus": "复评时重点核对外部验证结果与主结论是否一一对应。",
        "agenda_summary": (
            "优先修复：证据链仍有硬缺口：外部验证结果还未进入可复核闭环。；"
            "建议修订：先补齐外部验证并重写对应结果段，再做下一轮门控复评。；"
            "下一轮复评重点：复评时重点核对外部验证结果与主结论是否一一对应。"
        ),
    }
    assert summary["quality_revision_plan"] == {
        "policy_id": "medical_publication_critique_v1",
        "plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "execution_status": "planned",
        "overall_diagnosis": "核心科学质量还没有闭环；当前应先回到 analysis-campaign 完成最窄补充修复。",
        "weight_contract": {
            "clinical_significance": 25,
            "evidence_strength": 35,
            "novelty_positioning": 20,
            "human_review_readiness": 20,
        },
        "items": [
            {
                "item_id": "quality-revision-item-1",
                "priority": "p0",
                "dimension": "evidence_strength",
                "action_type": "close_evidence_gap",
                "action": "先补齐外部验证并重写对应结果段，再做下一轮门控复评。",
                "rationale": "证据链仍有硬缺口：外部验证结果还未进入可复核闭环。",
                "done_criteria": "下一轮复评能够明确确认：复评时重点核对外部验证结果与主结论是否一一对应。",
                "route_target": "analysis-campaign",
            }
        ],
        "next_review_focus": ["复评时重点核对外部验证结果与主结论是否一一对应。"],
    }
    assert summary["quality_review_loop"] == {
        "policy_id": "medical_publication_critique_v1",
        "loop_id": "quality-review-loop::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "closure_state": "quality_repair_required",
        "lane_id": "claim_evidence",
        "current_phase": "revision_required",
        "current_phase_label": "修订待执行",
        "recommended_next_phase": "revision",
        "recommended_next_phase_label": "执行修订",
        "active_plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "active_plan_execution_status": "planned",
        "blocking_issue_count": 1,
        "blocking_issues": ["证据链仍有硬缺口：外部验证结果还未进入可复核闭环。"],
        "next_review_focus": ["复评时重点核对外部验证结果与主结论是否一一对应。"],
        "re_review_ready": False,
        "summary": "当前已经形成结构化质量修订计划，下一步应先执行修订，再回到 MAS 做复评。",
        "recommended_next_action": "先补齐外部验证并重写对应结果段，再做下一轮门控复评。",
    }


def test_materialize_evaluation_summary_artifacts_projects_bundle_only_remaining_quality_closure(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    publication_eval_path = inputs["publication_eval_path"]
    gate_report_path = inputs["gate_report_path"]
    publication_eval_payload = dict(inputs["publication_eval_payload"])
    publication_eval_payload["verdict"] = {
        "overall_verdict": "blocked",
        "primary_claim_status": "supported",
        "summary": "Core science is closed; remaining work is finalize-stage package hardening.",
        "stop_loss_pressure": "none",
    }
    publication_eval_payload["quality_assessment"] = {
        "clinical_significance": {
            "status": "ready",
            "summary": "Clinical framing and result surface are already reviewable.",
            "evidence_refs": [str(gate_report_path)],
        },
        "evidence_strength": {
            "status": "ready",
            "summary": "Core evidence is already closed; remaining issues are downstream-only.",
            "evidence_refs": [str(gate_report_path)],
        },
        "novelty_positioning": {
            "status": "ready",
            "summary": "Contribution boundaries are already frozen in the charter and manuscript lane.",
            "evidence_refs": [str(inputs["charter_path"])],
        },
        "human_review_readiness": {
            "status": "partial",
            "summary": "Current package still needs one more finalize pass before human audit.",
            "evidence_refs": [str(gate_report_path)],
        },
    }
    _write_json(publication_eval_path, publication_eval_payload)
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
        },
    )

    module.materialize_evaluation_summary_artifacts(
        study_root=study_root,
        runtime_escalation_ref=str(inputs["runtime_escalation_path"]),
        publishability_gate_report_ref=gate_report_path,
    )

    evaluation_summary_payload = module.read_evaluation_summary(study_root=study_root)

    assert evaluation_summary_payload["quality_closure_truth"] == {
        "state": "bundle_only_remaining",
        "summary": "核心科学质量已经闭环；剩余工作收口在 finalize / submission bundle，同一论文线可以继续自动推进。",
        "current_required_action": "complete_bundle_stage",
        "route_target": "finalize",
    }
    assert evaluation_summary_payload["quality_closure_basis"]["publication_gate"] == {
        "status": "partial",
        "summary": "核心科学面已经闭环；剩余阻塞只落在当前论文线的 finalize / bundle 收口。",
        "evidence_refs": [str((study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json").resolve())],
    }
    assert evaluation_summary_payload["quality_revision_plan"] == {
        "policy_id": "medical_publication_critique_v1",
        "plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "execution_status": "planned",
        "overall_diagnosis": "核心科学质量已经闭环；剩余工作收口在 finalize / submission bundle，同一论文线可以继续自动推进。",
        "weight_contract": {
            "clinical_significance": 25,
            "evidence_strength": 35,
            "novelty_positioning": 20,
            "human_review_readiness": 20,
        },
        "items": [
            {
                "item_id": "quality-revision-item-1",
                "priority": "p0",
                "dimension": "human_review_readiness",
                "action_type": "stabilize_submission_bundle",
                "action": "先在 finalize 修订，完成当前最小投稿包收口。",
                "rationale": "核心科学质量已经闭环；剩余工作收口在 finalize / submission bundle，同一论文线可以继续自动推进。",
                "done_criteria": "下一轮复评能够明确确认：当前论文线还差哪一步 finalize / submission bundle 收口？",
                "route_target": "finalize",
            }
        ],
        "next_review_focus": ["当前论文线还差哪一步 finalize / submission bundle 收口？"],
    }
    assert evaluation_summary_payload["quality_review_loop"] == {
        "policy_id": "medical_publication_critique_v1",
        "loop_id": "quality-review-loop::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "closure_state": "bundle_only_remaining",
        "lane_id": "submission_hardening",
        "current_phase": "bundle_hardening",
        "current_phase_label": "投稿包收口",
        "recommended_next_phase": "finalize",
        "recommended_next_phase_label": "定稿与投稿收尾",
        "active_plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "active_plan_execution_status": "planned",
        "blocking_issue_count": 1,
        "blocking_issues": ["核心科学质量已经闭环；剩余工作收口在 finalize / submission bundle，同一论文线可以继续自动推进。"],
        "next_review_focus": ["当前论文线还差哪一步 finalize / submission bundle 收口？"],
        "re_review_ready": False,
        "summary": "核心科学质量已经闭环，当前只剩投稿包与人工审阅面的收口修订。",
        "recommended_next_action": "先在 finalize 修订，完成当前最小投稿包收口。",
    }


def test_read_evaluation_summary_derives_quality_review_agenda_when_missing(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    gate_report_path = inputs["gate_report_path"]

    module.materialize_evaluation_summary_artifacts(
        study_root=study_root,
        runtime_escalation_ref=str(inputs["runtime_escalation_path"]),
        publishability_gate_report_ref=gate_report_path,
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload.pop("quality_review_agenda", None)
    payload.pop("quality_revision_plan", None)
    payload.pop("quality_review_loop", None)
    _write_json(summary_path, payload)

    summary = module.read_evaluation_summary(study_root=study_root)

    assert summary["quality_review_agenda"] == {
        "top_priority_issue": "核心科学质量还没有闭环；当前应先回到 analysis-campaign 完成最窄补充修复。",
        "suggested_revision": (
            "先在 analysis-campaign 修订："
            "The study direction remains valid; only a bounded analysis-campaign repair is needed."
        ),
        "next_review_focus": "What is the narrowest supplementary analysis needed to restore endpoint provenance support?",
        "agenda_summary": (
            "优先修复：核心科学质量还没有闭环；当前应先回到 analysis-campaign 完成最窄补充修复。；"
            "建议修订：先在 analysis-campaign 修订：The study direction remains valid; only a bounded analysis-campaign repair is needed.；"
            "下一轮复评重点：What is the narrowest supplementary analysis needed to restore endpoint provenance support?"
        ),
    }
    assert summary["quality_revision_plan"] == {
        "policy_id": "medical_publication_critique_v1",
        "plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "execution_status": "planned",
        "overall_diagnosis": "核心科学质量还没有闭环；当前应先回到 analysis-campaign 完成最窄补充修复。",
        "weight_contract": {
            "clinical_significance": 25,
            "evidence_strength": 35,
            "novelty_positioning": 20,
            "human_review_readiness": 20,
        },
        "items": [
            {
                "item_id": "quality-revision-item-1",
                "priority": "p0",
                "dimension": "evidence_strength",
                "action_type": "close_evidence_gap",
                "action": (
                    "先在 analysis-campaign 修订："
                    "The study direction remains valid; only a bounded analysis-campaign repair is needed."
                ),
                "rationale": "核心科学质量还没有闭环；当前应先回到 analysis-campaign 完成最窄补充修复。",
                "done_criteria": (
                    "下一轮复评能够明确确认："
                    "What is the narrowest supplementary analysis needed to restore endpoint provenance support?"
                ),
                "route_target": "analysis-campaign",
            }
        ],
        "next_review_focus": [
            "What is the narrowest supplementary analysis needed to restore endpoint provenance support?"
        ],
    }
    assert summary["quality_review_loop"] == {
        "policy_id": "medical_publication_critique_v1",
        "loop_id": "quality-review-loop::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "closure_state": "quality_repair_required",
        "lane_id": "claim_evidence",
        "current_phase": "revision_required",
        "current_phase_label": "修订待执行",
        "recommended_next_phase": "revision",
        "recommended_next_phase_label": "执行修订",
        "active_plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "active_plan_execution_status": "planned",
        "blocking_issue_count": 1,
        "blocking_issues": ["核心科学质量还没有闭环；当前应先回到 analysis-campaign 完成最窄补充修复。"],
        "next_review_focus": ["What is the narrowest supplementary analysis needed to restore endpoint provenance support?"],
        "re_review_ready": False,
        "summary": "当前已经形成结构化质量修订计划，下一步应先执行修订，再回到 MAS 做复评。",
        "recommended_next_action": (
            "先在 analysis-campaign 修订："
            "The study direction remains valid; only a bounded analysis-campaign repair is needed."
        ),
    }


def test_read_evaluation_summary_derives_quality_execution_lane_when_missing(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    gate_report_path = inputs["gate_report_path"]

    module.materialize_evaluation_summary_artifacts(
        study_root=study_root,
        runtime_escalation_ref=str(inputs["runtime_escalation_path"]),
        publishability_gate_report_ref=gate_report_path,
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    expected_lane = payload["quality_execution_lane"]
    payload.pop("quality_execution_lane", None)
    _write_json(summary_path, payload)

    summary = module.read_evaluation_summary(study_root=study_root)

    assert summary["quality_execution_lane"] == expected_lane


def test_read_evaluation_summary_projects_re_review_required_loop_when_plan_completed(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    gate_report_path = inputs["gate_report_path"]

    module.materialize_evaluation_summary_artifacts(
        study_root=study_root,
        runtime_escalation_ref=str(inputs["runtime_escalation_path"]),
        publishability_gate_report_ref=gate_report_path,
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload["quality_revision_plan"]["execution_status"] = "completed"
    payload.pop("quality_review_loop", None)
    _write_json(summary_path, payload)

    summary = module.read_evaluation_summary(study_root=study_root)

    assert summary["quality_review_loop"] == {
        "policy_id": "medical_publication_critique_v1",
        "loop_id": "quality-review-loop::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "closure_state": "quality_repair_required",
        "lane_id": "claim_evidence",
        "current_phase": "re_review_required",
        "current_phase_label": "等待复评",
        "recommended_next_phase": "re_review",
        "recommended_next_phase_label": "发起复评",
        "active_plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "active_plan_execution_status": "completed",
        "blocking_issue_count": 1,
        "blocking_issues": ["必须优先修复：External validation cohort is still missing."],
        "next_review_focus": ["What is the narrowest supplementary analysis needed to restore endpoint provenance support?"],
        "re_review_ready": True,
        "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。",
        "recommended_next_action": "发起下一轮 MAS quality re-review，确认当前 blocking issues 是否已真正闭环。",
    }
