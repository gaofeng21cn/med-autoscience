from __future__ import annotations

from typing import Any, Iterable

from med_autoscience.study_task_intake_stop_loss import (
    build_publishability_stop_loss_intake,
    task_intake_requests_publishability_stop_loss,
)
from med_autoscience.submission_revision_operating_contract import build_submission_revision_operating_contract

DIRECT_FINALIZE_DOWNGRADE_MARKERS = (
    "不能按已达投稿包里程碑直接收口",
    "不得直接按外投收口",
    "submission-ready/finalize 判断降回",
    "降回待修订后再评估",
    "downgrade the current submission-ready/finalize judgment",
)
REVIEWER_REVISION_MARKERS = (
    "reviewer feedback",
    "reviewer comment",
    "review comments",
    "reviewer revision",
    "major revision",
    "major revisions",
    "reviewer-first revision",
    "reviewer first revision",
    "manuscript revision",
    "manuscript-change",
    "paper revision",
    "revise manuscript",
    "revision checklist",
    "explicit user feedback",
    "user feedback",
    "review matrix",
    "action matrix",
    "导师反馈",
    "专家反馈",
    "审稿意见",
    "审稿人意见",
    "审稿式反馈",
    "论文修改",
    "稿件修改",
    "修改意见",
    "大修改",
    "显式重新激活同一论文线",
    "重新激活同一论文线",
    "结构性返修",
    "revision/rebuttal",
    "投稿前必须修正",
    "补分析",
    "改表",
    "改图",
    "introduction feedback",
    "methods feedback",
    "results feedback",
    "figure feedback",
    "table feedback",
    "scientific revision feedback",
    "table/figure legends",
    "tripod",
    "probast",
)
REVISION_INTAKE_CHECKLIST: tuple[tuple[str, str, str], ...] = (
    ("text_revisions", "text revisions", "Introduction/Methods/Results/Discussion 等文字修订点已逐条定位。"),
    ("methods_completeness", "methods completeness", "方法学补充、数据来源、纳排、变量和流程说明已补齐或记录为缺口。"),
    ("statistical_analysis", "statistical analysis", "新增或修订统计分析、敏感性/亚组/稳健性需求已绑定证据来源。"),
    ("tables_figures", "tables/figures", "表格、图片、图注和补充材料改动范围已列明。"),
    ("follow_up_evidence", "follow-up evidence", "后续证据、补充结果和不可完成项有明确状态。"),
    (
        "scientific_finding_pattern",
        "scientific finding pattern",
        "描述性结果必须提升为结构化 phenotype pattern、rate-count/service-priority contrast 或等价医学发现问题。",
    ),
    (
        "analysis_gap_route_back",
        "analysis gap route-back",
        "calendar-year、repeated-visit、site variance 等未有证据的问题必须登记为 analysis-campaign gap，不能编入结果。",
    ),
    ("discussion_claim_guardrails", "discussion/claim guardrails", "讨论、结论和 claim 边界没有越过当前证据包。"),
    (
        "figure_table_terminology_retention",
        "Figure/Table terminology and supplementary retention",
        "Figure/Table 术语、rate/count 分离、supplementary retention 与图表证据边界进入质量门禁。",
    ),
    ("coverage_audit", "coverage audit", "大修改 closeout 必须逐条覆盖反馈、修订动作、证据 refs、未完成项和 owner/readback 状态。"),
    ("handoff_evidence_surface", "handoff/evidence surface", "durable handoff 写明数据源、脚本入口、输出表图、改动范围、claim guardrails 与 canonical source 回灌状态。"),
)
REVIEWER_REVISION_COVERAGE_AUDIT_REQUIREMENT = {
    "surface_kind": "mas_reviewer_revision_coverage_audit_requirement",
    "required_for_closeout": True,
    "minimum_fields": [
        "feedback_item_id",
        "requested_change",
        "revision_action",
        "status",
        "evidence_refs",
        "remaining_gap_or_not_applicable_reason",
        "owner_readback_ref",
    ],
    "accepted_statuses": ["covered", "not_applicable_with_reason", "blocked_with_owner"],
    "closeout_without_audit_allowed": False,
}
REVIEWER_REVISION_STAGE_ATTEMPT_READBACK_REQUIREMENT = {
    "surface_kind": "mas_reviewer_revision_stage_attempt_readback_requirement",
    "required_for_closeout": True,
    "must_preserve_professional_skill_invocation_refs": True,
    "professional_skill_ref_families": [
        "medical-manuscript-writing",
        "medical-manuscript-review",
        "medical-statistical-review",
        "medical-table-design",
        "medical-figure-design",
        "medical-submission-prep",
    ],
    "required_observability_fields": ["duration", "token_usage", "cost"],
    "missing_reason_fields": [
        "missing_duration_reason",
        "missing_token_usage_reason",
        "missing_cost_reason",
    ],
    "missing_reason_policy": "typed_missing_reason_required; do_not_coerce_to_zero",
}
REVIEWER_REVISION_SELF_EVOLUTION_AUTHORITY_BOUNDARY = {
    "mas": "study_truth_publication_quality_and_artifact_authority",
    "opl": "agent_lab_runtime_and_work_order_status_projection",
    "oma": "refs_only_developer_work_order_materialization",
    "can_write_study_truth": False,
    "can_write_owner_receipt": False,
    "can_write_typed_blocker": False,
    "can_write_human_gate": False,
    "can_mutate_current_package": False,
    "can_authorize_publication_ready": False,
}
FEEDBACKOPS_ACCEPTED_PROFILE = "target_agent_feedback_external_suite"
REVIEWER_REVISION_FEEDBACK_PROFILE = "reviewer_revision_feedback"
FEEDBACKOPS_TARGET_AGENT_ID = "med-autoscience"
OPL_FEEDBACKOPS_STANDARD_AGENT_ID = "mas"
DEVELOPER_MODE_EXECUTION_GATE_REFS = [
    "opl-developer-mode:repo-fix-execution",
    "workspace-profile-ref:developer_supervisor_mode",
    "workspace-profile-ref:github_username",
    "workspace-profile-ref:mas_developer_github_usernames",
]
PAPER_MISSION_SUBORDINATION = {
    "surface_kind": "mas_paper_mission_subordination",
    "authority_owner": "MedAutoScience",
    "mainline_route": [
        "PaperMission",
        "submission_authority",
        "submission_authority_owner_gate_or_typed_blocker",
    ],
    "control_plane_role": "subordinate_input_or_advisory_only",
    "can_start_parallel_mainline": False,
    "can_bypass_submission_authority": False,
    "can_close_without_owner_gate_or_typed_blocker": False,
}


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalized_strings(values: Iterable[object]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            normalized.append(text)
    return normalized


def _task_intake_text_corpus(payload: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()
    values: list[object] = [
        payload.get("task_intent"),
        *(payload.get("constraints") or []),
        *(payload.get("evidence_boundary") or []),
        *(payload.get("trusted_inputs") or []),
        *(payload.get("reference_papers") or []),
        *(payload.get("first_cycle_outputs") or []),
    ]
    return tuple(_normalized_strings(values))


def _task_intake_contains_any(payload: dict[str, Any] | None, markers: tuple[str, ...]) -> bool:
    corpus = _task_intake_text_corpus(payload)
    if not corpus:
        return False
    for text in corpus:
        lowered = text.lower()
        if any(marker.lower() in lowered for marker in markers):
            return True
    return False


def _task_intake_kind(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    return _non_empty_text(payload.get("task_intake_kind")) or _non_empty_text(payload.get("intake_kind"))


def task_intake_is_reviewer_revision(payload: dict[str, Any] | None) -> bool:
    if task_intake_requests_publishability_stop_loss(payload):
        return False
    if _task_intake_kind(payload) == "reviewer_revision":
        return True
    return _task_intake_contains_any(payload, REVIEWER_REVISION_MARKERS)


def task_intake_requests_submission_package_refresh(payload: dict[str, Any] | None) -> bool:
    return _task_intake_contains_any(payload, DIRECT_FINALIZE_DOWNGRADE_MARKERS)


def submission_revision_operating_state(payload: dict[str, Any] | None) -> str | None:
    if task_intake_requests_publishability_stop_loss(payload):
        return None
    if task_intake_is_reviewer_revision(payload):
        return "reviewer_revision"
    if task_intake_requests_submission_package_refresh(payload):
        return "submission_package_refresh"
    return None


def build_reviewer_revision_intake(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not task_intake_is_reviewer_revision(payload):
        return None
    selected_lane = build_reviewer_revision_execution_lane_projection(payload)
    revision_payload = {
        "kind": "reviewer_revision",
        "status": "active",
        "selected_revision_execution_lane": selected_lane,
        "checklist": [item_id for item_id, _, _ in REVISION_INTAKE_CHECKLIST],
        "checklist_items": [
            {"id": item_id, "label": label, "status": "pending", "requirement": requirement}
            for item_id, label, requirement in REVISION_INTAKE_CHECKLIST
        ],
        "handoff_required": True,
        "reactivation_required": True,
        "reactivation_policy": {
            "same_study_line": True,
            "stopped_milestone_reopens_same_line": True,
            "required_sequence": [
                "submit durable reviewer_revision task intake",
                "reactivate the same study through OPL current_control_state using MAS owner refs",
                "apply revisions to controller-authorized canonical paper sources",
                "regenerate manuscript/current_package from canonical authority",
            ],
        },
        "current_package_edit_policy": {
            "surface_kind": "human_facing_projection",
            "direct_current_package_edit_allowed": False,
            "emergency_overlay_only": True,
            "completion_claim_allowed": False,
        },
        "submission_revision_operating_contract": build_submission_revision_operating_contract(
            "reviewer_revision",
            trigger="reviewer_revision_task_intake",
        ),
        "handoff_evidence_surface": {
            "required": True,
            "read_before_mds_resume": True,
            "minimum_fields": [
                "data sources",
                "script entrypoints",
                "changed tables/figures",
                "change scope",
                "claim guardrails",
                "canonical source reconciliation status",
                "next owner: MAS controller or MDS paper surface",
            ],
        },
        "closeout_acceptance_requirements": {
            "coverage_audit": dict(REVIEWER_REVISION_COVERAGE_AUDIT_REQUIREMENT),
            "stage_attempt_readback": dict(REVIEWER_REVISION_STAGE_ATTEMPT_READBACK_REQUIREMENT),
        },
        "self_evolution_trigger": build_reviewer_revision_self_evolution_trigger(payload),
    }
    fast_lane = _build_manuscript_fast_lane_contract(payload)
    if fast_lane is not None:
        revision_payload["manuscript_fast_lane"] = fast_lane
    return revision_payload


def build_reviewer_revision_execution_lane_projection(
    payload: dict[str, Any] | None,
    *,
    owner_callable_receipt_ref: str | None = None,
) -> dict[str, Any]:
    if _task_intake_requests_manuscript_fast_lane(payload):
        return {
            "surface_kind": "mas_selected_reviewer_revision_execution_lane",
            "lane_id": "manuscript_fast_lane",
            "selected_by": "MAS task_intake",
            "agent_lab_suite_required": False,
            "agent_lab_suite_status": "bypassed",
            "summary": (
                "MAS task_intake selected manuscript_fast_lane: small-scope existing-evidence-only "
                "manuscript repair; Agent Lab is not run for this lane."
            ),
        }

    materialization = payload.get("agent_lab_suite_materialization") if isinstance(payload, dict) else None
    suite_status = _non_empty_text(materialization.get("status")) if isinstance(materialization, dict) else None
    trigger = build_reviewer_revision_self_evolution_trigger(payload)
    contract_triggers_execution = (
        trigger["agent_lab_suite_materialization"]["contract_itself_triggers_execution"] is True
    )
    if _non_empty_text(owner_callable_receipt_ref) is not None:
        return {
            "surface_kind": "mas_selected_reviewer_revision_execution_lane",
            "lane_id": "owner_callable_foreground",
            "selected_by": "MAS owner callable receipt/evidence",
            "agent_lab_suite_required": True,
            "agent_lab_suite_status": suite_status or "pending",
            "owner_callable_receipt_ref": owner_callable_receipt_ref,
            "summary": (
                "MAS readback selected owner_callable_foreground: this is a foreground MAS owner callable "
                "repair receipt/evidence path, not a full OPL stage execution claim."
            ),
        }
    if suite_status == "materialized" and not contract_triggers_execution:
        dispatch_request = build_reviewer_revision_feedbackops_dispatch_request(payload)
        return {
            "surface_kind": "mas_selected_reviewer_revision_execution_lane",
            "lane_id": "oma_self_evolution_pending",
            "selected_by": "MAS Agent Lab suite materialization",
            "agent_lab_suite_required": True,
            "agent_lab_suite_status": "materialized",
            "contract_itself_triggers_execution": False,
            "suite_path": materialization.get("suite_path") if isinstance(materialization, dict) else None,
            "feedbackops_dispatch_request_status": dispatch_request["status"],
            "next_owner": "one-person-lab.feedbackops_then_opl-meta-agent",
            "summary": (
                "MAS materialized the Agent Lab suite and selected oma_self_evolution_pending: OMA has a "
                "pending action via OPL FeedbackOps; the contract itself does not mean the suite was executed."
            ),
        }
    return {
        "surface_kind": "mas_selected_reviewer_revision_execution_lane",
        "lane_id": "reviewer_revision_general",
        "selected_by": "MAS task_intake",
        "agent_lab_suite_required": True,
        "agent_lab_suite_status": suite_status or "pending",
        "summary": (
            "MAS task_intake selected reviewer_revision_general: same-line write/analysis revision; "
            "Agent Lab suite must be materialized or remain explicitly pending before OMA execution."
        ),
    }


def build_reviewer_revision_self_evolution_trigger(payload: dict[str, Any] | None) -> dict[str, Any]:
    study_id = _study_id(payload)
    fast_lane_requested = _task_intake_requests_manuscript_fast_lane(payload)
    suite_materialization_required = not fast_lane_requested
    return {
        "surface_kind": "mas_reviewer_revision_self_evolution_trigger",
        "schema_version": 1,
        "feedbackops_event_kind": FEEDBACKOPS_ACCEPTED_PROFILE,
        "accepted_feedback_profile": FEEDBACKOPS_ACCEPTED_PROFILE,
        "feedback_profiles": [
            FEEDBACKOPS_ACCEPTED_PROFILE,
            REVIEWER_REVISION_FEEDBACK_PROFILE,
        ],
        "target_agent_id": FEEDBACKOPS_TARGET_AGENT_ID,
        "idempotency_key": _reviewer_revision_feedbackops_idempotency_key(payload, study_id=study_id),
        "feedback_capture_requires_developer_mode": False,
        "repo_fix_execution_requires_opl_developer_mode": True,
        "developer_mode_execution_gate_refs": list(DEVELOPER_MODE_EXECUTION_GATE_REFS),
        "refs_only": True,
        "writes_study_truth": False,
        "status": "queued_for_agent_lab_external_suite",
        "trigger_kind": "reviewer_revision_quality_gap",
        "study_id": study_id,
        "adapter_role": "domain_thin_feedback_adapter",
        "paper_mission_subordination": dict(PAPER_MISSION_SUBORDINATION),
        "default_route": "paper_mission_to_submission_authority_to_agent_lab_to_oma_then_owner_gate_or_typed_blocker",
        "owner_chain": [
            "med-autoscience:reviewer_revision_intake",
            "med-autoscience:agent_lab_medical_manuscript_quality_suite",
            "one-person-lab:feedbackops_agent_lab_projection",
            "opl-meta-agent:oma-agent-evolution",
            "med-autoscience:owner_closeout_readback",
        ],
        "oma_evolution_skill_ref": "opl-meta-agent:oma-agent-evolution",
        "agent_lab_suite_materialization": {
            "required": suite_materialization_required,
            "bypass_allowed": fast_lane_requested,
            "bypass_reason": "text_only_fast_lane" if fast_lane_requested else None,
            "stable_suite_relative_path": "artifacts/agent_lab/medical_manuscript_quality/latest_suite.json",
            "materialized_by": "medautosci submit-study-task reviewer_revision hook",
            "contract_itself_triggers_execution": False,
        },
        "fast_lane_policy": {
            "text_only_fast_lane_may_bypass_agent_lab": True,
            "structural_manuscript_or_evidence_change_requires_agent_lab": True,
            "requires_mas_format_record_even_when_fast_lane": True,
        },
        "target_actions": {
            "mas_suite_builder": (
                "medautosci agent-lab-medical-manuscript-quality-suite "
                "--study-root <study_root> --reviewer-feedback-ref <feedback_ref> --apply"
            ),
            "opl_agent_lab": "opl agent-lab run --suite <suite_path> --json",
            "oma_materialization": "opl-meta-agent.improve-from-external-agent-lab-suite",
            "opl_work_order_execution": "opl-meta-agent.execute-external-work-order",
            "mas_acceptance_readback": "medautosci paper-mission inspect --study-id <study_id> --format json",
        },
        "owner_closeout_readback_refs": [
            "paper_mission_readback_ref",
            "submission_authority_owner_gate_readback_ref",
            "target_owner_receipt_or_typed_blocker_ref",
        ],
        "required_packet_refs": [
            "agent_lab_suite_result_ref",
            "structured_ai_reviewer_evaluation_ref",
            "developer_patch_work_order_ref",
            "opl_work_order_status_ref",
            "reviewer_revision_coverage_audit_ref",
            "stage_attempt_readback_ref",
            "target_owner_receipt_or_typed_blocker_ref",
        ],
        "closeout_acceptance_requirements": {
            "coverage_audit": dict(REVIEWER_REVISION_COVERAGE_AUDIT_REQUIREMENT),
            "stage_attempt_readback": dict(REVIEWER_REVISION_STAGE_ATTEMPT_READBACK_REQUIREMENT),
        },
        "status_projection": {
            "opl_app_should_show": True,
            "queued_status": "queued_for_agent_lab_external_suite",
            "running_status": "running_in_opl_agent_lab_or_work_order",
            "terminal_statuses": [
                "completed_with_owner_receipt",
                "completed_with_typed_blocker",
                "blocked_requires_human_or_owner_gate",
            ],
        },
        "authority_boundary": dict(REVIEWER_REVISION_SELF_EVOLUTION_AUTHORITY_BOUNDARY),
    }


def build_reviewer_revision_feedbackops_dispatch_request(payload: dict[str, Any] | None) -> dict[str, Any]:
    study_id = _study_id(payload)
    fast_lane_requested = _task_intake_requests_manuscript_fast_lane(payload)
    trigger = build_reviewer_revision_self_evolution_trigger(payload)
    materialization = payload.get("agent_lab_suite_materialization") if isinstance(payload, dict) else None
    suite_path = _non_empty_text(materialization.get("suite_path")) if isinstance(materialization, dict) else None
    artifact_refs = payload.get("artifact_refs") if isinstance(payload, dict) and isinstance(payload.get("artifact_refs"), dict) else {}
    feedback_ref = (
        _non_empty_text(artifact_refs.get("latest_json"))
        or _non_empty_text(payload.get("task_id")) if isinstance(payload, dict) else None
    )
    delivery_ref = suite_path or trigger["agent_lab_suite_materialization"]["stable_suite_relative_path"]
    if fast_lane_requested:
        status = "bypassed_text_only_fast_lane"
    elif suite_path is None:
        status = "pending_agent_lab_suite_materialization"
    else:
        status = "ready_for_opl_feedbackops"
    return {
        "surface_kind": "mas_reviewer_revision_feedbackops_dispatch_request",
        "schema_version": 1,
        "status": status,
        "dispatch_is_automatic_request": status == "ready_for_opl_feedbackops",
        "execution_is_owner_gated": True,
        "contract_itself_triggers_execution": False,
        "target_agent_id": trigger["target_agent_id"],
        "opl_feedbackops_target_agent_id": OPL_FEEDBACKOPS_STANDARD_AGENT_ID,
        "feedbackops_event_kind": trigger["feedbackops_event_kind"],
        "accepted_feedback_profile": trigger["accepted_feedback_profile"],
        "idempotency_key": trigger["idempotency_key"],
        "study_id": study_id,
        "delivery_ref": delivery_ref,
        "feedback_ref": feedback_ref or f"reviewer_revision:{study_id}:latest",
        "external_suite_ref": suite_path,
        "suite_path": suite_path,
        "source_trigger_ref": trigger["idempotency_key"],
        "dispatch_owner": "one-person-lab.feedbackops",
        "meta_agent_owner": "opl-meta-agent.oma-agent-evolution",
        "target_owner_closeout_owner": "med-autoscience",
        "dispatch_chain": [
            "opl feedback submit",
            "opl feedback read/reconcile",
            "opl-meta-agent improve-from-external-agent-lab-suite",
            "opl-meta-agent execute-external-work-order",
            "medautosci paper-mission inspect owner closeout readback",
        ],
        "opl_feedback_submit": {
            "command": "opl feedback submit",
            "argv": [
                "--target-agent",
                OPL_FEEDBACKOPS_STANDARD_AGENT_ID,
                "--delivery-ref",
                delivery_ref,
                "--feedback-ref",
                feedback_ref or f"reviewer_revision:{study_id}:latest",
                "--feedback-kind",
                "quality_gap",
                "--external-suite-ref",
                suite_path or trigger["agent_lab_suite_materialization"]["stable_suite_relative_path"],
                "--idempotency-key",
                trigger["idempotency_key"],
                "--source-ref",
                "medautosci submit-study-task reviewer_revision",
                "--json",
            ],
            "writes_target_domain_truth": False,
        },
        "readback_commands": [
            "opl feedback read --json",
            "opl feedback reconcile --json",
            "medautosci paper-mission inspect --study-id <study_id> --format json",
        ],
        "developer_mode_execution_gate_refs": list(DEVELOPER_MODE_EXECUTION_GATE_REFS),
        "required_packet_refs": list(trigger["required_packet_refs"]),
        "closeout_acceptance_requirements": dict(trigger["closeout_acceptance_requirements"]),
        "authority_boundary": dict(REVIEWER_REVISION_SELF_EVOLUTION_AUTHORITY_BOUNDARY),
    }


def _study_id(payload: dict[str, Any] | None) -> str:
    if isinstance(payload, dict):
        for key in ("study_id", "target_study_id", "paper_study_id"):
            text = _non_empty_text(payload.get(key))
            if text is not None:
                return text
    return "<study_id>"


def _reviewer_revision_feedbackops_idempotency_key(
    payload: dict[str, Any] | None,
    *,
    study_id: str,
) -> str:
    identity = None
    if isinstance(payload, dict):
        for key in ("task_id", "feedback_id", "request_id", "emitted_at"):
            identity = _non_empty_text(payload.get(key))
            if identity is not None:
                break
    return f"feedbackops:mas/{study_id}/reviewer_revision/{identity or 'latest'}"


def _build_manuscript_fast_lane_contract(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    from med_autoscience.study_task_intake_fast_lane import build_manuscript_fast_lane_contract

    return build_manuscript_fast_lane_contract(payload)


def _task_intake_requests_manuscript_fast_lane(payload: dict[str, Any] | None) -> bool:
    from med_autoscience.study_task_intake_fast_lane import task_intake_requests_manuscript_fast_lane

    return task_intake_requests_manuscript_fast_lane(payload)
