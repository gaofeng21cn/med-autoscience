from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import runtime_failure_taxonomy


SCHEMA_VERSION = 1
SURFACE_KIND = "auto_runtime_parked"
REOPEN_POLICY = "user_feedback_first"

PARKED_STATES = (
    "package_ready_handoff",
    "external_metadata_pending",
    "waiting_user_decision",
    "external_input_pending",
    "external_upstream_pending",
    "explicit_resume_pending",
    "platform_repair_pending",
    "preflight_contract_pending",
)

_NON_PARKED_RUNTIME_REASONS = frozenset(
    {
        "quest_marked_running_but_no_live_session",
        "quest_stopped_by_controller_guard",
        "quest_waiting_on_invalid_blocking",
        "quest_completion_requested_before_publication_gate_clear",
        "quest_drifting_into_write_without_gate_approval",
        "quest_stale_decision_after_write_stage_ready",
    }
)

_EXTERNAL_METADATA_REASONS = frozenset(
    {
        "quest_waiting_for_submission_metadata",
        "quest_waiting_for_submission_metadata_but_auto_resume_disabled",
    }
)

_EXPLICIT_RESUME_REASONS = frozenset(
    {
        "quest_stopped_requires_explicit_rerun",
        "quest_stopped_explicit_relaunch_requested",
        "quest_initialized_waiting_to_start",
        "quest_paused",
        "quest_stopped",
        "quest_marked_running_but_auto_resume_disabled",
        "quest_paused_but_auto_resume_disabled",
        "quest_stopped_but_auto_resume_disabled",
        "quest_initialized_but_auto_resume_disabled",
        "quest_exists_with_non_resumable_state",
    }
)

_PREFLIGHT_CONTRACT_REASONS = frozenset(
    {
        "workspace_contract_not_ready",
        "study_data_readiness_blocked",
        "startup_contract_resolution_failed",
        "runtime_reentry_not_ready_for_auto_start",
        "startup_boundary_not_ready_for_auto_start",
        "startup_boundary_not_ready_for_resume",
        "startup_boundary_not_ready_for_running_quest",
        "runtime_reentry_not_ready_for_resume",
        "runtime_reentry_not_ready_for_running_quest",
        "study_charter_missing",
        "study_charter_invalid",
    }
)

_PLATFORM_REPAIR_REASONS = frozenset(
    {
        "runtime_overlay_not_ready",
        "runtime_overlay_audit_failed_for_running_quest",
        "managed_skill_audit_not_available",
        "hydration_validation_failed",
        "running_quest_live_session_audit_failed",
    }
)

_STATE_LABELS = {
    "package_ready_handoff": "投稿包/人审包交付停驻",
    "external_metadata_pending": "外部投稿元数据待补",
    "waiting_user_decision": "等待用户判断",
    "external_input_pending": "等待外部输入",
    "external_upstream_pending": "等待上游服务恢复",
    "explicit_resume_pending": "等待显式恢复",
    "platform_repair_pending": "等待 MAS/MDS 平台修复",
    "preflight_contract_pending": "等待运行前置合同满足",
}

_STATE_SUMMARIES = {
    "package_ready_handoff": (
        "投稿包/人审包已到可交付节点；MAS/MDS 已释放自动运行资源，等待用户审阅、"
        "显式 resume 或新的修订输入。"
    ),
    "external_metadata_pending": (
        "外部投稿元数据待补；稿件主体和投稿包骨架已生成，当前只差作者、单位、伦理、基金、COI、通讯作者等"
        "MAS/MDS 不能自行决定的外部投稿事实。"
    ),
    "waiting_user_decision": (
        "当前需要用户做医学、策略、投稿或路线判断；MAS/MDS 不会越权继续自动运行。"
    ),
    "external_input_pending": (
        "当前缺少外部 secret、credential、受限数据路径或第三方事实输入；MAS/MDS 不能自行生成。"
    ),
    "external_upstream_pending": (
        "当前阻塞来自 Codex/API/provider/account/quota/rate-limit/5xx 等上游问题；"
        "MAS/MDS 本机不会把它当作可本地修复问题继续空转。"
    ),
    "explicit_resume_pending": "当前运行已停驻，等待用户显式 rerun、relaunch 或 resume。",
    "platform_repair_pending": "当前阻塞属于 MAS/MDS 协议、runner、tool-call 或 wire-format 平台问题，需先工程修复。",
    "preflight_contract_pending": "当前 workspace/data/startup/reentry 前置合同仍未满足，自动运行应先停驻等待合同修复。",
}

_NEXT_ACTIONS = {
    "package_ready_handoff": "等待用户审阅或显式恢复；如收到大修意见，重新进入同一论文线修订。",
    "external_metadata_pending": "等待用户补齐外部投稿元数据；补齐后再恢复投稿包同步与 QC。",
    "waiting_user_decision": "等待用户给出明确判断；收到新意见后按用户反馈优先重新进入修订线。",
    "external_input_pending": "等待外部输入可用后再恢复运行。",
    "external_upstream_pending": "等待上游服务或账户状态恢复；退避重试耗尽后保持停驻。",
    "explicit_resume_pending": "等待显式 resume、rerun 或 relaunch。",
    "platform_repair_pending": "先修复 MAS/MDS 平台问题并验证，再恢复运行。",
    "preflight_contract_pending": "先补齐运行前置合同，再由 controller 重新判断是否恢复。",
}

_OWNER_BY_STATE = {
    "package_ready_handoff": "user",
    "external_metadata_pending": "user",
    "waiting_user_decision": "user",
    "external_input_pending": "user",
    "external_upstream_pending": "external_provider",
    "explicit_resume_pending": "user",
    "platform_repair_pending": "mas_platform",
    "preflight_contract_pending": "controller",
}

_AUTO_EXECUTION_COMPLETE_STATES = frozenset(
    {
        "package_ready_handoff",
        "external_metadata_pending",
    }
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _classification_from_status(status: Mapping[str, Any]) -> Mapping[str, Any]:
    direct = _mapping(status.get("runtime_failure_classification"))
    if direct:
        return direct
    return runtime_failure_taxonomy.classify_runtime_failure_from_profile(status)


def _state_from_runtime_failure(classification: Mapping[str, Any]) -> str | None:
    action_mode = _text(classification.get("action_mode"))
    blocker_class = _text(classification.get("blocker_class"))
    if action_mode in {"external_fix_required", "provider_backoff_and_recheck"}:
        return "external_upstream_pending"
    if action_mode == "platform_repair_required" or blocker_class == "platform_protocol_or_runner_bug":
        return "platform_repair_pending"
    if action_mode == "wait_for_user_or_explicit_resume":
        return "explicit_resume_pending"
    return None


def _state_from_reason(
    *,
    reason: str | None,
    decision: str | None,
    quest_status: str | None,
    interaction_arbitration: Mapping[str, Any],
    publication_supervisor_state: Mapping[str, Any],
    needs_user_decision: bool,
    manual_finish_contract: Mapping[str, Any],
) -> str | None:
    if reason in _NON_PARKED_RUNTIME_REASONS:
        return None
    if reason in _EXTERNAL_METADATA_REASONS:
        return "external_metadata_pending"
    if reason == "quest_waiting_for_external_input":
        return "external_input_pending"
    if _text(interaction_arbitration.get("classification")) == "external_input_required":
        return "external_input_pending"
    if needs_user_decision or reason in {
        "quest_waiting_for_user",
        "study_completion_requires_program_human_confirmation",
    }:
        return "waiting_user_decision"
    if reason == "quest_parked_on_unchanged_finalize_state":
        supervisor_phase = _text(publication_supervisor_state.get("supervisor_phase"))
        current_required_action = _text(publication_supervisor_state.get("current_required_action"))
        if (
            publication_supervisor_state
            and (
                bool(publication_supervisor_state.get("bundle_tasks_downstream_only"))
                or supervisor_phase in {"publishability_gate_blocked", "bundle_stage_blocked"}
                or current_required_action == "return_to_publishability_gate"
            )
        ):
            return None
        return "package_ready_handoff"
    if reason in _EXPLICIT_RESUME_REASONS:
        supervisor_phase = _text(publication_supervisor_state.get("supervisor_phase"))
        current_required_action = _text(publication_supervisor_state.get("current_required_action"))
        if supervisor_phase == "bundle_stage_ready" and current_required_action == "continue_bundle_stage":
            return "package_ready_handoff"
    if reason in _EXPLICIT_RESUME_REASONS and decision not in {"resume", "continue", "relaunch"}:
        return "explicit_resume_pending"
    if reason in _PREFLIGHT_CONTRACT_REASONS and decision in {"blocked", "pause"}:
        return "preflight_contract_pending"
    if reason in _PLATFORM_REPAIR_REASONS and decision in {"blocked", "pause"}:
        return "platform_repair_pending"
    if (
        bool(manual_finish_contract.get("compatibility_guard_only"))
        and quest_status not in {"running", "retrying", "active"}
        and decision in {"blocked", "pause", "noop", None}
    ):
        return "package_ready_handoff"
    if reason is None and quest_status in {"stopped", "paused"} and decision in {"blocked", "noop", None}:
        return "explicit_resume_pending"
    return None


def _awaiting_explicit_wakeup(state: str, classification: Mapping[str, Any]) -> bool:
    if state == "external_upstream_pending":
        action_mode = _text(classification.get("action_mode"))
        requires_human_gate = _bool(classification.get("requires_human_gate"))
        return action_mode == "external_fix_required" or requires_human_gate is True
    return state in {
        "package_ready_handoff",
        "external_metadata_pending",
        "waiting_user_decision",
        "external_input_pending",
        "explicit_resume_pending",
    }


def _empty_projection(
    *,
    reason: str | None,
    decision: str | None,
    quest_status: str | None,
) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "parked": False,
        "parked_state": None,
        "parked_state_label": None,
        "parked_owner": None,
        "resource_release_expected": False,
        "awaiting_explicit_wakeup": False,
        "auto_execution_complete": False,
        "reopen_policy": REOPEN_POLICY,
        "legacy_current_stage": None,
        "summary": None,
        "next_action_summary": None,
        "source_reason": reason,
        "source_decision": decision,
        "source_quest_status": quest_status,
    }


def build_auto_runtime_parked_projection(
    status: Mapping[str, Any],
    *,
    needs_user_decision: bool = False,
    manual_finish_contract: Mapping[str, Any] | None = None,
    runtime_failure_classification: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    status_payload = _mapping(status)
    reason = _text(status_payload.get("reason")) or _text(status_payload.get("runtime_reason"))
    decision = _text(status_payload.get("decision")) or _text(status_payload.get("runtime_decision"))
    quest_status = _text(status_payload.get("quest_status"))
    interaction_arbitration = _mapping(status_payload.get("interaction_arbitration"))
    publication_supervisor_state = _mapping(status_payload.get("publication_supervisor_state"))
    manual_finish = _mapping(manual_finish_contract)
    classification = _mapping(runtime_failure_classification) or _classification_from_status(status_payload)

    if reason in _NON_PARKED_RUNTIME_REASONS:
        return _empty_projection(reason=reason, decision=decision, quest_status=quest_status)

    state = _state_from_runtime_failure(classification)
    if state is None:
        state = _state_from_reason(
            reason=reason,
            decision=decision,
            quest_status=quest_status,
            interaction_arbitration=interaction_arbitration,
            publication_supervisor_state=publication_supervisor_state,
            needs_user_decision=needs_user_decision,
            manual_finish_contract=manual_finish,
        )
    if state is None:
        return _empty_projection(reason=reason, decision=decision, quest_status=quest_status)

    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "parked": True,
        "parked_state": state,
        "parked_state_label": _STATE_LABELS[state],
        "parked_owner": _OWNER_BY_STATE[state],
        "resource_release_expected": True,
        "awaiting_explicit_wakeup": _awaiting_explicit_wakeup(state, classification),
        "auto_execution_complete": state in _AUTO_EXECUTION_COMPLETE_STATES,
        "reopen_policy": REOPEN_POLICY,
        "legacy_current_stage": "manual_finishing" if state in _AUTO_EXECUTION_COMPLETE_STATES else None,
        "summary": _STATE_SUMMARIES[state],
        "next_action_summary": _NEXT_ACTIONS[state],
        "source_reason": reason,
        "source_decision": decision,
        "source_quest_status": quest_status,
        "runtime_failure_classification": dict(classification) or None,
    }


def is_auto_runtime_parked(projection: Mapping[str, Any] | None) -> bool:
    return bool(_mapping(projection).get("parked"))
