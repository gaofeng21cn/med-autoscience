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
    ("discussion_claim_guardrails", "discussion/claim guardrails", "讨论、结论和 claim 边界没有越过当前证据包。"),
    ("handoff_evidence_surface", "handoff/evidence surface", "durable handoff 写明数据源、脚本入口、输出表图、改动范围、claim guardrails 与 canonical source 回灌状态。"),
)
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
DEVELOPER_MODE_EXECUTION_GATE_REFS = [
    "opl-developer-mode:repo-fix-execution",
    "workspace-profile-ref:developer_supervisor_mode",
    "workspace-profile-ref:github_username",
    "workspace-profile-ref:mas_developer_github_usernames",
]


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
    revision_payload = {
        "kind": "reviewer_revision",
        "status": "active",
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
        "self_evolution_trigger": build_reviewer_revision_self_evolution_trigger(payload),
    }
    fast_lane = _build_manuscript_fast_lane_contract(payload)
    if fast_lane is not None:
        revision_payload["manuscript_fast_lane"] = fast_lane
    return revision_payload


def build_reviewer_revision_self_evolution_trigger(payload: dict[str, Any] | None) -> dict[str, Any]:
    study_id = _study_id(payload)
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
        "default_route": "mas_to_opl_agent_lab_to_oma_work_order",
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
            "mas_acceptance_readback": "medautosci study progress --study-id <study_id> --format json",
        },
        "required_packet_refs": [
            "agent_lab_suite_result_ref",
            "structured_ai_reviewer_evaluation_ref",
            "developer_patch_work_order_ref",
            "opl_work_order_status_ref",
            "target_owner_receipt_or_typed_blocker_ref",
        ],
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
