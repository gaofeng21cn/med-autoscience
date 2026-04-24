from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_read_evaluation_summary_overrides_stale_bundle_only_agenda_with_latest_task_intake_scope(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    inputs = _stable_inputs(tmp_path)
    study_root = inputs["study_root"]
    publication_eval_path = inputs["publication_eval_path"]
    gate_report_path = inputs["gate_report_path"]
    publication_eval_payload = dict(inputs["publication_eval_payload"])
    publication_eval_payload["verdict"] = {
        "overall_verdict": "promising",
        "primary_claim_status": "supported",
        "summary": "bundle-stage work is unlocked and can proceed on the critical path",
        "stop_loss_pressure": "none",
    }
    publication_eval_payload["quality_assessment"] = {
        "clinical_significance": {
            "status": "partial",
            "summary": "主临床问题与结果表面已具备，但 charter 里还缺更显式的 clinician-facing interpretation target。",
            "reviewer_reason": "主临床问题与结果表面已具备，但 clinician-facing interpretation target 仍未显式冻结。",
            "reviewer_revision_advice": "在 charter 补齐 clinician-facing interpretation target，再做临床叙事定稿。",
            "reviewer_next_round_focus": "下一轮重点确认解释目标是否能覆盖主临床结论的每一条关键陈述。",
            "evidence_refs": [str(gate_report_path)],
        },
        "evidence_strength": {
            "status": "ready",
            "summary": "核心科学证据链已经清楚，当前剩余问题位于交付/刷新层。",
            "reviewer_reason": "核心科学证据链已经清楚，当前剩余问题位于交付/刷新层。",
            "reviewer_revision_advice": "核心证据链已达标，下一轮优先清理交付与刷新层阻塞，避免再次影响审阅入口。",
            "reviewer_next_round_focus": "下一轮重点确认 current package 与 submission surfaces 的刷新时序。",
            "evidence_refs": [str(gate_report_path)],
        },
        "novelty_positioning": {
            "status": "underdefined",
            "summary": "当前 charter 还缺显式的 scientific follow-up 或 explanation targets，创新性 framing 仍偏弱。",
            "reviewer_reason": "当前 charter 缺少显式 scientific follow-up 或 explanation targets，创新性 framing 仍偏弱。",
            "reviewer_revision_advice": "先在 charter 增补可审计的 scientific follow-up questions 或 explanation targets。",
            "reviewer_next_round_focus": "补齐 scientific follow-up questions 或 explanation targets，再复核创新叙事与主结论边界。",
            "evidence_refs": [str(inputs["charter_path"])],
        },
        "human_review_readiness": {
            "status": "ready",
            "summary": "给人看的 current_package 和 submission_minimal 已同步到最新真相，可以进入人工审阅。",
            "reviewer_reason": "current_package 与 submission_minimal 已同步到最新真相，人工审阅入口已就绪。",
            "reviewer_revision_advice": "保持当前交付状态并仅做事实一致性修订。",
            "reviewer_next_round_focus": "下一轮重点复核审阅包中的引用路径与提交清单一致性。",
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
            "recommended_action": "continue_bundle_stage",
            "latest_gate_path": str(gate_report_path),
            "supervisor_phase": "bundle_stage_ready",
            "current_required_action": "continue_bundle_stage",
            "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
            "blockers": ["registry_contract_mismatch"],
        },
    )
    _write_reporting_contract_task_intake(study_root)

    module.materialize_evaluation_summary_artifacts(
        study_root=study_root,
        runtime_escalation_ref=str(inputs["runtime_escalation_path"]),
        publishability_gate_report_ref=gate_report_path,
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload["quality_review_agenda"] = {
        "top_priority_issue": "当前 charter 缺少显式 scientific follow-up 或 explanation targets，创新性 framing 仍偏弱。",
        "suggested_revision": "先在 charter 增补可审计的 scientific follow-up questions 或 explanation targets。",
        "next_review_focus": "补齐 scientific follow-up questions 或 explanation targets，再复核创新叙事与主结论边界。",
    }
    payload["quality_revision_plan"] = {
        "policy_id": "medical_publication_critique_v1",
        "plan_id": "quality-revision-plan::stale",
        "execution_status": "in_progress",
        "overall_diagnosis": "核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。",
        "weight_contract": {
            "clinical_significance": 25,
            "evidence_strength": 35,
            "novelty_positioning": 20,
            "human_review_readiness": 20,
        },
        "items": [
            {
                "item_id": "quality-revision-item-1",
                "priority": "p1",
                "dimension": "novelty_positioning",
                "action_type": "stabilize_submission_bundle",
                "action": "先在 charter 增补可审计的 scientific follow-up questions 或 explanation targets。",
                "rationale": "当前 charter 缺少显式 scientific follow-up 或 explanation targets，创新性 framing 仍偏弱。",
                "done_criteria": "下一轮复评能够明确确认：补齐 scientific follow-up questions 或 explanation targets，再复核创新叙事与主结论边界。",
                "route_target": "finalize",
            }
        ],
        "next_review_focus": ["补齐 scientific follow-up questions 或 explanation targets，再复核创新叙事与主结论边界。"],
    }
    _write_json(summary_path, payload)

    summary = module.read_evaluation_summary(study_root=study_root)

    assert summary["quality_review_agenda"] == {
        "top_priority_issue": "当前任务范围已收窄到 reporting/display contract mismatch；现阶段不要重开 manuscript evidence adequacy 或 scientific claims。",
        "suggested_revision": "对齐 reporting contract、display registry 与必需 shell/input surfaces，让 current package 与已接受展示包保持一致。",
        "next_review_focus": "复核 medical_reporting_audit、runtime_watch 与 publication gate 状态是否已清掉 stale reporting blockers。",
        "agenda_summary": (
            "优先修复：当前任务范围已收窄到 reporting/display contract mismatch；现阶段不要重开 manuscript evidence adequacy 或 scientific claims。；"
            "建议修订：对齐 reporting contract、display registry 与必需 shell/input surfaces，让 current package 与已接受展示包保持一致。；"
            "下一轮复评重点：复核 medical_reporting_audit、runtime_watch 与 publication gate 状态是否已清掉 stale reporting blockers。"
        ),
    }
    assert summary["quality_revision_plan"] == {
        "policy_id": "medical_publication_critique_v1",
        "plan_id": "quality-revision-plan::stale",
        "execution_status": "in_progress",
        "overall_diagnosis": "核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。",
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
                "action": "对齐 reporting contract、display registry 与必需 shell/input surfaces，让 current package 与已接受展示包保持一致。",
                "rationale": "当前任务范围已收窄到 reporting/display contract mismatch；现阶段不要重开 manuscript evidence adequacy 或 scientific claims。",
                "done_criteria": "下一轮复评能够明确确认：复核 medical_reporting_audit、runtime_watch 与 publication gate 状态是否已清掉 stale reporting blockers。",
                "route_target": "finalize",
            }
        ],
        "next_review_focus": ["复核 medical_reporting_audit、runtime_watch 与 publication gate 状态是否已清掉 stale reporting blockers。"],
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
def test_read_evaluation_summary_derives_quality_execution_lane_when_non_mapping(tmp_path: Path) -> None:
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
    payload["quality_execution_lane"] = "legacy-string-payload"
    _write_json(summary_path, payload)

    summary = module.read_evaluation_summary(study_root=study_root)

    assert summary["quality_execution_lane"] == expected_lane
def test_read_evaluation_summary_derives_same_line_route_surface_when_missing(tmp_path: Path) -> None:
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
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    expected_surface = payload["same_line_route_surface"]
    payload.pop("same_line_route_surface", None)
    _write_json(summary_path, payload)

    summary = module.read_evaluation_summary(study_root=study_root)

    assert summary["same_line_route_surface"] == expected_surface
def test_read_evaluation_summary_derives_same_line_route_truth_when_missing(tmp_path: Path) -> None:
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
    expected_truth = payload["same_line_route_truth"]
    payload.pop("same_line_route_truth", None)
    _write_json(summary_path, payload)

    summary = module.read_evaluation_summary(study_root=study_root)

    assert summary["same_line_route_truth"] == expected_truth
def test_read_evaluation_summary_derives_same_line_route_truth_when_non_mapping(tmp_path: Path) -> None:
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
    expected_truth = payload["same_line_route_truth"]
    payload["same_line_route_truth"] = "legacy-string-payload"
    _write_json(summary_path, payload)

    summary = module.read_evaluation_summary(study_root=study_root)

    assert summary["same_line_route_truth"] == expected_truth
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
