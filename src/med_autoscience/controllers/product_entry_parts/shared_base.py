from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import (
    ai_first_cross_study_completion,
    domain_slo_scheduler_projection,
    study_runtime_router,
)
from med_autoscience.action_catalog import (
    action_catalog_command_map as _action_catalog_command_map,
    build_mas_action_catalog as _build_mas_action_catalog,
    product_entry_shell_from_action_catalog as _product_entry_shell_from_action_catalog,
    project_mas_action_catalog as _project_mas_action_catalog,
)
from med_autoscience.controllers.study_runtime_resolution import _execution_payload, _resolve_study
from med_autoscience.domain_entry_contract import (
    PRODUCT_ENTRY_MANIFEST_SCHEMA_REF,
    PRODUCT_ENTRY_STATUS_SCHEMA_REF,
    SERVICE_SAFE_ENTRY_ADAPTER,
    build_domain_entry_contract as _build_domain_entry_contract,
    build_shared_handoff as _build_shared_handoff,
    build_user_interaction_contract as _build_user_interaction_contract,
    validate_user_interaction_contract as _validate_shared_user_interaction_contract,
)
from med_autoscience.doctor import build_doctor_report
from med_autoscience.policies.automation_ready import render_automation_ready_summary
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile
from med_autoscience.runtime_protocol.lifecycle_refs_adapter import (
    build_domain_memory_descriptor,
    build_family_stage_control_plane,
    build_product_entry_adoption_projection,
)
from med_autoscience.study_task_intake import (
    read_latest_task_intake,
    render_task_intake_markdown,
    upsert_startup_brief_task_block,
    write_task_intake,
)
from opl_harness_shared.automation_companions import (
    build_automation_catalog as _build_shared_automation_catalog,
    build_automation_descriptor as _build_shared_automation_descriptor,
)
from opl_harness_shared.managed_runtime import (
    ManagedRuntimeThreeLayerContract as _SharedManagedRuntimeThreeLayerContract,
    read_bundled_managed_runtime_three_layer_contract as _read_shared_managed_runtime_contract,
    build_managed_runtime_contract as _build_shared_managed_runtime_contract,
)
from opl_harness_shared.family_orchestration import (
    build_family_product_entry_orchestration as _build_shared_family_product_entry_orchestration,
)
from opl_harness_shared.family_entry_contracts import (
    validate_family_domain_entry_contract as _validate_shared_family_domain_entry_contract,
)
from opl_harness_shared.product_entry_companions import (
    build_family_product_entry_manifest as _build_shared_family_product_entry_manifest,
    build_operator_loop_action_catalog as _build_shared_operator_loop_action_catalog,
    build_product_entry_start as _build_shared_product_entry_start,
    build_product_entry_overview as _build_shared_product_entry_overview,
    build_product_entry_quickstart as _build_shared_product_entry_quickstart,
    build_product_entry_readiness as _build_shared_product_entry_readiness,
    build_product_entry_resume_surface as _build_shared_product_entry_resume_surface,
    build_product_entry_shell_catalog as _build_shared_product_entry_shell_catalog,
    build_product_entry_shell_linked_surface as _build_shared_product_entry_shell_linked_surface,
    collect_family_human_gate_ids as _collect_family_human_gate_ids,
)
from opl_harness_shared.product_entry_program_companions import (
    build_clearance_lane as _build_shared_clearance_lane,
    build_clearance_target as _build_shared_clearance_target,
    build_guardrail_class as _build_shared_guardrail_class,
    build_platform_target as _build_shared_platform_target,
    build_product_entry_guardrails as _build_shared_product_entry_guardrails,
    build_product_entry_preflight as _build_shared_product_entry_preflight,
    build_product_entry_program_step as _build_shared_product_entry_program_step,
    build_product_entry_program_surface as _build_shared_product_entry_program_surface,
    build_program_capability as _build_shared_program_capability,
    build_program_check as _build_shared_program_check,
    build_program_sequence_step as _build_shared_program_sequence_step,
    build_source_provenance_surface as _build_shared_source_provenance_surface,
)
from opl_harness_shared.runtime_task_companions import (
    build_artifact_inventory as _build_shared_artifact_inventory,
    build_checkpoint_summary as _build_shared_checkpoint_summary,
    build_progress_projection as _build_shared_progress_projection,
    build_runtime_inventory as _build_shared_runtime_inventory,
    build_session_continuity as _build_shared_session_continuity,
    build_task_lifecycle as _build_shared_task_lifecycle,
)
from opl_harness_shared.skill_catalog import (
    build_skill_catalog as _build_shared_skill_catalog,
    build_skill_descriptor as _build_shared_skill_descriptor,
)

from .boundary_surfaces import (
    _capability_owner_boundary_payload,
    _normalized_strings,
    _render_capability_owner_boundary_markdown_lines,
    _render_single_project_boundary_markdown_lines,
    _require_mapping,
    _require_nonempty_string_from_mapping,
    _single_project_boundary_payload,
    _validate_capability_owner_boundary,
    _validate_single_project_boundary,
)
from .command_surfaces import (
    _command_prefix,
    _json_surface_command,
    _profile_arg,
    _profile_command_prefix,
    _quote_cli_arg,
    _require_direct_entry_mode as _require_direct_entry_mode_for_supported_modes,
    _study_selector,
)
from .human_status_view import (
    _append_human_status_lines,
    _operator_handling_state_label,
    _recovery_action_mode_label,
    _status_narration_human_view,
)
from .shared_labels import (
    _bool_label,
    _check_status_label,
    _direct_entry_mode_label,
    _non_empty_text,
    _operator_verdict_label,
    _phase5_monorepo_status_label,
    _phase5_sequence_scope_label,
    _runtime_decision_label,
    _start_mode_label,
    _surface_kind_label,
    _user_interaction_mode_label,
    _workspace_status_label,
)


def _controller_override(name: str, default: Any) -> Any:
    controller_module = sys.modules.get("med_autoscience.controllers.product_entry")
    if controller_module is None:
        return default
    return getattr(controller_module, name, default)


SCHEMA_VERSION = 1
PRODUCT_ENTRY_KIND = "med_autoscience_product_entry"
PRODUCT_ENTRY_MANIFEST_KIND = "med_autoscience_product_entry_manifest"
PRODUCT_ENTRY_STATUS_KIND = "product_entry_status"
TARGET_DOMAIN_ID = "med-autoscience"
CONTROLLED_BACKEND_EXECUTOR_OWNER = runtime_backend_contract.CONTROLLED_RESEARCH_BACKEND_EXECUTOR_OWNER
MAS_RUNTIME_OWNER = runtime_backend_contract.MAS_RUNTIME_OWNER
MAS_RUNTIME_SUBSTRATE = runtime_backend_contract.MAS_RUNTIME_SUBSTRATE
SUPPORTED_DIRECT_ENTRY_MODES = ("direct", "opl-handoff")
_LIVE_TASK_INTAKE_RUNTIME_STATUSES = frozenset({"running", "active", "waiting_for_user"})
_ATTENTION_PRIORITIES = {
    "workspace_supervisor_service_not_loaded": 0,
    "study_runtime_recovery_required": 1,
    "study_runtime_reconcile_requestable": 1,
    "study_waiting_user_decision": 2,
    "study_supervision_gap": 3,
    "study_quality_floor_blocker": 4,
    "study_progress_stale": 5,
    "study_progress_missing": 6,
    "study_auto_runtime_parked": 7, "study_manual_finishing": 7,
    "study_blocked": 7,
}


def _validate_domain_entry_contract_shape(contract: Mapping[str, Any], *, context: str) -> None:
    _validate_shared_family_domain_entry_contract(contract, context)


def _validate_user_interaction_contract_shape(contract: Mapping[str, Any], *, context: str) -> None:
    _validate_shared_user_interaction_contract(dict(contract), context)


def _validate_surface_kind_mapping(
    payload: Mapping[str, Any],
    *,
    field: str,
    expected_surface_kind: str,
    context: str,
) -> None:
    surface = _require_mapping(payload, field, context=context)
    surface_kind = _require_nonempty_string_from_mapping(surface, "surface_kind", context=f"{context}.{field}")
    if surface_kind != expected_surface_kind:
        raise ValueError(
            f"{context}.{field}.surface_kind 必须是 {expected_surface_kind}，当前为 {surface_kind}。"
        )


def _validate_product_entry_manifest_contract(payload: Mapping[str, Any]) -> None:
    _validate_surface_kind_mapping(
        payload,
        field="product_entry_surface",
        expected_surface_kind=PRODUCT_ENTRY_STATUS_KIND,
        context="product_entry_manifest",
    )
    _validate_surface_kind_mapping(
        payload,
        field="operator_loop_surface",
        expected_surface_kind="workspace_cockpit",
        context="product_entry_manifest",
    )
    _validate_domain_entry_contract_shape(
        _require_mapping(payload, "domain_entry_contract", context="product_entry_manifest"),
        context="product_entry_manifest.domain_entry_contract",
    )
    _validate_user_interaction_contract_shape(
        _require_mapping(payload, "user_interaction_contract", context="product_entry_manifest"),
        context="product_entry_manifest.user_interaction_contract",
    )
    _validate_single_project_boundary(
        payload.get("single_project_boundary"),
        context="product_entry_manifest.single_project_boundary",
    )
    _validate_capability_owner_boundary(
        payload.get("capability_owner_boundary"),
        context="product_entry_manifest.capability_owner_boundary",
    )


def _validate_product_entry_status_contract(payload: Mapping[str, Any]) -> None:
    surface_kind = _require_nonempty_string_from_mapping(payload, "surface_kind", context="product_entry_status")
    if surface_kind != PRODUCT_ENTRY_STATUS_KIND:
        raise ValueError(f"product_entry_status.surface_kind 必须是 {PRODUCT_ENTRY_STATUS_KIND}。")
    _validate_surface_kind_mapping(
        payload,
        field="product_entry_surface",
        expected_surface_kind=PRODUCT_ENTRY_STATUS_KIND,
        context="product_entry_status",
    )
    _validate_surface_kind_mapping(
        payload,
        field="operator_loop_surface",
        expected_surface_kind="workspace_cockpit",
        context="product_entry_status",
    )
    _validate_domain_entry_contract_shape(
        _require_mapping(payload, "domain_entry_contract", context="product_entry_status"),
        context="product_entry_status.domain_entry_contract",
    )
    _validate_user_interaction_contract_shape(
        _require_mapping(payload, "user_interaction_contract", context="product_entry_status"),
        context="product_entry_status.user_interaction_contract",
    )
    _validate_single_project_boundary(
        payload.get("single_project_boundary"),
        context="product_entry_status.single_project_boundary",
    )
    _validate_capability_owner_boundary(
        payload.get("capability_owner_boundary"),
        context="product_entry_status.capability_owner_boundary",
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _quality_review_loop_preview(loop_payload: Mapping[str, Any] | None) -> str | None:
    if not isinstance(loop_payload, Mapping):
        return None
    current_phase_label = _non_empty_text(loop_payload.get("current_phase_label"))
    next_phase_label = _non_empty_text(loop_payload.get("recommended_next_phase_label"))
    summary = _non_empty_text(loop_payload.get("summary"))
    parts = [part for part in (current_phase_label, next_phase_label, summary) if part]
    if not parts:
        return None
    if current_phase_label and next_phase_label and summary:
        return f"{current_phase_label} -> {next_phase_label}；{summary}"
    return "；".join(parts)


def _quality_review_followthrough_preview(payload: Mapping[str, Any] | None) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    state_label = _non_empty_text(payload.get("state_label"))
    summary = _non_empty_text(payload.get("summary"))
    next_confirmation_signal = _non_empty_text(payload.get("next_confirmation_signal"))
    parts = [part for part in (state_label, summary, next_confirmation_signal) if part]
    if not parts:
        return None
    return "；".join(parts)


def _quality_repair_followthrough_preview(payload: Mapping[str, Any] | None) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    state_label = _non_empty_text(payload.get("state_label"))
    summary = _non_empty_text(payload.get("summary"))
    next_confirmation_signal = _non_empty_text(payload.get("next_confirmation_signal"))
    parts = [part for part in (state_label, summary, next_confirmation_signal) if part]
    if not parts:
        return None
    return "；".join(parts)


def _same_line_route_truth_preview(payload: Mapping[str, Any] | None) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    return _non_empty_text(payload.get("summary")) or _non_empty_text(payload.get("current_focus"))


def _gate_clearing_followthrough_summary(payload: Mapping[str, Any] | None) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    return (
        _non_empty_text(payload.get("summary"))
        or _non_empty_text(payload.get("blocking_reason"))
        or _non_empty_text(payload.get("action_summary"))
        or _non_empty_text(payload.get("current_focus"))
        or _non_empty_text(payload.get("latest_unit_summary"))
        or _non_empty_text(payload.get("gate_replay_summary"))
    )


def _gate_clearing_followthrough_preview(payload: Mapping[str, Any] | None) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    state_label = _non_empty_text(payload.get("state_label"))
    summary = _gate_clearing_followthrough_summary(payload)
    action_summary = _non_empty_text(payload.get("action_summary"))
    if action_summary == summary:
        action_summary = None
    next_confirmation_signal = _non_empty_text(payload.get("next_confirmation_signal"))
    parts = [part for part in (state_label, summary, action_summary, next_confirmation_signal) if part]
    if not parts:
        return None
    return "；".join(parts)


def _normalized_gate_clearing_followthrough(
    item: Mapping[str, Any] | None,
    *,
    fallback_command: str | None = None,
) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        return {}
    direct_followthrough = dict(item.get("gate_clearing_followthrough") or {})
    if direct_followthrough:
        return direct_followthrough
    batch_followthrough = dict(item.get("gate_clearing_batch_followthrough") or {})
    if not batch_followthrough:
        return {}
    gate_replay_status = _non_empty_text(batch_followthrough.get("gate_replay_status")) or "unknown"
    failed_unit_count = batch_followthrough.get("failed_unit_count")
    failed_unit_count = failed_unit_count if isinstance(failed_unit_count, int) else 0
    blocking_issue_count = batch_followthrough.get("blocking_issue_count")
    blocking_issue_count = blocking_issue_count if isinstance(blocking_issue_count, int) else 0
    if failed_unit_count > 0:
        state = "repair_units_failed"
        state_label = "repair unit 失败"
    elif gate_replay_status == "clear":
        state = "gate_replay_clear"
        state_label = "gate replay 已放行"
    else:
        state = "waiting_gate_replay"
        state_label = "等待 gate replay"
    return {
        "surface_kind": "gate_clearing_followthrough",
        "state": state,
        "state_label": state_label,
        "summary": _non_empty_text(batch_followthrough.get("summary")),
        "next_confirmation_signal": _non_empty_text(batch_followthrough.get("next_confirmation_signal")),
        "recommended_step_id": "inspect_gate_clearing_followthrough",
        "recommended_command": _non_empty_text(batch_followthrough.get("recommended_command")) or fallback_command,
        "gate_replay_status": gate_replay_status,
        "failed_unit_count": failed_unit_count,
        "blocking_issue_count": blocking_issue_count,
        "latest_record_path": _non_empty_text(batch_followthrough.get("latest_record_path")),
        "user_intervention_required_now": bool(batch_followthrough.get("user_intervention_required_now")),
    }


def _build_managed_runtime_contract(
    *,
    domain_owner: str,
    executor_owner: str,
    supervision_status_surface: str,
    attention_queue_surface: str,
    recovery_contract_surface: str,
) -> dict[str, Any]:
    shared_contract = _read_shared_managed_runtime_contract()
    return _build_shared_managed_runtime_contract(
        runtime_owner=MAS_RUNTIME_OWNER,
        domain_owner=domain_owner,
        executor_owner=executor_owner,
        supervision_status_surface=supervision_status_surface,
        attention_queue_surface=attention_queue_surface,
        recovery_contract_surface=recovery_contract_surface,
        contract=_SharedManagedRuntimeThreeLayerContract(
            contract_ref="contracts/opl-framework/managed-runtime-three-layer-contract.json",
            contract_id=shared_contract.contract_id,
            required_owner_fields=shared_contract.required_owner_fields,
            required_surface_locator_fields=shared_contract.required_surface_locator_fields,
            canonical_fail_closed_rules=shared_contract.canonical_fail_closed_rules,
        ),
    )


def _serialize_runtime_status(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return dict(result)
    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if not isinstance(payload, dict):
            raise TypeError("product entry runtime status to_dict() must return a mapping")
        return dict(payload)
    raise TypeError("product entry runtime status must be a mapping-like payload")


def _require_direct_entry_mode(value: str | None) -> str:
    return _require_direct_entry_mode_for_supported_modes(value, supported_modes=SUPPORTED_DIRECT_ENTRY_MODES)


def _inspect_workspace_supervision(profile: WorkspaceProfile) -> dict[str, Any]:
    return domain_slo_scheduler_projection.read_supervision_status(profile=profile)


def _doctor_workspace_domain_route_contract(doctor_report: Any) -> dict[str, Any]:
    contract = getattr(doctor_report, "workspace_domain_route_contract", None)
    if isinstance(contract, Mapping):
        return dict(contract)
    return {}


def _doctor_mas_runtime_core_ready(doctor_report: Any) -> bool:
    contract = getattr(doctor_report, "runtime_contract", None)
    if isinstance(contract, Mapping):
        return bool(contract.get("ready"))
    return bool(getattr(doctor_report, "runtime_exists", False))


def _workspace_ready_alerts(doctor_report) -> list[str]:
    alerts: list[str] = []
    if not doctor_report.workspace_exists:
        alerts.append("workspace 根目录不存在，MAS 还不能进入正式产品态。")
    if not doctor_report.runtime_exists:
        alerts.append("runtime root 不存在，MAS 还不能接管托管运行。")
    if not doctor_report.studies_exists:
        alerts.append("studies 根目录不存在，当前没有 study authority surface。")
    if not doctor_report.portfolio_exists:
        alerts.append("portfolio 根目录不存在，workspace 数据资产面还未完整。")
    runtime_contract_ready = _doctor_mas_runtime_core_ready(doctor_report)
    if not runtime_contract_ready:
        alerts.append("MAS runtime contract 尚未 ready，当前无法继续托管研究执行。")
    if not doctor_report.medical_overlay_ready:
        alerts.append("workspace medical overlay 还未 ready，当前运行前置能力不完整。")
    workspace_domain_route_contract = _doctor_workspace_domain_route_contract(doctor_report)
    workspace_supervision_ready = bool(workspace_domain_route_contract.get("loaded"))
    workspace_supervision_summary = _non_empty_text(workspace_domain_route_contract.get("summary"))
    if not workspace_supervision_ready:
        alerts.append(
            workspace_supervision_summary
            or "OPL scheduler replacement projection 尚未 ready。"
        )
    return alerts


def _build_product_entry_preflight(
    *,
    doctor_report: Any,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    doctor_command = f"{_command_prefix(profile_ref)} doctor --profile {_profile_arg(profile_ref)}"
    start_command = f"{_command_prefix(profile_ref)} product-entry-status --profile {_profile_arg(profile_ref)}"
    workspace_domain_route_contract = _doctor_workspace_domain_route_contract(doctor_report)
    runtime_contract_ready = _doctor_mas_runtime_core_ready(doctor_report)
    checks = [
        _build_shared_program_check(
            check_id="workspace_root_exists",
            title="Workspace Root Exists",
            status="pass" if doctor_report.workspace_exists else "fail",
            blocking=True,
            summary="workspace 根目录已就位。" if doctor_report.workspace_exists else "workspace 根目录不存在。",
            command=doctor_command,
        ),
        _build_shared_program_check(
            check_id="runtime_root_exists",
            title="Runtime Root Exists",
            status="pass" if doctor_report.runtime_exists else "fail",
            blocking=True,
            summary="runtime root 已就位。" if doctor_report.runtime_exists else "runtime root 不存在。",
            command=doctor_command,
        ),
        _build_shared_program_check(
            check_id="studies_root_exists",
            title="Studies Root Exists",
            status="pass" if doctor_report.studies_exists else "fail",
            blocking=True,
            summary="studies 根目录已就位。" if doctor_report.studies_exists else "studies 根目录不存在。",
            command=doctor_command,
        ),
        _build_shared_program_check(
            check_id="portfolio_root_exists",
            title="Portfolio Root Exists",
            status="pass" if doctor_report.portfolio_exists else "fail",
            blocking=True,
            summary="portfolio 根目录已就位。" if doctor_report.portfolio_exists else "portfolio 根目录不存在。",
            command=doctor_command,
        ),
        _build_shared_program_check(
            check_id="mas_runtime_core_ready",
            title="MAS Runtime Core Ready",
            status="pass" if runtime_contract_ready else "fail",
            blocking=True,
            summary=(
                "MAS runtime core contract 已就位。"
                if runtime_contract_ready
                else "MAS runtime core contract 尚未 ready。"
            ),
            command=doctor_command,
        ),
        _build_shared_program_check(
            check_id="medical_overlay_ready",
            title="Medical Overlay Ready",
            status="pass" if doctor_report.medical_overlay_ready else "fail",
            blocking=True,
            summary="medical overlay 已 ready。" if doctor_report.medical_overlay_ready else "medical overlay 尚未 ready。",
            command=doctor_command,
        ),
        _build_shared_program_check(
            check_id="workspace_domain_route_contract_ready",
            title="Workspace Supervision Contract Ready",
            status="pass" if bool(workspace_domain_route_contract.get("loaded")) else "fail",
            blocking=True,
            summary=(
                "OPL scheduler replacement projection 已 ready。"
                if bool(workspace_domain_route_contract.get("loaded"))
                else _non_empty_text(workspace_domain_route_contract.get("summary"))
                or "OPL scheduler replacement projection 尚未 ready。"
            ),
            command=f"{_command_prefix(profile_ref)} runtime-ensure-supervision --profile {_profile_arg(profile_ref)}",
        ),
    ]
    blocking_check_ids = [
        check["check_id"]
        for check in checks
        if check["blocking"] and check["status"] != "pass"
    ]
    ready_to_try_now = not blocking_check_ids
    first_blocking_summary = next(
        (check["summary"] for check in checks if check["check_id"] in blocking_check_ids and _non_empty_text(check.get("summary"))),
        None,
    )
    summary = (
        "当前 product-entry 前置检查已通过，可以先复核 doctor 输出，再进入 research entry_status。"
        if ready_to_try_now
        else first_blocking_summary
        or "当前仍有 blocking preflight check；请先修复 workspace/runtime/overlay/backend/runtime/supervision contract 再进入 research entry_status。"
    )
    build_preflight = _controller_override("_build_shared_product_entry_preflight", _build_shared_product_entry_preflight)
    return build_preflight(
        summary=summary,
        recommended_check_command=doctor_command,
        recommended_start_command=start_command,
        checks=checks,
    )


def _build_product_entry_guardrails(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
) -> dict[str, Any]:
    prefix = _command_prefix(profile_ref)
    profile_arg = _profile_arg(profile_ref)
    progress_command = f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>"
    refresh_command = (
        f"{prefix} runtime domain-health-diagnostic --runtime-root {_quote_cli_arg(profile.runtime_root)} "
        f"--profile {profile_arg} --ensure-study-runtimes --apply-supervisor-platform-repair --apply"
    )
    build_guardrails = _controller_override("_build_shared_product_entry_guardrails", _build_shared_product_entry_guardrails)
    return build_guardrails(
        summary=(
            "把卡住、没进度、监管掉线、需要人工决策和质量阻塞显式投影成可执行恢复回路，"
            "避免研究主线失去监管。"
        ),
        guardrail_classes=[
            _build_shared_guardrail_class(
                guardrail_id="workspace_supervision_gap",
                trigger="workspace-cockpit attention queue / study-progress supervisor freshness",
                symptom="OPL scheduler replacement projection 未在线，或 MAS domain runtime freshness stale/missing。",
                recommended_command=refresh_command,
            ),
            _build_shared_guardrail_class(
                guardrail_id="study_progress_gap",
                trigger="study-progress progress_freshness / workspace-cockpit attention queue",
                symptom="当前 study 进度 stale 或 missing，疑似卡住、空转或没有新的明确推进证据。",
                recommended_command=progress_command,
            ),
            _build_shared_guardrail_class(
                guardrail_id="user_decision_gate",
                trigger="study-progress needs_user_decision / controller decision gate",
                symptom="当前已前移到用户或 publication release 的人工判断节点。",
                recommended_command=progress_command,
            ),
            _build_shared_guardrail_class(
                guardrail_id="runtime_recovery_required",
                trigger="study-progress intervention_lane / runtime_supervision health_status / workspace-cockpit attention queue",
                symptom="托管运行恢复失败、健康降级或长期停在恢复态，当前必须优先处理 runtime recovery。",
                recommended_command=f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>",
            ),
            _build_shared_guardrail_class(
                guardrail_id="quality_floor_blocker",
                trigger="study-progress intervention_lane / domain health diagnostic figure-loop alerts / publication gate",
                symptom="研究输出质量、figure/reference floor 或 publication gate 出现硬阻塞，不能继续盲目长跑。",
                recommended_command=progress_command,
            ),
        ],
        recovery_loop=[
            _build_shared_product_entry_program_step(
                step_id="inspect_workspace_inbox",
                command=f"{prefix} workspace-cockpit --profile {profile_arg}",
                surface_kind="workspace_cockpit",
            ),
            _build_shared_product_entry_program_step(
                step_id="refresh_supervision",
                command=refresh_command,
                surface_kind="domain_health_diagnostic_refresh",
            ),
            _build_shared_product_entry_program_step(
                step_id="inspect_study_progress",
                command=progress_command,
                surface_kind="study_progress",
            ),
            _build_shared_product_entry_program_step(
                step_id="continue_or_relaunch",
                command=f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>",
                surface_kind="launch_study",
            ),
        ],
    )
