from __future__ import annotations

import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from med_autoscience.controllers import hermes_supervision, mainline_status, study_progress, study_runtime_router
from med_autoscience.controllers.study_runtime_resolution import _execution_payload, _resolve_study
from med_autoscience.domain_entry_contract import (
    PRODUCT_ENTRY_MANIFEST_SCHEMA_REF,
    PRODUCT_FRONTDESK_SCHEMA_REF,
    SERVICE_SAFE_ENTRY_ADAPTER,
    build_domain_entry_contract as _build_domain_entry_contract,
    build_gateway_interaction_contract as _build_gateway_interaction_contract,
    build_shared_handoff as _build_shared_handoff,
)
from med_autoscience.doctor import build_doctor_report
from med_autoscience.policies.automation_ready import render_automation_ready_summary
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.runtime_protocol import quest_state, user_message
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile
from med_autoscience.study_task_intake import (
    read_latest_task_intake,
    render_task_intake_markdown,
    render_task_intake_runtime_context,
    upsert_startup_brief_task_block,
    write_task_intake,
)
from opl_harness_shared.automation_companions import (
    build_automation_catalog as _build_shared_automation_catalog,
    build_automation_descriptor as _build_shared_automation_descriptor,
)
from opl_harness_shared.managed_runtime import build_managed_runtime_contract as _build_shared_managed_runtime_contract
from opl_harness_shared.family_orchestration import (
    build_family_product_entry_orchestration as _build_shared_family_product_entry_orchestration,
)
from opl_harness_shared.family_entry_contracts import (
    validate_family_domain_entry_contract as _validate_shared_family_domain_entry_contract,
    validate_gateway_interaction_contract as _validate_shared_gateway_interaction_contract,
)
from opl_harness_shared.product_entry_companions import (
    build_family_product_frontdesk_from_manifest as _build_shared_family_product_frontdesk_from_manifest,
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
    validate_family_product_frontdesk as _validate_shared_family_product_frontdesk,
    validate_family_product_entry_manifest as _validate_shared_family_product_entry_manifest,
)
from opl_harness_shared.product_entry_program_companions import (
    build_backend_deconstruction_lane as _build_shared_backend_deconstruction_lane,
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
)
from opl_harness_shared.runtime_task_companions import (
    build_checkpoint_summary as _build_shared_checkpoint_summary,
    build_runtime_inventory as _build_shared_runtime_inventory,
    build_task_lifecycle as _build_shared_task_lifecycle,
)
from opl_harness_shared.status_narration import (
    build_status_narration_human_view as _build_shared_status_narration_human_view,
)
from opl_harness_shared.skill_catalog import (
    build_skill_catalog as _build_shared_skill_catalog,
    build_skill_descriptor as _build_shared_skill_descriptor,
)


SCHEMA_VERSION = 1
PRODUCT_ENTRY_KIND = "med_autoscience_product_entry"
PRODUCT_ENTRY_MANIFEST_KIND = "med_autoscience_product_entry_manifest"
PRODUCT_FRONTDESK_KIND = "product_frontdesk"
TARGET_DOMAIN_ID = "med-autoscience"
SUPPORTED_DIRECT_ENTRY_MODES = ("direct", "opl-handoff")
_LIVE_TASK_INTAKE_RUNTIME_STATUSES = frozenset({"running", "active", "waiting_for_user"})
_ATTENTION_PRIORITIES = {
    "workspace_supervisor_service_not_loaded": 0,
    "study_runtime_recovery_required": 1,
    "study_needs_physician_decision": 2,
    "study_supervision_gap": 3,
    "study_quality_floor_blocker": 4,
    "study_progress_stale": 5,
    "study_progress_missing": 6,
    "study_blocked": 7,
}


def _require_mapping(payload: Mapping[str, Any], field: str, *, context: str) -> Mapping[str, Any]:
    value = payload.get(field)
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} 缺少合法 mapping 字段: {field}")
    return value


def _require_nonempty_string_from_mapping(payload: Mapping[str, Any], field: str, *, context: str) -> str:
    value = payload.get(field)
    text = _non_empty_text(value)
    if text is None:
        raise ValueError(f"{context} 缺少合法字符串字段: {field}")
    return text


def _validate_domain_entry_contract_shape(contract: Mapping[str, Any], *, context: str) -> None:
    _validate_shared_family_domain_entry_contract(contract, context)


def _validate_gateway_interaction_contract_shape(contract: Mapping[str, Any], *, context: str) -> None:
    _validate_shared_gateway_interaction_contract(contract, context)


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
    _validate_shared_family_product_entry_manifest(
        payload,
        require_contract_bundle=True,
        require_runtime_companions=True,
    )
    _validate_single_project_boundary(
        payload.get("single_project_boundary"),
        context="product_entry_manifest.single_project_boundary",
    )


def _validate_product_frontdesk_contract(payload: Mapping[str, Any]) -> None:
    _validate_shared_family_product_frontdesk(
        payload,
        require_contract_bundle=True,
    )
    _validate_single_project_boundary(
        payload.get("single_project_boundary"),
        context="product_frontdesk.single_project_boundary",
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _single_project_boundary_payload(source: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = dict(source or {})
    if not payload:
        payload = dict(mainline_status._single_project_boundary())
    return payload


def _validate_single_project_boundary(value: object, *, context: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} 缺少合法 mapping 字段: single_project_boundary")
    payload = dict(value)
    surface_kind = _require_nonempty_string_from_mapping(payload, "surface_kind", context=context)
    if surface_kind != "single_project_boundary":
        raise ValueError(f"{context}.surface_kind 必须是 single_project_boundary，当前为 {surface_kind}。")
    summary = _require_nonempty_string_from_mapping(payload, "summary", context=context)
    mas_owner_modules = _normalized_strings(payload.get("mas_owner_modules") or [])
    if not mas_owner_modules:
        raise ValueError(f"{context}.mas_owner_modules 不能为空。")
    raw_roles = payload.get("mds_retained_roles") or []
    if not isinstance(raw_roles, list) or not raw_roles:
        raise ValueError(f"{context}.mds_retained_roles 不能为空。")
    normalized_roles: list[dict[str, str]] = []
    for index, item in enumerate(raw_roles):
        if not isinstance(item, Mapping):
            raise ValueError(f"{context}.mds_retained_roles[{index}] 必须是 mapping。")
        role = dict(item)
        normalized_roles.append(
            {
                "role_id": _require_nonempty_string_from_mapping(
                    role,
                    "role_id",
                    context=f"{context}.mds_retained_roles[{index}]",
                ),
                "title": _require_nonempty_string_from_mapping(
                    role,
                    "title",
                    context=f"{context}.mds_retained_roles[{index}]",
                ),
                "summary": _require_nonempty_string_from_mapping(
                    role,
                    "summary",
                    context=f"{context}.mds_retained_roles[{index}]",
                ),
            }
        )
    land_now = _normalized_strings(payload.get("land_now") or [])
    post_gate_only = _normalized_strings(payload.get("post_gate_only") or [])
    not_now = _normalized_strings(payload.get("not_now") or [])
    if not post_gate_only:
        raise ValueError(f"{context}.post_gate_only 不能为空。")
    if not not_now:
        raise ValueError(f"{context}.not_now 不能为空。")
    return {
        "surface_kind": surface_kind,
        "summary": summary,
        "mas_owner_modules": mas_owner_modules,
        "mds_retained_roles": normalized_roles,
        "land_now": land_now,
        "post_gate_only": post_gate_only,
        "not_now": not_now,
    }


def _render_single_project_boundary_markdown_lines(single_project_boundary: Mapping[str, Any]) -> list[str]:
    lines = [
        "## Single-Project Boundary",
        "",
        f"- 当前摘要: {single_project_boundary.get('summary') or 'none'}",
        f"- MAS owner modules: `{', '.join(single_project_boundary.get('mas_owner_modules') or []) or 'none'}`",
    ]
    for item in single_project_boundary.get("land_now") or []:
        lines.append(f"- 当前 tranche 收口: {item}")
    for item in single_project_boundary.get("mds_retained_roles") or []:
        if not isinstance(item, Mapping):
            continue
        lines.append(f"- MDS 保留 `{item.get('role_id')}`: {item.get('summary') or 'none'}")
    for item in single_project_boundary.get("post_gate_only") or []:
        lines.append(f"- post-gate only: {item}")
    for item in single_project_boundary.get("not_now") or []:
        lines.append(f"- 当前不允许: {item}")
    return lines


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


def _status_narration_human_view(payload: Mapping[str, Any]) -> dict[str, Any]:
    return _build_shared_status_narration_human_view(
        payload,
        fallback_current_stage=_non_empty_text(payload.get("current_stage"))
        or _non_empty_text(payload.get("current_stage_id")),
        fallback_latest_update=_non_empty_text(payload.get("current_stage_summary"))
        or _non_empty_text(payload.get("summary")),
        fallback_next_step=_non_empty_text(payload.get("next_system_action")),
        fallback_blockers=payload.get("current_blockers") or [],
    )


def _append_human_status_lines(lines: list[str], payload: Mapping[str, Any]) -> None:
    human_view = _status_narration_human_view(payload)
    has_status_contract = isinstance(payload.get("status_narration_contract"), Mapping)
    current_stage = _non_empty_text(human_view.get("current_stage_label")) or _non_empty_text(
        payload.get("current_stage")
    ) or _non_empty_text(payload.get("current_stage_id"))
    if has_status_contract:
        judgment = _non_empty_text(human_view.get("status_summary")) or _non_empty_text(
            human_view.get("latest_update")
        )
    else:
        judgment = _non_empty_text(human_view.get("latest_update")) or _non_empty_text(
            human_view.get("status_summary")
        )
    next_step = _non_empty_text(human_view.get("next_step"))
    if current_stage:
        lines.append(f"- 当前阶段: {current_stage}")
    if judgment:
        lines.append(f"- 当前判断: {judgment}")
    if next_step:
        lines.append(f"- 下一步建议: {next_step}")


_OPERATOR_VERDICT_LABELS = {
    "attention_required": "需要处理",
    "preflight_blocked": "前置检查未通过",
    "ready_for_task": "可直接开始",
    "monitor_only": "持续观察",
}

_WORKSPACE_STATUS_LABELS = {
    "ready": "已就绪",
    "attention_required": "需要处理",
    "blocked": "前置检查未通过",
}

_START_MODE_LABELS = {
    "open_frontdesk": "打开 MAS 前台",
    "submit_task": "给 study 下 durable 任务",
    "continue_study": "启动或续跑 study",
}

_DIRECT_ENTRY_MODE_LABELS = {
    "direct": "直接进入",
    "opl-handoff": "OPL handoff",
}

_RUNTIME_DECISION_LABELS = {
    "resume": "恢复当前运行",
    "launch": "启动新运行",
    "reroute": "改走其他运行路径",
}

_SURFACE_KIND_LABELS = {
    PRODUCT_FRONTDESK_KIND: "MAS 前台",
    "workspace_cockpit": "workspace cockpit",
    "study_task_intake": "study 任务入口",
    "launch_study": "启动或续跑 study",
    "study_progress": "study 进度",
}

_CHECK_STATUS_LABELS = {
    "pass": "通过",
    "fail": "未通过",
    "warning": "需关注",
}

_PHASE5_SEQUENCE_SCOPE_LABELS = {
    "monorepo_landing_readiness": "monorepo 落地就绪度（monorepo_landing_readiness）",
}

_PHASE5_MONOREPO_STATUS_LABELS = {
    "post_gate_target": "post-gate 目标态（post_gate_target）",
}

_USER_INTERACTION_MODE_LABELS = {
    "natural_language_frontdoor": "自然语言前台（natural_language_frontdoor）",
}


def _operator_verdict_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _OPERATOR_VERDICT_LABELS.get(text, text)


def _workspace_status_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _WORKSPACE_STATUS_LABELS.get(text, text)


def _start_mode_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _START_MODE_LABELS.get(text, text.replace("_", " "))


def _direct_entry_mode_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _DIRECT_ENTRY_MODE_LABELS.get(text, text)


def _runtime_decision_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _RUNTIME_DECISION_LABELS.get(text, text)


def _surface_kind_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _SURFACE_KIND_LABELS.get(text, text.replace("_", " "))


def _bool_label(value: object) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return text


def _check_status_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _CHECK_STATUS_LABELS.get(text, text)


def _phase5_sequence_scope_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _PHASE5_SEQUENCE_SCOPE_LABELS.get(text, text)


def _phase5_monorepo_status_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _PHASE5_MONOREPO_STATUS_LABELS.get(text, text)


def _user_interaction_mode_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _USER_INTERACTION_MODE_LABELS.get(text, text)


def _operator_handling_state_label(payload: Mapping[str, Any]) -> str | None:
    explicit_label = _non_empty_text(payload.get("handling_state_label"))
    if explicit_label is not None:
        return explicit_label
    handling_state = _non_empty_text(payload.get("handling_state"))
    if handling_state is None:
        return None
    return study_progress._OPERATOR_STATUS_HANDLING_LABELS.get(
        handling_state,
        handling_state.replace("_", " "),
    )


def _recovery_action_mode_label(payload: Mapping[str, Any]) -> str | None:
    action_mode = _non_empty_text(payload.get("action_mode"))
    if action_mode is None:
        return None
    return study_progress._RECOVERY_ACTION_MODE_LABELS.get(
        action_mode,
        action_mode.replace("_", " "),
    )


def _normalized_strings(values: Iterable[object]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            normalized.append(text)
    return tuple(normalized)


def _build_managed_runtime_contract(
    *,
    domain_owner: str,
    executor_owner: str,
    supervision_status_surface: str,
    attention_queue_surface: str,
    recovery_contract_surface: str,
) -> dict[str, Any]:
    return _build_shared_managed_runtime_contract(
        domain_owner=domain_owner,
        executor_owner=executor_owner,
        supervision_status_surface=supervision_status_surface,
        attention_queue_surface=attention_queue_surface,
        recovery_contract_surface=recovery_contract_surface,
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


def _quote_cli_arg(value: str | Path | None) -> str:
    text = str(value or "").strip()
    if not text:
        return "<profile>"
    return shlex.quote(text)


def _profile_command_prefix(profile_ref: str | Path | None) -> str:
    return f"uv run python -m med_autoscience.cli --help >/dev/null 2>&1 || true\nuv run python -m med_autoscience.cli"


def _profile_arg(profile_ref: str | Path | None) -> str:
    return _quote_cli_arg(Path(profile_ref).expanduser().resolve() if profile_ref is not None else None)


def _command_prefix(profile_ref: str | Path | None) -> str:
    return f"uv run python -m med_autoscience.cli"


def _json_surface_command(command: str) -> str:
    if "--format" in command:
        return command
    return f"{command} --format json"


def _require_direct_entry_mode(value: str | None) -> str:
    mode = _non_empty_text(value) or "direct"
    if mode not in SUPPORTED_DIRECT_ENTRY_MODES:
        raise ValueError(f"direct entry mode 不支持: {mode}")
    return mode


def _study_selector(*, study_id: str | None = None, study_root: Path | None = None) -> str:
    if study_id is not None:
        return f"--study-id {_quote_cli_arg(study_id)}"
    if study_root is not None:
        return f"--study-root {_quote_cli_arg(Path(study_root).expanduser().resolve())}"
    raise ValueError("study_id or study_root is required")


def _inspect_workspace_supervision(profile: WorkspaceProfile) -> dict[str, Any]:
    return hermes_supervision.read_supervision_status(profile=profile)


def _doctor_workspace_supervision_contract(doctor_report: Any) -> dict[str, Any]:
    contract = getattr(doctor_report, "workspace_supervision_contract", None)
    if isinstance(contract, Mapping):
        return dict(contract)
    return {}


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
    if not doctor_report.med_deepscientist_runtime_exists:
        alerts.append("受控 research backend runtime root 不存在，当前无法继续研究执行。")
    if not doctor_report.medical_overlay_ready:
        alerts.append("workspace medical overlay 还未 ready，当前运行前置能力不完整。")
    external_runtime_ready = bool((doctor_report.external_runtime_contract or {}).get("ready"))
    if not external_runtime_ready:
        alerts.append("external Hermes runtime 还未 ready，MAS 会对托管运行 fail-closed。")
    workspace_supervision_contract = _doctor_workspace_supervision_contract(doctor_report)
    workspace_supervision_ready = bool(workspace_supervision_contract.get("loaded"))
    workspace_supervision_summary = _non_empty_text(workspace_supervision_contract.get("summary"))
    if not workspace_supervision_ready:
        alerts.append(
            workspace_supervision_summary
            or "workspace supervision owner 尚未收敛到 canonical Hermes supervision。"
        )
    return alerts


def _build_product_entry_preflight(
    *,
    doctor_report: Any,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    doctor_command = f"{_command_prefix(profile_ref)} doctor --profile {_profile_arg(profile_ref)}"
    start_command = f"{_command_prefix(profile_ref)} product-frontdesk --profile {_profile_arg(profile_ref)}"
    workspace_supervision_contract = _doctor_workspace_supervision_contract(doctor_report)
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
            check_id="research_backend_runtime_ready",
            title="Research Backend Runtime Ready",
            status="pass" if doctor_report.med_deepscientist_runtime_exists else "fail",
            blocking=True,
            summary=(
                "受控 research backend runtime 已就位。"
                if doctor_report.med_deepscientist_runtime_exists
                else "受控 research backend runtime 尚未就位。"
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
            check_id="external_runtime_contract_ready",
            title="External Runtime Contract Ready",
            status="pass" if bool((doctor_report.external_runtime_contract or {}).get("ready")) else "fail",
            blocking=True,
            summary=(
                "external Hermes runtime contract 已 ready。"
                if bool((doctor_report.external_runtime_contract or {}).get("ready"))
                else "external Hermes runtime contract 尚未 ready。"
            ),
            command=doctor_command,
        ),
        _build_shared_program_check(
            check_id="workspace_supervision_contract_ready",
            title="Workspace Supervision Contract Ready",
            status="pass" if bool(workspace_supervision_contract.get("loaded")) else "fail",
            blocking=True,
            summary=(
                "workspace supervision owner 已收敛到 canonical Hermes supervision。"
                if bool(workspace_supervision_contract.get("loaded"))
                else _non_empty_text(workspace_supervision_contract.get("summary"))
                or "workspace supervision owner 仍未收敛到 canonical Hermes supervision。"
            ),
            command=f"{_command_prefix(profile_ref)} runtime-supervision-status --profile {_profile_arg(profile_ref)}",
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
        "当前 product-entry 前置检查已通过，可以先复核 doctor 输出，再进入 research frontdesk。"
        if ready_to_try_now
        else first_blocking_summary
        or "当前仍有 blocking preflight check；请先修复 workspace/runtime/overlay/backend/runtime/supervision contract 再进入 research frontdesk。"
    )
    return _build_shared_product_entry_preflight(
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
        f"{prefix} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
        f"--profile {profile_arg} --ensure-study-runtimes --apply"
    )
    return _build_shared_product_entry_guardrails(
        summary=(
            "把卡住、没进度、监管掉线、需要人工决策和质量阻塞显式投影成可执行恢复回路，"
            "避免研究主线失去监管。"
        ),
        guardrail_classes=[
            _build_shared_guardrail_class(
                guardrail_id="workspace_supervision_gap",
                trigger="workspace-cockpit attention queue / study-progress supervisor freshness",
                symptom="Hermes-hosted supervision 未在线、supervisor tick stale/missing、托管恢复真相不再新鲜。",
                recommended_command=refresh_command,
            ),
            _build_shared_guardrail_class(
                guardrail_id="study_progress_gap",
                trigger="study-progress progress_freshness / workspace-cockpit attention queue",
                symptom="当前 study 进度 stale 或 missing，疑似卡住、空转或没有新的明确推进证据。",
                recommended_command=progress_command,
            ),
            _build_shared_guardrail_class(
                guardrail_id="human_decision_gate",
                trigger="study-progress needs_physician_decision / controller decision gate",
                symptom="当前已前移到医生、PI 或 publication release 的人工判断节点。",
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
                trigger="study-progress intervention_lane / runtime watch figure-loop alerts / publication gate",
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
                surface_kind="runtime_watch_refresh",
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


def _build_phase5_platform_target() -> dict[str, Any]:
    payload = mainline_status.read_mainline_status()
    source = payload.get("platform_target")
    if not isinstance(source, Mapping):
        source = mainline_status._platform_target()
    source_payload = dict(source)
    source_landing_sequence = [
        dict(item)
        for item in source_payload.get("landing_sequence") or []
        if isinstance(item, Mapping)
    ]
    normalized_landing_sequence = [
        _build_shared_program_sequence_step(
            step_id=str(item.get("step_id") or ""),
            phase_id=str(item.get("phase_id") or ""),
            status=str(item.get("status") or ""),
            summary=str(item.get("summary") or ""),
            title=_non_empty_text(item.get("title")),
        )
        for item in source_landing_sequence
    ]
    return _build_shared_platform_target(
        summary=str(source_payload.get("summary") or ""),
        sequence_scope=str(source_payload.get("sequence_scope") or ""),
        current_step_id=str(source_payload.get("current_step_id") or ""),
        current_readiness_summary=str(source_payload.get("current_readiness_summary") or ""),
        north_star_topology=dict(source_payload.get("north_star_topology") or {}),
        target_internal_modules=list(source_payload.get("target_internal_modules") or []),
        landing_sequence=normalized_landing_sequence,
        completed_step_ids=list(source_payload.get("completed_step_ids") or []),
        remaining_step_ids=list(source_payload.get("remaining_step_ids") or []),
        promotion_gates=list(source_payload.get("promotion_gates") or []),
        recommended_phase_command=str(source_payload.get("recommended_phase_command") or ""),
        land_now=list(_normalized_strings(source_payload.get("land_now") or [])),
        not_yet=list(_normalized_strings(source_payload.get("not_yet") or [])),
    )


def _render_phase5_platform_target_markdown_lines(phase5_platform_target: Mapping[str, Any]) -> list[str]:
    current_step_id = _non_empty_text(phase5_platform_target.get("current_step_id")) or "stabilize_user_product_loop"
    north_star_topology = dict(phase5_platform_target.get("north_star_topology") or {})
    monorepo_status = _non_empty_text(north_star_topology.get("monorepo_status")) or "post_gate_target"
    lines = [
        "## Platform Target",
        "",
        f"- 当前摘要: {phase5_platform_target.get('summary') or 'none'}",
        f"- 当前序列范围: {_phase5_sequence_scope_label(phase5_platform_target.get('sequence_scope'))}",
        f"- 当前步骤: `{current_step_id}`",
        f"- 当前就绪判断: {phase5_platform_target.get('current_readiness_summary') or 'none'}",
        f"- monorepo 目标状态: {_phase5_monorepo_status_label(monorepo_status)}",
        f"- 推荐 phase 命令: `{phase5_platform_target.get('recommended_phase_command') or 'none'}`",
        "",
        "## Monorepo Sequence",
        "",
    ]
    landing_sequence = list(phase5_platform_target.get("landing_sequence") or [])
    if landing_sequence:
        for item in landing_sequence:
            if not isinstance(item, Mapping):
                continue
            lines.append(
                f"- `{item.get('step_id')}` [{item.get('status')}] / `{item.get('phase_id')}`: {item.get('summary') or 'none'}"
            )
    else:
        lines.append("- none")
    return lines


def _build_phase2_user_product_loop(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
) -> dict[str, Any]:
    prefix = _command_prefix(profile_ref)
    profile_arg = _profile_arg(profile_ref)
    return mainline_status.build_phase2_user_product_loop_lane(
        frontdesk_command=f"{prefix} product-frontdesk --profile {profile_arg}",
        workspace_cockpit_command=_json_surface_command(
            f"{prefix} workspace-cockpit --profile {profile_arg}"
        ),
        submit_task_command=(
            f"{prefix} submit-study-task --profile {profile_arg} "
            "--study-id <study_id> --task-intent '<task_intent>'"
        ),
        launch_study_command=f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>",
        study_progress_command=_json_surface_command(
            f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>"
        ),
        controller_decisions_ref=str(
            profile.studies_root / "<study_id>" / "artifacts" / "controller_decisions" / "latest.json"
        ),
    )


def _build_phase3_clearance_lane(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
) -> dict[str, Any]:
    prefix = _command_prefix(profile_ref)
    profile_arg = _profile_arg(profile_ref)
    doctor_command = f"{prefix} doctor --profile {profile_arg}"
    hermes_runtime_check_command = f"{prefix} hermes-runtime-check --profile {profile_arg}"
    supervisor_service_command = f"{prefix} runtime-supervision-status --profile {profile_arg}"
    refresh_supervision_command = (
        f"{prefix} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
        f"--profile {profile_arg} --ensure-study-runtimes --apply"
    )
    launch_study_command = f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>"
    study_progress_command = f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>"
    return _build_shared_clearance_lane(
        surface_kind="phase3_host_clearance_lane",
        summary="Phase 3 把 external runtime、Hermes-hosted workspace supervision 和 study recovery proof 扩到更多 workspace/host，并保持 fail-closed。",
        recommended_step_id="external_runtime_contract",
        recommended_command=doctor_command,
        clearance_targets=[
            _build_shared_clearance_target(
                target_id="external_runtime_contract",
                title="Check external Hermes runtime contract",
                commands=[
                    doctor_command,
                    hermes_runtime_check_command,
                ],
            ),
            _build_shared_clearance_target(
                target_id="supervisor_service",
                title="Keep Hermes-hosted workspace supervision online",
                commands=[
                    supervisor_service_command,
                    refresh_supervision_command,
                ],
            ),
            _build_shared_clearance_target(
                target_id="study_recovery_proof",
                title="Prove live study recovery and supervision",
                commands=[
                    launch_study_command,
                    study_progress_command,
                ],
            ),
        ],
        clearance_loop=[
            _build_shared_product_entry_program_step(
                step_id="external_runtime_contract",
                title="先确认 external Hermes runtime contract ready",
                surface_kind="doctor_runtime_contract",
                command=doctor_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="hermes_runtime_check",
                title="确认 Hermes runtime 绑定证据",
                surface_kind="hermes_runtime_check",
                command=hermes_runtime_check_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="supervisor_service",
                title="确认 workspace 常驻监管在线",
                surface_kind="workspace_supervisor_service",
                command=supervisor_service_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="refresh_supervision",
                title="刷新 Hermes-hosted supervision tick",
                surface_kind="runtime_watch_refresh",
                command=refresh_supervision_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="study_recovery_proof",
                title="证明 live study recovery / progress supervision 成立",
                surface_kind="launch_study",
                command=launch_study_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="inspect_study_progress",
                title="读取 study-progress proof",
                surface_kind="study_progress",
                command=study_progress_command,
            ),
        ],
        proof_surfaces=[
            _build_shared_product_entry_program_surface(
                surface_kind="doctor.external_runtime_contract",
                command=doctor_command,
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="study_runtime_status.autonomous_runtime_notice",
                command=f"{prefix} study-runtime-status --profile {profile_arg} --study-id <study_id>",
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="runtime_watch",
                ref=str(profile.studies_root / "<study_id>" / "artifacts" / "runtime_watch" / "latest.json"),
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="runtime_supervision",
                ref=str(profile.studies_root / "<study_id>" / "artifacts" / "runtime_supervision" / "latest.json"),
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="controller_decisions",
                ref=str(profile.studies_root / "<study_id>" / "artifacts" / "controller_decisions" / "latest.json"),
            ),
        ],
        recommended_phase_command=(
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_3_multi_workspace_host_clearance"
        ),
    )


def _build_phase4_backend_deconstruction() -> dict[str, Any]:
    return _build_shared_backend_deconstruction_lane(
        summary="Phase 4 把可迁出的通用 runtime 能力继续迁向 substrate，同时诚实保留 controlled backend executor。",
        substrate_targets=[
            _build_shared_program_capability(
                capability_id="session_run_watch_recovery",
                owner="upstream Hermes-Agent",
                summary="session / run / watch / recovery / scheduling / interruption 继续收归 outer runtime substrate。",
            ),
            _build_shared_program_capability(
                capability_id="backend_generic_runtime_contract",
                owner="MedAutoScience controller boundary",
                summary="controller / transport / durable surface 只认 backend-generic contract 与 explicit runtime handle。",
            ),
        ],
        backend_retained_now=[
            "MedDeepScientist CodexRunner autonomous executor chain",
            "backend-local agent/tool routing and Codex skills",
            "quest-local research execution, paper worktree, and daemon side effects",
        ],
        current_backend_chain=[
            "med_autoscience.runtime_transport.hermes -> med_autoscience.runtime_transport.med_deepscientist",
            "med_deepscientist CodexRunner -> codex exec autonomous agent loop",
        ],
        optional_executor_proofs=[
            {
                "executor_kind": "hermes_native_proof",
                "entrypoint": "MedDeepScientist HermesNativeProofRunner -> run_agent.AIAgent.run_conversation",
                "default_model": "inherit_local_hermes_default",
                "default_reasoning_effort": "inherit_local_hermes_default",
            }
        ],
        promotion_rules=[
            "no claim of backend retirement without owner + contract + tests + proof",
            "executor replacement must be explicit and proof-backed",
            "no physical monorepo absorb before the external gate is cleared",
        ],
        deconstruction_map_doc="docs/program/med_deepscientist_deconstruction_map.md",
        recommended_phase_command=(
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_4_backend_deconstruction"
        ),
    )


def _build_product_entry_start(
    *,
    product_entry_shell: dict[str, Any],
    operator_loop_actions: dict[str, Any],
    family_orchestration: dict[str, Any],
) -> dict[str, Any]:
    return _build_shared_product_entry_start(
        summary=(
            "先从 MAS research frontdesk 进入当前 workspace frontdoor；"
            "需要新任务时先写 durable study task intake，已有 study 时直接恢复研究运行。"
        ),
        recommended_mode_id="open_frontdesk",
        modes=[
            {
                "mode_id": "open_frontdesk",
                "title": "启动 MAS 前台",
                "command": product_entry_shell["product_frontdesk"]["command"],
                "surface_kind": PRODUCT_FRONTDESK_KIND,
                "summary": product_entry_shell["product_frontdesk"]["purpose"],
                "requires": [],
            },
            {
                "mode_id": "submit_task",
                "title": "给 study 下 durable 任务",
                "command": product_entry_shell["submit_study_task"]["command"],
                "surface_kind": "study_task_intake",
                "summary": operator_loop_actions["submit_task"]["summary"],
                "requires": list(operator_loop_actions["submit_task"]["requires"]),
            },
            {
                "mode_id": "continue_study",
                "title": "启动或续跑 study",
                "command": product_entry_shell["launch_study"]["command"],
                "surface_kind": "launch_study",
                "summary": operator_loop_actions["continue_study"]["summary"],
                "requires": list(operator_loop_actions["continue_study"]["requires"]),
            },
        ],
        resume_surface=dict(family_orchestration["resume_contract"]),
        human_gate_ids=_collect_family_human_gate_ids(family_orchestration),
    )


def _build_runtime_inventory_surface(
    *,
    profile: WorkspaceProfile,
    runtime: Mapping[str, Any],
    managed_runtime_contract: Mapping[str, Any],
    product_entry_preflight: Mapping[str, Any],
    operator_loop_surface: Mapping[str, Any],
) -> dict[str, Any]:
    blocking_check_ids = list(product_entry_preflight.get("blocking_check_ids") or [])
    ready_to_try_now = bool(product_entry_preflight.get("ready_to_try_now")) and not blocking_check_ids
    availability = "ready" if ready_to_try_now else "blocked"
    health_status = "healthy" if ready_to_try_now else "attention_required"
    summary = (
        "MAS runtime inventory 已连接 external Hermes runtime，当前可通过 workspace cockpit 持续监管并续跑 study。"
        if ready_to_try_now
        else "MAS runtime inventory 当前存在 blocking preflight，需要先恢复 runtime/监督前置状态。"
    )
    return _build_shared_runtime_inventory(
        summary=summary,
        runtime_owner=str(runtime.get("runtime_owner") or ""),
        domain_owner=str(runtime.get("domain_owner") or ""),
        executor_owner=str(runtime.get("executor_owner") or ""),
        substrate=str(runtime.get("runtime_substrate") or ""),
        availability=availability,
        health_status=health_status,
        status_surface={
            "ref_kind": "workspace_locator",
            "ref": "studies/<study_id>/artifacts/runtime_watch/latest.json",
            "label": "runtime watch event companion",
        },
        attention_surface={
            "ref_kind": "json_pointer",
            "ref": "/operator_loop_surface",
            "label": "workspace cockpit attention surface",
        },
        recovery_surface={
            "ref_kind": "json_pointer",
            "ref": "/managed_runtime_contract/recovery_contract_surface",
            "label": "managed runtime recovery contract surface",
        },
        workspace_binding={
            "workspace_root": str(profile.workspace_root),
            "profile_name": profile.name,
        },
        domain_projection={
            "managed_runtime_backend_id": runtime.get("managed_runtime_backend_id"),
            "managed_runtime_contract": dict(managed_runtime_contract),
            "recommended_loop_surface": operator_loop_surface.get("surface_kind"),
        },
    )


def _build_task_lifecycle_surface(
    *,
    repo_mainline: Mapping[str, Any],
    product_entry_status: Mapping[str, Any],
    product_entry_readiness: Mapping[str, Any],
    family_orchestration: Mapping[str, Any],
    operator_loop_surface: Mapping[str, Any],
    product_entry_shell: Mapping[str, Any],
) -> dict[str, Any]:
    program_id = _non_empty_text(repo_mainline.get("program_id")) or TARGET_DOMAIN_ID
    stage_id = _non_empty_text(repo_mainline.get("current_stage_id")) or _non_empty_text(
        repo_mainline.get("current_program_phase_id")
    ) or "unknown-stage"
    lifecycle_status = _non_empty_text(repo_mainline.get("current_stage_status")) or _non_empty_text(
        repo_mainline.get("current_program_phase_status")
    ) or "unknown"
    lifecycle_summary = _non_empty_text(product_entry_status.get("summary")) or "MAS product entry lane is active."
    checkpoint_summary = _build_shared_checkpoint_summary(
        status="ready" if bool(product_entry_readiness.get("good_to_use_now")) else "monitoring_required",
        summary=(
            "当前 lane 已进入可执行状态，继续通过 workspace cockpit 和 study progress 维持监督与恢复闭环。"
            if bool(product_entry_readiness.get("usable_now"))
            else "当前 lane 需要先完成 blocking preflight 后再恢复常规执行。"
        ),
        checkpoint_id=f"{program_id}:{stage_id}",
        lineage_ref=dict(family_orchestration.get("checkpoint_lineage_surface") or {}),
        verification_ref=dict(family_orchestration.get("event_envelope_surface") or {}),
    )
    return _build_shared_task_lifecycle(
        task_kind="mas_product_entry_mainline",
        task_id=f"{program_id}:{stage_id}",
        status=lifecycle_status,
        summary=lifecycle_summary,
        progress_surface={
            "surface_kind": "workspace_cockpit",
            "summary": "读取 workspace attention queue、监督在线态与研究入口回路。",
            "command": str(operator_loop_surface.get("command") or ""),
            "step_id": "inspect_workspace_inbox",
            "locator_fields": ["profile_ref"],
        },
        resume_surface={
            "surface_kind": "launch_study",
            "summary": "按 study_id 启动或续跑当前研究。",
            "command": str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
            "step_id": "continue_study",
            "locator_fields": ["study_id"],
        },
        checkpoint_summary=checkpoint_summary,
        human_gate_ids=_collect_family_human_gate_ids(family_orchestration),
        domain_projection={
            "current_program_phase_id": repo_mainline.get("current_program_phase_id"),
            "recommended_loop_surface": operator_loop_surface.get("surface_kind"),
            "recommended_loop_command": operator_loop_surface.get("command"),
        },
    )


def _build_skill_catalog_surface(
    *,
    product_entry_status: Mapping[str, Any],
    domain_entry_contract: Mapping[str, Any],
    product_entry_shell: Mapping[str, Any],
) -> dict[str, Any]:
    summary = _non_empty_text(product_entry_status.get("summary")) or "MAS product entry skill catalog."
    skills = [
        _build_shared_skill_descriptor(
            skill_id="mas_product_frontdesk",
            title="MAS product frontdesk",
            owner=TARGET_DOMAIN_ID,
            distribution_mode="repo_tracked",
            surface_kind=PRODUCT_FRONTDESK_KIND,
            description="启动 MAS 当前产品入口并进入 research frontdoor。",
            command=str((product_entry_shell.get("product_frontdesk") or {}).get("command") or ""),
            readiness="landed",
            tags=["entry", "frontdesk", "study"],
            domain_projection={"shell_key": "product_frontdesk"},
        ),
        _build_shared_skill_descriptor(
            skill_id="mas_workspace_cockpit",
            title="MAS workspace cockpit",
            owner=TARGET_DOMAIN_ID,
            distribution_mode="repo_tracked",
            surface_kind="workspace_cockpit",
            description="读取 workspace attention queue、监督状态与当前研究入口回路。",
            command=str((product_entry_shell.get("workspace_cockpit") or {}).get("command") or ""),
            readiness="landed",
            tags=["workspace", "runtime", "monitoring"],
            domain_projection={"shell_key": "workspace_cockpit"},
        ),
        _build_shared_skill_descriptor(
            skill_id="mas_submit_study_task",
            title="MAS submit study task",
            owner=TARGET_DOMAIN_ID,
            distribution_mode="repo_tracked",
            surface_kind="study_task_intake",
            description="把任务写入 durable study task intake，作为后续执行真相源。",
            command=str((product_entry_shell.get("submit_study_task") or {}).get("command") or ""),
            readiness="landed",
            tags=["study", "intake", "task"],
            domain_projection={"shell_key": "submit_study_task"},
        ),
        _build_shared_skill_descriptor(
            skill_id="mas_launch_study",
            title="MAS launch study",
            owner=TARGET_DOMAIN_ID,
            distribution_mode="repo_tracked",
            surface_kind="launch_study",
            description="创建或恢复 study runtime，并切回当前研究主线。",
            command=str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
            readiness="landed",
            tags=["study", "runtime", "resume"],
            domain_projection={"shell_key": "launch_study"},
        ),
        _build_shared_skill_descriptor(
            skill_id="mas_study_progress",
            title="MAS study progress",
            owner=TARGET_DOMAIN_ID,
            distribution_mode="repo_tracked",
            surface_kind="study_progress",
            description="持续读取当前阶段、阻塞、监督 freshness 与恢复建议。",
            command=str((product_entry_shell.get("study_progress") or {}).get("command") or ""),
            readiness="landed",
            tags=["study", "progress", "recovery"],
            domain_projection={"shell_key": "study_progress"},
        ),
    ]
    return _build_shared_skill_catalog(
        summary=summary,
        skills=skills,
        supported_commands=list(domain_entry_contract.get("supported_commands") or []),
        command_contracts=[
            dict(item)
            for item in (domain_entry_contract.get("command_contracts") or [])
            if isinstance(item, Mapping)
        ],
    )


def _build_automation_surface(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    product_entry_status: Mapping[str, Any],
) -> dict[str, Any]:
    summary = _non_empty_text(product_entry_status.get("summary")) or "MAS automation entry surface."
    refresh_command = (
        f"{_command_prefix(profile_ref)} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
        f"--profile {_profile_arg(profile_ref)} --ensure-study-runtimes --apply"
    )
    runtime_supervision = _build_shared_automation_descriptor(
        automation_id="mas_runtime_supervision_loop",
        title="MAS runtime supervision loop",
        owner=TARGET_DOMAIN_ID,
        trigger_kind="interval",
        target_surface_kind="runtime_watch_refresh",
        summary="按监督节拍刷新 study runtime，保持恢复建议和 attention queue 为最新状态。",
        readiness_status="automation_ready",
        gate_policy="publication_gated",
        output_expectation=[
            "refresh runtime watch",
            "update workspace attention queue",
            "preserve controller decision lineage",
        ],
        target_command=refresh_command,
        domain_projection={
            "service_status_command": str(
                profile.workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status"
            ),
            "recommended_entry_surface": "workspace_cockpit",
        },
    )
    return _build_shared_automation_catalog(
        summary=summary,
        automations=[runtime_supervision],
        readiness_summary=render_automation_ready_summary(),
    )


def _workspace_supervision_summary(
    *,
    studies: list[dict[str, Any]],
    service: dict[str, Any],
) -> dict[str, Any]:
    counts = {
        "total": len(studies),
        "supervisor_fresh": 0,
        "supervisor_gap": 0,
        "recovery_required": 0,
        "quality_blocked": 0,
        "progress_fresh": 0,
        "progress_stale": 0,
        "progress_missing": 0,
        "needs_physician_decision": 0,
    }
    for item in studies:
        monitoring = dict(item.get("monitoring") or {})
        supervisor_tick_status = _non_empty_text(monitoring.get("supervisor_tick_status"))
        if supervisor_tick_status == "fresh":
            counts["supervisor_fresh"] += 1
        elif supervisor_tick_status in {"stale", "missing", "invalid"}:
            counts["supervisor_gap"] += 1

        intervention_lane = dict(item.get("intervention_lane") or {})
        lane_id = _non_empty_text(intervention_lane.get("lane_id"))
        if lane_id == "runtime_recovery_required":
            counts["recovery_required"] += 1
        elif lane_id == "quality_floor_blocker":
            counts["quality_blocked"] += 1

        progress_freshness = dict(item.get("progress_freshness") or {})
        freshness_status = _non_empty_text(progress_freshness.get("status"))
        if freshness_status == "fresh":
            counts["progress_fresh"] += 1
        elif freshness_status == "stale":
            counts["progress_stale"] += 1
        elif freshness_status == "missing":
            counts["progress_missing"] += 1

        if bool(item.get("needs_physician_decision")):
            counts["needs_physician_decision"] += 1

    summary = (
        f"{counts['total']} 个 study；"
        f"{counts['supervisor_gap']} 个监管心跳缺口；"
        f"{counts['recovery_required']} 个恢复异常；"
        f"{counts['quality_blocked']} 个质量阻塞；"
        f"{counts['progress_stale']} 个进度陈旧；"
        f"{counts['progress_missing']} 个缺少明确进度信号。"
    )
    return {
        "service": service,
        "study_counts": counts,
        "summary": summary,
    }


def _mainline_snapshot() -> dict[str, Any]:
    payload = mainline_status.read_mainline_status()
    current_stage = dict(payload.get("current_stage") or {})
    current_program_phase = dict(payload.get("current_program_phase") or {})
    next_focus = _normalized_strings(payload.get("next_focus") or [])
    explicitly_not_now = _normalized_strings(payload.get("explicitly_not_now") or [])
    single_project_boundary = _validate_single_project_boundary(
        _single_project_boundary_payload(payload.get("single_project_boundary")),
        context="mainline_snapshot.single_project_boundary",
    )
    return {
        "program_id": _non_empty_text(payload.get("program_id")),
        "current_stage_id": _non_empty_text(current_stage.get("id")),
        "current_stage_status": _non_empty_text(current_stage.get("status")),
        "current_stage_summary": _non_empty_text(current_stage.get("summary")),
        "current_program_phase_id": _non_empty_text(current_program_phase.get("id")),
        "current_program_phase_status": _non_empty_text(current_program_phase.get("status")),
        "current_program_phase_summary": _non_empty_text(current_program_phase.get("summary")),
        "next_focus": list(next_focus),
        "explicitly_not_now": list(explicitly_not_now),
        "single_project_boundary": single_project_boundary,
    }


def _attention_item(
    *,
    code: str,
    title: str,
    summary: str,
    recommended_step_id: str | None,
    recommended_command: str | None,
    scope: str,
    study_id: str | None = None,
    operator_status_card: dict[str, Any] | None = None,
    autonomy_contract: dict[str, Any] | None = None,
    quality_closure_truth: dict[str, Any] | None = None,
    quality_execution_lane: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "priority": _ATTENTION_PRIORITIES.get(code, 999),
        "scope": scope,
        "study_id": study_id,
        "code": code,
        "title": title,
        "summary": summary,
        "recommended_step_id": recommended_step_id,
        "recommended_command": recommended_command,
        "operator_status_card": dict(operator_status_card or {}) or None,
        "autonomy_contract": dict(autonomy_contract or {}) or None,
        "quality_closure_truth": dict(quality_closure_truth or {}) or None,
        "quality_execution_lane": dict(quality_execution_lane or {}) or None,
    }


def _operator_status_summary(card: Mapping[str, Any] | None) -> str | None:
    if not isinstance(card, Mapping):
        return None
    return _non_empty_text(card.get("user_visible_verdict")) or _non_empty_text(card.get("owner_summary"))


def _quality_route_focus(intervention_lane: Mapping[str, Any] | None) -> str | None:
    if not isinstance(intervention_lane, Mapping):
        return None
    return _non_empty_text(intervention_lane.get("route_summary"))


def _quality_execution_focus(item: Mapping[str, Any] | None) -> str | None:
    if not isinstance(item, Mapping):
        return None
    quality_execution_lane = dict(item.get("quality_execution_lane") or {})
    route_key_question = _non_empty_text(quality_execution_lane.get("route_key_question"))
    if route_key_question is not None:
        return route_key_question
    return _non_empty_text(quality_execution_lane.get("summary"))


def _quality_execution_lane_title(study_id: str, lane: Mapping[str, Any] | None) -> str | None:
    if not isinstance(lane, Mapping):
        return None
    lane_id = _non_empty_text(lane.get("lane_id"))
    if lane_id == "reviewer_first":
        return f"{study_id} 当前先做 reviewer-first 收口"
    if lane_id == "claim_evidence":
        return f"{study_id} 当前先做 claim-evidence 修复"
    if lane_id == "submission_hardening":
        return f"{study_id} 当前先做 submission hardening 收口"
    if lane_id == "write_ready":
        return f"{study_id} 当前进入同线写作推进"
    if lane_id == "general_quality_repair":
        return f"{study_id} 当前先做质量修复收口"
    return None


def _attention_step_id(code: str) -> str:
    if code == "workspace_supervisor_service_not_loaded":
        return "inspect_supervision_service"
    if code == "study_supervision_gap":
        return "refresh_supervision"
    if code == "study_runtime_recovery_required":
        return "continue_or_relaunch"
    return "inspect_study_progress"


def _quality_blocker_title(study_id: str, intervention_lane: Mapping[str, Any] | None) -> str:
    if not isinstance(intervention_lane, Mapping):
        return f"{study_id} 当前存在质量硬阻塞"
    repair_mode = _non_empty_text(intervention_lane.get("repair_mode"))
    route_target_label = _non_empty_text(intervention_lane.get("route_target_label"))
    if route_target_label is None:
        return f"{study_id} 当前存在质量硬阻塞"
    if repair_mode == "bounded_analysis":
        return f"{study_id} 当前需要进入{route_target_label}完成有限补充分析"
    return f"{study_id} 当前需要回到{route_target_label}修复质量阻塞"


def _workspace_operator_brief(
    *,
    workspace_status: str,
    workspace_alerts: list[str],
    attention_queue: list[dict[str, Any]],
    studies: list[dict[str, Any]],
    user_loop: dict[str, str],
    commands: dict[str, str],
) -> dict[str, Any]:
    if workspace_status == "blocked":
        summary = _non_empty_text(workspace_alerts[0] if workspace_alerts else None) or (
            "当前 workspace 还没有通过正式前置检查，先不要盲目启动研究。"
        )
        return {
            "surface_kind": "workspace_operator_brief",
            "verdict": "preflight_blocked",
            "summary": summary,
            "should_intervene_now": True,
            "focus_scope": "workspace",
            "focus_study_id": None,
            "recommended_step_id": "run_doctor",
            "recommended_command": commands.get("doctor"),
        }
    if attention_queue:
        top = dict(attention_queue[0] or {})
        operator_status_card = dict(top.get("operator_status_card") or {})
        brief = {
            "surface_kind": "workspace_operator_brief",
            "verdict": "attention_required",
            "summary": _operator_status_summary(operator_status_card)
            or _non_empty_text(top.get("summary"))
            or _non_empty_text(top.get("title"))
            or "当前 workspace 有需要优先处理的 attention item。",
            "should_intervene_now": True,
            "focus_scope": _non_empty_text(top.get("scope")) or "workspace",
            "focus_study_id": _non_empty_text(top.get("study_id")),
            "recommended_step_id": _non_empty_text(top.get("recommended_step_id")) or "handle_attention_item",
            "recommended_command": _non_empty_text(top.get("recommended_command")) or commands.get("doctor"),
        }
        current_focus = _non_empty_text(operator_status_card.get("current_focus")) or _quality_execution_focus(top)
        if current_focus is not None:
            brief["current_focus"] = current_focus
        next_confirmation_signal = _non_empty_text(operator_status_card.get("next_confirmation_signal"))
        if next_confirmation_signal is not None:
            brief["next_confirmation_signal"] = next_confirmation_signal
        return brief
    if not studies:
        return {
            "surface_kind": "workspace_operator_brief",
            "verdict": "ready_for_task",
            "summary": "当前 workspace 已 ready，下一步先给目标 study 写 durable task intake。",
            "should_intervene_now": False,
            "focus_scope": "workspace",
            "focus_study_id": None,
            "recommended_step_id": "submit_task",
            "recommended_command": user_loop.get("submit_task_template"),
        }

    lead_study = dict(studies[0] or {})
    lead_study_id = _non_empty_text(lead_study.get("study_id"))
    lead_status_card = dict(lead_study.get("operator_status_card") or {})
    recommended_command = _non_empty_text(lead_study.get("recommended_command")) or _non_empty_text(
        ((lead_study.get("commands") or {}).get("progress"))
    )
    summary = (
        _operator_status_summary(lead_status_card)
        or (
            f"当前没有新的 workspace 级硬告警，继续盯住 {lead_study_id} 的进度与监管即可。"
        if lead_study_id is not None
        else "当前没有新的 workspace 级硬告警，继续保持对活跃 study 的监管即可。"
        )
    )
    brief = {
        "surface_kind": "workspace_operator_brief",
        "verdict": "monitor_only",
        "summary": summary,
        "should_intervene_now": False,
        "focus_scope": "study",
        "focus_study_id": lead_study_id,
        "recommended_step_id": "inspect_progress",
        "recommended_command": recommended_command or user_loop.get("open_workspace_cockpit"),
    }
    current_focus = _non_empty_text(lead_status_card.get("current_focus"))
    if current_focus is not None:
        brief["current_focus"] = current_focus
    next_confirmation_signal = _non_empty_text(lead_status_card.get("next_confirmation_signal"))
    if next_confirmation_signal is not None:
        brief["next_confirmation_signal"] = next_confirmation_signal
    return brief


def _attention_queue(
    *,
    workspace_status: str,
    workspace_supervision: dict[str, Any],
    studies: list[dict[str, Any]],
    commands: dict[str, str],
) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    service = dict(workspace_supervision.get("service") or {})
    study_counts = dict(workspace_supervision.get("study_counts") or {})
    service_loaded = bool(service.get("loaded"))
    if not service_loaded or bool(service.get("drift_reasons")):
        queue.append(
            _attention_item(
                code="workspace_supervisor_service_not_loaded",
                title="先恢复 Hermes-hosted 常驻监管",
                summary=_non_empty_text(service.get("summary"))
                or "当前 workspace 还没有稳定的 Hermes-hosted 常驻监管入口。",
                recommended_step_id=_attention_step_id("workspace_supervisor_service_not_loaded"),
                recommended_command=commands.get("service_status") or commands.get("service_install"),
                scope="workspace",
            )
        )

    for item in studies:
        study_id = _non_empty_text(item.get("study_id")) or "unknown-study"
        monitoring = dict(item.get("monitoring") or {})
        progress_freshness = dict(item.get("progress_freshness") or {})
        blocker_list = list(item.get("current_blockers") or [])
        operator_verdict = dict(item.get("operator_verdict") or {})
        operator_status_card = dict(item.get("operator_status_card") or {})
        autonomy_contract = dict(item.get("autonomy_contract") or {})
        quality_closure_truth = dict(item.get("quality_closure_truth") or {})
        quality_execution_lane = dict(item.get("quality_execution_lane") or {})
        progress_command = _non_empty_text(((item.get("commands") or {}).get("progress")))
        launch_command = _non_empty_text(((item.get("commands") or {}).get("launch")))
        preferred_command = _non_empty_text(item.get("recommended_command")) or _non_empty_text(
            operator_verdict.get("primary_command")
        )
        supervisor_tick_status = _non_empty_text(monitoring.get("supervisor_tick_status"))
        progress_status = _non_empty_text(progress_freshness.get("status"))
        current_stage_summary = _non_empty_text(item.get("current_stage_summary"))
        next_system_action = _non_empty_text(item.get("next_system_action"))
        intervention_lane = dict(item.get("intervention_lane") or {})
        lane_id = _non_empty_text(intervention_lane.get("lane_id"))
        autonomy_summary = _non_empty_text(autonomy_contract.get("summary"))
        lane_summary = (
            _operator_status_summary(operator_status_card)
            or _non_empty_text(operator_verdict.get("summary"))
            or _non_empty_text(intervention_lane.get("summary"))
            or current_stage_summary
            or next_system_action
        )

        if lane_id == "human_decision_gate" or bool(item.get("needs_physician_decision")):
            queue.append(
                _attention_item(
                    code="study_needs_physician_decision",
                    title=f"{study_id} 需要医生或 PI 判断",
                    summary=lane_summary or "当前 study 已到需要人工明确决策的节点。",
                    recommended_step_id=_attention_step_id("study_needs_physician_decision"),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                )
            )
            continue
        if lane_id == "workspace_supervision_gap" or supervisor_tick_status in {"stale", "missing", "invalid"}:
            queue.append(
                _attention_item(
                    code="study_supervision_gap",
                    title=f"{study_id} 当前失去新鲜监管心跳",
                    summary=lane_summary or "Hermes-hosted 托管监管存在缺口。",
                    recommended_step_id=_attention_step_id("study_supervision_gap"),
                    recommended_command=preferred_command or commands.get("supervisor_tick") or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                )
            )
            continue
        if lane_id == "runtime_recovery_required":
            queue.append(
                _attention_item(
                    code="study_runtime_recovery_required",
                    title=f"{study_id} 当前需要优先处理 runtime recovery",
                    summary=autonomy_summary or lane_summary or "托管运行恢复失败或健康降级，需要尽快介入。",
                    recommended_step_id=_attention_step_id("study_runtime_recovery_required"),
                    recommended_command=preferred_command or launch_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                )
            )
            continue
        if lane_id == "quality_floor_blocker":
            route_focus = _quality_route_focus(intervention_lane)
            queue.append(
                _attention_item(
                    code="study_quality_floor_blocker",
                    title=_quality_blocker_title(study_id, intervention_lane),
                    summary=(
                        _non_empty_text(quality_execution_lane.get("summary"))
                        or
                        route_focus
                        or
                        lane_summary
                        or _non_empty_text(blocker_list[0] if blocker_list else None)
                        or "当前 study 存在质量或发表门控硬阻塞。"
                    ),
                    recommended_step_id=_attention_step_id("study_quality_floor_blocker"),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                )
            )
            continue
        if progress_status == "stale":
            queue.append(
                _attention_item(
                    code="study_progress_stale",
                    title=f"{study_id} 进度信号已陈旧",
                    summary=_non_empty_text(progress_freshness.get("summary"))
                    or "最近缺少新的明确研究推进记录，需要排查是否卡住或空转。",
                    recommended_step_id=_attention_step_id("study_progress_stale"),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                )
            )
            continue
        if progress_status == "missing":
            queue.append(
                _attention_item(
                    code="study_progress_missing",
                    title=f"{study_id} 缺少明确进度信号",
                    summary=_non_empty_text(progress_freshness.get("summary"))
                    or "当前还没有看到明确的研究推进记录。",
                    recommended_step_id=_attention_step_id("study_progress_missing"),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                )
            )
            continue
        if blocker_list or workspace_status in {"attention_required", "blocked"}:
            quality_lane_title = _quality_execution_lane_title(study_id, quality_execution_lane)
            queue.append(
                _attention_item(
                    code="study_blocked",
                    title=quality_lane_title or f"{study_id} 仍有主线阻塞",
                    summary=_non_empty_text(quality_execution_lane.get("summary"))
                    or _non_empty_text(blocker_list[0] if blocker_list else None)
                    or current_stage_summary
                    or next_system_action
                    or "当前 study 仍有待收口问题。",
                    recommended_step_id=_attention_step_id("study_blocked"),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                    operator_status_card=operator_status_card,
                    autonomy_contract=autonomy_contract,
                    quality_closure_truth=quality_closure_truth,
                    quality_execution_lane=quality_execution_lane,
                )
            )

    return sorted(
        queue,
        key=lambda item: (
            int(item.get("priority", 999)),
            str(item.get("study_id") or ""),
            str(item.get("code") or ""),
        ),
    )


def _user_loop(*, profile: WorkspaceProfile, profile_ref: str | Path | None) -> dict[str, str]:
    profile_arg = _profile_arg(profile_ref)
    prefix = _command_prefix(profile_ref)
    return {
        "mainline_status": f"{prefix} mainline-status",
        "phase_status_current": f"{prefix} mainline-phase --phase current",
        "phase_status_next": f"{prefix} mainline-phase --phase next",
        "open_workspace_cockpit": f"{prefix} workspace-cockpit --profile {profile_arg}",
        "submit_task_template": (
            f"{prefix} submit-study-task --profile {profile_arg} --study-id <study_id> "
            "--task-intent '<task_intent>'"
        ),
        "launch_study_template": f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>",
        "watch_progress_template": f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>",
        "refresh_supervision": (
            f"{prefix} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {profile_arg} --ensure-study-runtimes --apply"
        ),
    }


def _study_item(
    *,
    progress_payload: dict[str, Any],
    profile_ref: str | Path | None,
) -> dict[str, Any]:
    study_id = str(progress_payload.get("study_id") or "").strip()
    commands = {
        "launch": (
            f"{_command_prefix(profile_ref)} launch-study --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=study_id)}"
        ),
        "progress": (
            f"{_command_prefix(profile_ref)} study-progress --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=study_id)}"
        ),
        "status": (
            f"{_command_prefix(profile_ref)} study-runtime-status --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=study_id)}"
        ),
    }
    supervision = dict(progress_payload.get("supervision") or {})
    monitoring = {
        "browser_url": _non_empty_text(supervision.get("browser_url")),
        "quest_session_api_url": _non_empty_text(supervision.get("quest_session_api_url")),
        "active_run_id": _non_empty_text(supervision.get("active_run_id")),
        "health_status": _non_empty_text(supervision.get("health_status")),
        "supervisor_tick_status": _non_empty_text(supervision.get("supervisor_tick_status")),
    }
    task_intake = dict(progress_payload.get("task_intake") or {})
    progress_freshness = dict(progress_payload.get("progress_freshness") or {})
    intervention_lane = dict(progress_payload.get("intervention_lane") or {})
    operator_verdict = dict(progress_payload.get("operator_verdict") or {})
    operator_status_card = dict(progress_payload.get("operator_status_card") or {})
    recommended_command = _non_empty_text(progress_payload.get("recommended_command"))
    recommended_commands = [
        dict(item)
        for item in (progress_payload.get("recommended_commands") or [])
        if isinstance(item, dict)
    ]
    autonomy_contract = dict(progress_payload.get("autonomy_contract") or {})
    quality_closure_truth = dict(progress_payload.get("quality_closure_truth") or {})
    quality_execution_lane = dict(progress_payload.get("quality_execution_lane") or {})
    quality_review_loop = dict(progress_payload.get("quality_review_loop") or {})
    recovery_contract = dict(progress_payload.get("recovery_contract") or {})
    return {
        "study_id": study_id,
        "current_stage": progress_payload.get("current_stage"),
        "current_stage_summary": progress_payload.get("current_stage_summary"),
        "current_blockers": list(progress_payload.get("current_blockers") or []),
        "next_system_action": progress_payload.get("next_system_action"),
        "intervention_lane": intervention_lane or None,
        "operator_verdict": operator_verdict or None,
        "operator_status_card": operator_status_card or None,
        "recommended_command": recommended_command,
        "recommended_commands": recommended_commands,
        "autonomy_contract": autonomy_contract or None,
        "quality_closure_truth": quality_closure_truth or None,
        "quality_execution_lane": quality_execution_lane or None,
        "quality_review_loop": quality_review_loop or None,
        "recovery_contract": recovery_contract or None,
        "needs_physician_decision": bool(progress_payload.get("needs_physician_decision")),
        "monitoring": monitoring,
        "task_intake": task_intake or None,
        "progress_freshness": progress_freshness or None,
        "commands": commands,
    }


def read_workspace_cockpit(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    doctor_report = build_doctor_report(profile)
    workspace_alerts = _workspace_ready_alerts(doctor_report)
    studies: list[dict[str, Any]] = []
    for study_root in sorted(path for path in profile.studies_root.iterdir() if path.is_dir()) if profile.studies_root.exists() else []:
        if not (study_root / "study.yaml").exists():
            continue
        progress_payload = study_progress.read_study_progress(
            profile=profile,
            profile_ref=profile_ref,
            study_root=study_root,
        )
        item = _study_item(progress_payload=progress_payload, profile_ref=profile_ref)
        studies.append(item)
        for blocker in item["current_blockers"]:
            if blocker not in workspace_alerts:
                workspace_alerts.append(blocker)
        progress_freshness = dict(item.get("progress_freshness") or {})
        progress_summary = _non_empty_text(progress_freshness.get("summary"))
        if _non_empty_text(progress_freshness.get("status")) in {"stale", "missing"} and progress_summary not in workspace_alerts:
            workspace_alerts.append(progress_summary)
    service = _inspect_workspace_supervision(profile)
    workspace_supervision = _workspace_supervision_summary(studies=studies, service=service)
    if (
        (not bool(service.get("loaded")) or bool(service.get("drift_reasons")))
        and service.get("summary") not in workspace_alerts
    ):
        workspace_alerts.append(str(service.get("summary")))
    baseline_alerts = _workspace_ready_alerts(doctor_report)
    if workspace_alerts and not baseline_alerts:
        workspace_status = "attention_required"
    elif baseline_alerts:
        workspace_status = "blocked"
    else:
        workspace_status = "ready"
    mainline_snapshot = _mainline_snapshot()
    commands = {
        "mainline_status": f"{_command_prefix(profile_ref)} mainline-status",
        "doctor": f"{_command_prefix(profile_ref)} doctor --profile {_profile_arg(profile_ref)}",
        "bootstrap": f"{_command_prefix(profile_ref)} bootstrap --profile {_profile_arg(profile_ref)}",
        "supervisor_tick": (
            f"{_command_prefix(profile_ref)} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {_profile_arg(profile_ref)} --ensure-study-runtimes --apply"
        ),
        "service_install": f"{_command_prefix(profile_ref)} runtime-ensure-supervision --profile {_profile_arg(profile_ref)}",
        "service_status": f"{_command_prefix(profile_ref)} runtime-supervision-status --profile {_profile_arg(profile_ref)}",
    }
    attention_queue = _attention_queue(
        workspace_status=workspace_status,
        workspace_supervision=workspace_supervision,
        studies=studies,
        commands=commands,
    )
    user_loop = _user_loop(profile=profile, profile_ref=profile_ref)
    operator_brief = _workspace_operator_brief(
        workspace_status=workspace_status,
        workspace_alerts=workspace_alerts,
        attention_queue=attention_queue,
        studies=studies,
        user_loop=user_loop,
        commands=commands,
    )
    phase2_user_product_loop = _build_phase2_user_product_loop(
        profile=profile,
        profile_ref=profile_ref,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "profile_name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "workspace_status": workspace_status,
        "mainline_snapshot": mainline_snapshot,
        "workspace_alerts": workspace_alerts,
        "workspace_supervision": workspace_supervision,
        "attention_queue": attention_queue,
        "operator_brief": operator_brief,
        "user_loop": user_loop,
        "phase2_user_product_loop": phase2_user_product_loop,
        "studies": studies,
        "commands": commands,
    }


def render_workspace_cockpit_markdown(payload: dict[str, Any]) -> str:
    mainline_snapshot = dict(payload.get("mainline_snapshot") or {})
    workspace_supervision = dict(payload.get("workspace_supervision") or {})
    service = dict(workspace_supervision.get("service") or {})
    study_counts = dict(workspace_supervision.get("study_counts") or {})
    operator_brief = dict(payload.get("operator_brief") or {})
    phase2_user_product_loop = dict(payload.get("phase2_user_product_loop") or {})
    lines = [
        "# Workspace Cockpit",
        "",
        f"- profile: `{payload.get('profile_name')}`",
        f"- workspace_root: `{payload.get('workspace_root')}`",
        f"- 当前 workspace 状态: {_workspace_status_label(payload.get('workspace_status'))}",
        "",
        "## Now",
        "",
    ]
    if operator_brief:
        lines.append(f"- 当前状态: {_operator_verdict_label(operator_brief.get('verdict'))}")
        lines.append(f"- 当前处理摘要: {operator_brief.get('summary') or 'none'}")
        lines.append(f"- 是否需要立刻介入: {'是' if operator_brief.get('should_intervene_now') else '否'}")
        lines.append(f"- 推荐动作: `{operator_brief.get('recommended_step_id') or 'none'}`")
        lines.append(f"- 推荐命令: `{operator_brief.get('recommended_command') or 'none'}`")
        if operator_brief.get("focus_study_id"):
            lines.append(f"- 聚焦 study: `{operator_brief.get('focus_study_id')}`")
        if operator_brief.get("current_focus"):
            lines.append(f"- 当前清障重点: {operator_brief.get('current_focus')}")
        if operator_brief.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {operator_brief.get('next_confirmation_signal')}")
    else:
        lines.append("- 当前还没有 operator brief。")
    lines.extend([
        "",
        "## Mainline Snapshot",
        "",
    ])
    if mainline_snapshot:
        lines.append(f"- 当前 program: `{mainline_snapshot.get('program_id') or 'unknown'}`")
        lines.append(f"- 当前主线阶段: `{mainline_snapshot.get('current_stage_id') or 'unknown'}`")
        if mainline_snapshot.get("current_stage_summary"):
            lines.append(f"- 当前判断: {mainline_snapshot.get('current_stage_summary')}")
        if mainline_snapshot.get("current_program_phase_id"):
            lines.append(
                f"- 当前 program phase: `{mainline_snapshot.get('current_program_phase_id')}`"
            )
        if mainline_snapshot.get("current_program_phase_summary"):
            lines.append(f"- program phase 摘要: {mainline_snapshot.get('current_program_phase_summary')}")
        next_focus = list(mainline_snapshot.get("next_focus") or [])
        if next_focus:
            lines.append(f"- 下一步焦点: {next_focus[0]}")
    else:
        lines.append("- 当前还没有 repo 主线快照。")
    lines.extend([
        "",
        "## Workspace Supervision",
        "",
    ])
    if workspace_supervision:
        lines.append(f"- 当前监管摘要: {workspace_supervision.get('summary')}")
        if service.get("summary"):
            lines.append(f"- 监管服务: {service.get('summary')}")
        if study_counts:
            lines.append(
                "- 当前计数: "
                f"监管缺口 {study_counts.get('supervisor_gap', 0)}；"
                f"需要恢复 {study_counts.get('recovery_required', 0)}；"
                f"质量阻塞 {study_counts.get('quality_blocked', 0)}；"
                f"进度陈旧 {study_counts.get('progress_stale', 0)}；"
                f"进度缺失 {study_counts.get('progress_missing', 0)}；"
                f"等待医生判断 {study_counts.get('needs_physician_decision', 0)}"
            )
    else:
        lines.append("- 当前还没有 workspace 级监管汇总。")
    lines.extend(
        [
            "",
        "## Workspace Alerts",
        "",
        ]
    )
    workspace_alerts = list(payload.get("workspace_alerts") or [])
    if workspace_alerts:
        lines.extend(f"- {item}" for item in workspace_alerts)
    else:
        lines.append("- 当前没有新的 workspace 级硬告警。")
    lines.extend(["", "## Attention Queue", ""])
    attention_queue = list(payload.get("attention_queue") or [])
    if attention_queue:
        for item in attention_queue:
            title = _non_empty_text(item.get("title")) or "未命名关注项"
            lines.append(f"- 当前关注项: {title}")
            if item.get("summary"):
                lines.append(f"  当前判断: {item.get('summary')}")
            autonomy_contract = dict(item.get("autonomy_contract") or {})
            if autonomy_contract.get("summary"):
                lines.append(f"  自治合同: {autonomy_contract.get('summary')}")
            quality_closure_truth = dict(item.get("quality_closure_truth") or {})
            if quality_closure_truth.get("summary"):
                lines.append(f"  质量闭环: {quality_closure_truth.get('summary')}")
            quality_execution_lane = dict(item.get("quality_execution_lane") or {})
            if quality_execution_lane.get("summary"):
                lines.append(f"  质量执行线: {quality_execution_lane.get('summary')}")
            quality_review_loop_preview = _quality_review_loop_preview(item.get("quality_review_loop"))
            if quality_review_loop_preview:
                lines.append(f"  质量评审闭环: {quality_review_loop_preview}")
            restore_point = dict(autonomy_contract.get("restore_point") or {})
            if restore_point.get("summary"):
                lines.append(f"  恢复点: {restore_point.get('summary')}")
            if item.get("recommended_command"):
                lines.append(f"  处理命令: `{item.get('recommended_command')}`")
            operator_status_card = dict(item.get("operator_status_card") or {})
            handling_state_label = _operator_handling_state_label(operator_status_card)
            if handling_state_label:
                lines.append(f"  当前处理状态: {handling_state_label}")
            if operator_status_card.get("next_confirmation_signal"):
                lines.append(f"  下一确认信号: {operator_status_card.get('next_confirmation_signal')}")
    else:
        lines.append("- 当前没有新的 attention item。")
    lines.extend(["", "## User Loop", ""])
    for name, command in (payload.get("user_loop") or {}).items():
        lines.append(f"- `{name}`: `{command}`")
    lines.extend(["", "## Phase 2 User Loop", ""])
    lines.append(f"- 当前路径摘要: {phase2_user_product_loop.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase2_user_product_loop.get('recommended_command') or 'none'}`")
    for item in phase2_user_product_loop.get("operator_questions") or []:
        if not isinstance(item, Mapping):
            continue
        lines.append(f"- {item.get('question') or 'question'}: `{item.get('command') or 'none'}`")
    lines.extend(["", "## Commands", ""])
    for name, command in (payload.get("commands") or {}).items():
        lines.append(f"- `{name}`: `{command}`")
    lines.extend(["", "## Studies", ""])
    for item in payload.get("studies") or []:
        lines.extend(
            [
                f"### {item.get('study_id')}",
                "",
                f"- 浏览器入口: `{((item.get('monitoring') or {}).get('browser_url') or 'none')}`",
                f"- 当前运行批次: `{((item.get('monitoring') or {}).get('active_run_id') or 'none')}`",
            ]
        )
        _append_human_status_lines(lines, item)
        task_intake = dict(item.get("task_intake") or {})
        if task_intake:
            lines.append(f"- 当前任务意图: {task_intake.get('task_intent') or '未提供'}")
            lines.append(f"- 当前投稿目标: {task_intake.get('journal_target') or 'none'}")
        progress_freshness = dict(item.get("progress_freshness") or {})
        if progress_freshness.get("summary"):
            lines.append(f"- 进度信号: {progress_freshness.get('summary')}")
        intervention_lane = dict(item.get("intervention_lane") or {})
        if intervention_lane.get("title"):
            lines.append(f"- 当前介入通道: {intervention_lane.get('title')}")
        if intervention_lane.get("summary"):
            lines.append(f"- 当前介入摘要: {intervention_lane.get('summary')}")
        operator_verdict = dict(item.get("operator_verdict") or {})
        if operator_verdict.get("decision_mode"):
            lines.append(f"- 当前决策模式: {_operator_verdict_label(operator_verdict.get('decision_mode'))}")
        if operator_verdict.get("summary"):
            lines.append(f"- 当前处理摘要: {operator_verdict.get('summary')}")
        operator_status_card = dict(item.get("operator_status_card") or {})
        handling_state_label = _operator_handling_state_label(operator_status_card)
        if handling_state_label:
            lines.append(f"- 当前处理状态: {handling_state_label}")
        if operator_status_card.get("user_visible_verdict"):
            lines.append(f"- 当前处理结论: {operator_status_card.get('user_visible_verdict')}")
        if operator_status_card.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {operator_status_card.get('next_confirmation_signal')}")
        autonomy_contract = dict(item.get("autonomy_contract") or {})
        if autonomy_contract.get("summary"):
            lines.append(f"- 自治合同: {autonomy_contract.get('summary')}")
        quality_closure_truth = dict(item.get("quality_closure_truth") or {})
        if quality_closure_truth.get("summary"):
            lines.append(f"- 质量闭环: {quality_closure_truth.get('summary')}")
        quality_execution_lane = dict(item.get("quality_execution_lane") or {})
        if quality_execution_lane.get("summary"):
            lines.append(f"- 质量执行线: {quality_execution_lane.get('summary')}")
        quality_review_loop_preview = _quality_review_loop_preview(item.get("quality_review_loop"))
        if quality_review_loop_preview:
            lines.append(f"- 质量评审闭环: {quality_review_loop_preview}")
        restore_point = dict(autonomy_contract.get("restore_point") or {})
        if restore_point.get("summary"):
            lines.append(f"- 恢复点: {restore_point.get('summary')}")
        recovery_contract = dict(item.get("recovery_contract") or {})
        recovery_action_mode_label = _recovery_action_mode_label(recovery_contract)
        if recovery_action_mode_label:
            lines.append(f"- 恢复建议: {recovery_action_mode_label}")
        if item.get("recommended_command"):
            lines.append(f"- 推荐动作命令: `{item.get('recommended_command')}`")
        blockers = list(item.get("current_blockers") or [])
        lines.append(f"- 当前卡点: {', '.join(blockers) if blockers else '当前没有新的卡点。'}")
        lines.append(f"- 启动命令: `{((item.get('commands') or {}).get('launch') or '')}`")
        lines.append("")
    return "\n".join(lines)


def launch_study(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
    allow_stopped_relaunch: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    runtime_status = _serialize_runtime_status(
        study_runtime_router.ensure_study_runtime(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            entry_mode=entry_mode,
            allow_stopped_relaunch=allow_stopped_relaunch,
            force=force,
            source="product_entry",
        )
    )
    progress_payload = study_progress.read_study_progress(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=study_root,
        entry_mode=entry_mode,
    )
    resolved_study_id = _non_empty_text(progress_payload.get("study_id")) or _non_empty_text(runtime_status.get("study_id")) or study_id
    commands = {
        "progress": (
            f"{_command_prefix(profile_ref)} study-progress --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "status": (
            f"{_command_prefix(profile_ref)} study-runtime-status --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "cockpit": f"{_command_prefix(profile_ref)} workspace-cockpit --profile {_profile_arg(profile_ref)}",
        "supervisor_tick": (
            f"{_command_prefix(profile_ref)} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {_profile_arg(profile_ref)} --ensure-study-runtimes --apply"
        ),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "study_id": resolved_study_id,
        "runtime_status": runtime_status,
        "progress": progress_payload,
        "commands": commands,
    }


def render_launch_study_markdown(payload: dict[str, Any]) -> str:
    progress_payload = dict(payload.get("progress") or {})
    supervision = dict(progress_payload.get("supervision") or {})
    blockers = list(progress_payload.get("current_blockers") or [])
    task_intake = dict(progress_payload.get("task_intake") or {})
    progress_freshness = dict(progress_payload.get("progress_freshness") or {})
    recovery_contract = dict(progress_payload.get("recovery_contract") or {})
    recommended_commands = [
        dict(item)
        for item in (progress_payload.get("recommended_commands") or [])
        if isinstance(item, dict)
    ]
    lines = [
        "# Launch Study",
        "",
        f"- 当前 study: `{payload.get('study_id')}`",
        f"- 当前运行判断: {_runtime_decision_label((payload.get('runtime_status') or {}).get('decision'))}",
        f"- 浏览器入口: `{supervision.get('browser_url') or 'none'}`",
        f"- 当前运行批次: `{supervision.get('active_run_id') or 'none'}`",
    ]
    _append_human_status_lines(lines, progress_payload)
    if task_intake:
        lines.extend(
            [
                f"- 当前任务意图: {task_intake.get('task_intent') or '未提供'}",
                f"- 当前投稿目标: {task_intake.get('journal_target') or 'none'}",
            ]
        )
    if progress_freshness.get("summary"):
        lines.append(f"- 进度信号: {progress_freshness.get('summary')}")
    lines.extend(["", "## Blockers", ""])
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- 当前没有新的硬阻塞。")
    if recovery_contract:
        lines.extend(["", "## 恢复建议", ""])
        if recovery_contract.get("contract_kind"):
            lines.append(f"- 恢复合同类型: `{recovery_contract.get('contract_kind')}`")
        recovery_action_mode_label = _recovery_action_mode_label(recovery_contract)
        if recovery_action_mode_label:
            lines.append(f"- 当前恢复模式: {recovery_action_mode_label}")
        if recovery_contract.get("summary"):
            lines.append(f"- 当前恢复判断: {recovery_contract.get('summary')}")
        for item in recommended_commands:
            title = _non_empty_text(item.get("title")) or _non_empty_text(item.get("step_id")) or "unnamed"
            lines.append(f"- {title}: `{item.get('command') or 'none'}`")
    lines.extend(["", "## Commands", ""])
    for name, command in (payload.get("commands") or {}).items():
        lines.append(f"- `{name}`: `{command}`")
    lines.append("")
    return "\n".join(lines)


def build_product_entry_manifest(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    mainline_payload = mainline_status.read_mainline_status()
    mainline_snapshot = _mainline_snapshot()
    doctor_report = build_doctor_report(profile)
    product_entry_preflight = _build_product_entry_preflight(
        doctor_report=doctor_report,
        profile_ref=profile_ref,
    )
    domain_entry_contract = _build_domain_entry_contract()
    gateway_interaction_contract = _build_gateway_interaction_contract()
    _validate_domain_entry_contract_shape(
        domain_entry_contract,
        context="product_entry_manifest.domain_entry_contract",
    )
    _validate_gateway_interaction_contract_shape(
        gateway_interaction_contract,
        context="product_entry_manifest.gateway_interaction_contract",
    )
    profile_arg = _profile_arg(profile_ref)
    prefix = _command_prefix(profile_ref)
    workspace_root = str(profile.workspace_root)

    product_entry_shell = _build_shared_product_entry_shell_catalog({
        "product_frontdesk": {
            "command": f"{prefix} product-frontdesk --profile {profile_arg}",
            "purpose": "当前 research product frontdesk，先暴露当前 frontdoor、workspace inbox 与 shared handoff 入口。",
            "surface_kind": PRODUCT_FRONTDESK_KIND,
        },
        "workspace_cockpit": {
            "command": _json_surface_command(f"{prefix} workspace-cockpit --profile {profile_arg}"),
            "purpose": "当前 workspace 级用户 inbox，聚合 attention queue、监督在线态与研究入口回路。",
            "surface_kind": "workspace_cockpit",
        },
        "submit_study_task": {
            "command": (
                f"{prefix} submit-study-task --profile {profile_arg} "
                "--study-id <study_id> --task-intent '<task_intent>'"
            ),
            "purpose": "先把用户任务写成 durable study task intake，再启动研究执行。",
            "surface_kind": "study_task_intake",
        },
        "launch_study": {
            "command": f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>",
            "purpose": "创建或恢复 study runtime，并进入当前研究主线。",
            "surface_kind": "launch_study",
        },
        "study_progress": {
            "command": _json_surface_command(
                f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>"
            ),
            "purpose": "持续读取当前 study 的阶段摘要、阻塞、监督 freshness 与下一步。",
            "surface_kind": "study_progress",
        },
        "mainline_status": {
            "command": f"{prefix} mainline-status",
            "purpose": "查看 repo 理想形态、当前阶段、剩余缺口与下一步焦点。",
            "surface_kind": "mainline_status",
        },
        "mainline_phase": {
            "command": f"{prefix} mainline-phase --phase <current|next|phase_id>",
            "purpose": "查看某一阶段当前可用入口、退出条件与关键文档。",
            "surface_kind": "mainline_phase",
        },
    })
    shared_handoff = _build_shared_handoff(
        direct_entry_builder_command=(
            f"{prefix} build-product-entry --profile {profile_arg} "
            "--study-id <study_id> --entry-mode direct"
        ),
        opl_handoff_builder_command=(
            f"{prefix} build-product-entry --profile {profile_arg} "
            "--study-id <study_id> --entry-mode opl-handoff"
        ),
    )
    operator_loop_actions = _build_shared_operator_loop_action_catalog({
        "open_loop": {
            "command": product_entry_shell["workspace_cockpit"]["command"],
            "surface_kind": "workspace_cockpit",
            "summary": "先进入当前 workspace 级用户 inbox。",
            "requires": [],
        },
        "submit_task": {
            "command": product_entry_shell["submit_study_task"]["command"],
            "surface_kind": "study_task_intake",
            "summary": "先把新的研究任务写成 durable study task intake。",
            "requires": ["study_id", "task_intent"],
        },
        "continue_study": {
            "command": product_entry_shell["launch_study"]["command"],
            "surface_kind": "launch_study",
            "summary": "创建或恢复某个 study runtime，并回到当前研究主线。",
            "requires": ["study_id"],
        },
        "inspect_progress": {
            "command": product_entry_shell["study_progress"]["command"],
            "surface_kind": "study_progress",
            "summary": "读取某个 study 的当前阶段、阻塞和监督 freshness。",
            "requires": ["study_id"],
        },
    })
    family_orchestration = _build_shared_family_product_entry_orchestration(
        graph_id="mas_workspace_frontdoor_study_runtime_graph",
        target_domain_id=TARGET_DOMAIN_ID,
        graph_kind="study_runtime_orchestration",
        graph_version="2026-04-13",
        nodes=[
            {
                "node_id": "step:open_frontdesk",
                "node_kind": "operator_step",
                "title": "Open research frontdesk",
                "surface_kind": PRODUCT_FRONTDESK_KIND,
            },
            {
                "node_id": "step:submit_task",
                "node_kind": "operator_step",
                "title": "Write durable study task",
                "surface_kind": "study_task_intake",
                "produces_checkpoint": True,
            },
            {
                "node_id": "step:continue_study",
                "node_kind": "operator_step",
                "title": "Continue or relaunch a study",
                "surface_kind": "launch_study",
                "produces_checkpoint": True,
            },
            {
                "node_id": "step:inspect_progress",
                "node_kind": "operator_step",
                "title": "Inspect current study progress",
                "surface_kind": "study_progress",
                "produces_checkpoint": True,
            },
        ],
        edges=[
            {
                "from": "step:open_frontdesk",
                "to": "step:submit_task",
                "on": "new_task",
            },
            {
                "from": "step:open_frontdesk",
                "to": "step:continue_study",
                "on": "resume_study",
            },
            {
                "from": "step:open_frontdesk",
                "to": "step:inspect_progress",
                "on": "inspect_status",
            },
            {
                "from": "step:submit_task",
                "to": "step:continue_study",
                "on": "task_written",
            },
            {
                "from": "step:continue_study",
                "to": "step:inspect_progress",
                "on": "progress_refresh",
            },
        ],
        entry_nodes=["step:open_frontdesk"],
        exit_nodes=["step:continue_study", "step:inspect_progress"],
        human_gates=[
            {
                "gate_id": "study_physician_decision_gate",
                "trigger_nodes": ["step:continue_study"],
                "blocking": True,
            },
            {
                "gate_id": "publication_release_gate",
                "trigger_nodes": ["step:inspect_progress"],
                "blocking": True,
            },
        ],
        checkpoint_nodes=[
            "step:submit_task",
            "step:continue_study",
            "step:inspect_progress",
        ],
        human_gate_previews=[
            {
                "gate_id": "study_physician_decision_gate",
                "title": "Study physician decision gate",
            },
            {
                "gate_id": "publication_release_gate",
                "title": "Publication release gate",
            },
        ],
        resume_surface_kind="launch_study",
        session_locator_field="study_id",
        checkpoint_locator_field="controller_decision_path",
        action_graph_ref={
            "ref_kind": "json_pointer",
            "ref": "/family_orchestration/action_graph",
            "label": "mas family action graph",
        },
        event_envelope_surface={
            "ref_kind": "workspace_locator",
            "ref": "studies/<study_id>/artifacts/runtime_watch/latest.json",
            "label": "runtime watch event companion",
        },
        checkpoint_lineage_surface={
            "ref_kind": "workspace_locator",
            "ref": "studies/<study_id>/artifacts/controller_decisions/latest.json",
            "label": "controller checkpoint lineage companion",
        },
    )
    product_entry_guardrails = _build_product_entry_guardrails(
        profile=profile,
        profile_ref=profile_ref,
    )
    phase2_user_product_loop = _build_phase2_user_product_loop(
        profile=profile,
        profile_ref=profile_ref,
    )
    phase3_clearance_lane = _build_phase3_clearance_lane(
        profile=profile,
        profile_ref=profile_ref,
    )
    phase4_backend_deconstruction = _build_phase4_backend_deconstruction()
    phase5_platform_target = _build_phase5_platform_target()
    product_entry_quickstart = _build_shared_product_entry_quickstart(
        summary=(
            "先从 product frontdesk 进入当前 research frontdoor，"
            "需要新任务时先写 durable study task intake，再继续某个 study 或读取进度。"
        ),
        recommended_step_id="open_frontdesk",
        steps=[
            {
                "step_id": "open_frontdesk",
                "title": "启动 MAS 前台",
                "command": product_entry_shell["product_frontdesk"]["command"],
                "surface_kind": PRODUCT_FRONTDESK_KIND,
                "summary": product_entry_shell["product_frontdesk"]["purpose"],
                "requires": [],
            },
            {
                "step_id": "submit_task",
                "title": "给 study 下 durable 任务",
                "command": product_entry_shell["submit_study_task"]["command"],
                "surface_kind": "study_task_intake",
                "summary": operator_loop_actions["submit_task"]["summary"],
                "requires": list(operator_loop_actions["submit_task"]["requires"]),
            },
            {
                "step_id": "continue_study",
                "title": "启动或续跑 study",
                "command": product_entry_shell["launch_study"]["command"],
                "surface_kind": "launch_study",
                "summary": operator_loop_actions["continue_study"]["summary"],
                "requires": list(operator_loop_actions["continue_study"]["requires"]),
            },
            {
                "step_id": "inspect_progress",
                "title": "持续看研究进度",
                "command": product_entry_shell["study_progress"]["command"],
                "surface_kind": "study_progress",
                "summary": operator_loop_actions["inspect_progress"]["summary"],
                "requires": list(operator_loop_actions["inspect_progress"]["requires"]),
            },
        ],
        resume_contract=dict(family_orchestration["resume_contract"]),
        human_gate_ids=_collect_family_human_gate_ids(family_orchestration),
    )
    product_entry_start = _build_product_entry_start(
        product_entry_shell=product_entry_shell,
        operator_loop_actions=operator_loop_actions,
        family_orchestration=family_orchestration,
    )
    product_entry_overview = _build_shared_product_entry_overview(
        summary=(
            mainline_snapshot.get("current_stage_summary")
            or mainline_snapshot.get("current_program_phase_summary")
        ),
        frontdesk_command=product_entry_shell["product_frontdesk"]["command"],
        recommended_command=product_entry_shell["workspace_cockpit"]["command"],
        operator_loop_command=product_entry_shell["workspace_cockpit"]["command"],
        progress_surface={
            "surface_kind": "study_progress",
            "command": product_entry_shell["study_progress"]["command"],
            "step_id": "inspect_progress",
        },
        resume_surface=_build_shared_product_entry_resume_surface(
            command=product_entry_shell["launch_study"]["command"],
            resume_contract=family_orchestration["resume_contract"],
        ),
        recommended_step_id=product_entry_quickstart["recommended_step_id"],
        next_focus=list(mainline_snapshot.get("next_focus") or []),
        remaining_gaps_count=len(list(mainline_payload.get("remaining_gaps") or [])),
        human_gate_ids=list(product_entry_quickstart["human_gate_ids"]),
    )
    product_entry_readiness = _build_shared_product_entry_readiness(
        verdict="runtime_ready_not_standalone_product",
        usable_now=True,
        good_to_use_now=False,
        fully_automatic=False,
        summary=(
            "当前可以作为 research frontdesk / CLI 主线使用，并通过稳定的 runtime 回路持续推进研究；"
            "但还不是成熟的独立医学产品前台。"
        ),
        recommended_start_surface=PRODUCT_FRONTDESK_KIND,
        recommended_start_command=product_entry_shell["product_frontdesk"]["command"],
        recommended_loop_surface="workspace_cockpit",
        recommended_loop_command=product_entry_shell["workspace_cockpit"]["command"],
        blocking_gaps=[
            "独立医学前台 / hosted product entry 仍未 landed。",
            "更多 workspace / host 的真实 clearance 与 study-local blocker 收口仍在继续。",
        ],
    )
    managed_runtime_contract = _build_managed_runtime_contract(
        domain_owner=TARGET_DOMAIN_ID,
        executor_owner="med_deepscientist",
        supervision_status_surface="study_progress",
        attention_queue_surface="workspace_cockpit",
        recovery_contract_surface="study_runtime_status",
    )
    runtime = {
        "runtime_owner": "upstream_hermes_agent",
        "domain_owner": TARGET_DOMAIN_ID,
        "executor_owner": "med_deepscientist",
        "runtime_substrate": "external_hermes_agent_target",
        "managed_runtime_backend_id": profile.managed_runtime_backend_id,
        "runtime_root": str(profile.runtime_root),
        "hermes_home_root": str(profile.hermes_home_root),
    }
    frontdesk_surface = _build_shared_product_entry_shell_linked_surface(
        shell_key="product_frontdesk",
        shell_surface=product_entry_shell["product_frontdesk"],
        summary=product_entry_shell["product_frontdesk"]["purpose"],
    )
    operator_loop_surface = _build_shared_product_entry_shell_linked_surface(
        shell_key="workspace_cockpit",
        shell_surface=product_entry_shell["workspace_cockpit"],
        summary=product_entry_shell["workspace_cockpit"]["purpose"],
    )
    repo_mainline = {
        "program_id": mainline_snapshot.get("program_id"),
        "current_stage_id": mainline_snapshot.get("current_stage_id"),
        "current_stage_status": mainline_snapshot.get("current_stage_status"),
        "current_stage_summary": mainline_snapshot.get("current_stage_summary"),
        "current_program_phase_id": mainline_snapshot.get("current_program_phase_id"),
        "current_program_phase_status": mainline_snapshot.get("current_program_phase_status"),
        "current_program_phase_summary": mainline_snapshot.get("current_program_phase_summary"),
        "next_focus": list(mainline_snapshot.get("next_focus") or []),
    }
    single_project_boundary = dict(mainline_snapshot.get("single_project_boundary") or {})
    product_entry_status = {
        "summary": mainline_snapshot.get("current_stage_summary")
        or mainline_snapshot.get("current_program_phase_summary"),
        "next_focus": list(mainline_snapshot.get("next_focus") or []),
        "remaining_gaps_count": len(list(mainline_payload.get("remaining_gaps") or [])),
    }
    runtime_inventory = _build_runtime_inventory_surface(
        profile=profile,
        runtime=runtime,
        managed_runtime_contract=managed_runtime_contract,
        product_entry_preflight=product_entry_preflight,
        operator_loop_surface=operator_loop_surface,
    )
    task_lifecycle = _build_task_lifecycle_surface(
        repo_mainline=repo_mainline,
        product_entry_status=product_entry_status,
        product_entry_readiness=product_entry_readiness,
        family_orchestration=family_orchestration,
        operator_loop_surface=operator_loop_surface,
        product_entry_shell=product_entry_shell,
    )
    skill_catalog = _build_skill_catalog_surface(
        product_entry_status=product_entry_status,
        domain_entry_contract=domain_entry_contract,
        product_entry_shell=product_entry_shell,
    )
    automation = _build_automation_surface(
        profile=profile,
        profile_ref=profile_ref,
        product_entry_status=product_entry_status,
    )

    payload = _build_shared_family_product_entry_manifest(
        manifest_kind=PRODUCT_ENTRY_MANIFEST_KIND,
        target_domain_id=TARGET_DOMAIN_ID,
        formal_entry={
            "default": "CLI",
            "supported_protocols": ["MCP"],
            "internal_surface": "controller",
        },
        workspace_locator={
            "workspace_surface_kind": "med_autoscience_workspace_profile",
            "profile_name": profile.name,
            "workspace_root": workspace_root,
            "profile_ref": str(Path(profile_ref).expanduser().resolve()) if profile_ref is not None else None,
        },
        runtime=runtime,
        managed_runtime_contract=managed_runtime_contract,
        repo_mainline=repo_mainline,
        product_entry_status=product_entry_status,
        frontdesk_surface=frontdesk_surface,
        operator_loop_surface=operator_loop_surface,
        operator_loop_actions=operator_loop_actions,
        recommended_shell="workspace_cockpit",
        recommended_command=product_entry_shell["workspace_cockpit"]["command"],
        product_entry_shell=product_entry_shell,
        shared_handoff=shared_handoff,
        runtime_inventory=runtime_inventory,
        task_lifecycle=task_lifecycle,
        skill_catalog=skill_catalog,
        automation=automation,
        product_entry_start=product_entry_start,
        product_entry_overview=product_entry_overview,
        product_entry_preflight=product_entry_preflight,
        product_entry_readiness=product_entry_readiness,
        product_entry_quickstart=product_entry_quickstart,
        family_orchestration=family_orchestration,
        remaining_gaps=list(mainline_payload.get("remaining_gaps") or []),
        schema_ref=PRODUCT_ENTRY_MANIFEST_SCHEMA_REF,
        domain_entry_contract=domain_entry_contract,
        gateway_interaction_contract=gateway_interaction_contract,
        notes=[
            "This manifest freezes the current MAS repo-tracked research product-entry shell only.",
            "It does not include the display / paper-figure asset line.",
            "It does not claim that a mature standalone medical frontend is already landed.",
        ],
        extra_payload={
            "schema_version": SCHEMA_VERSION,
            "single_project_boundary": single_project_boundary,
            "executor_defaults": {
                "default_executor_name": "codex_cli",
                "default_executor_mode": "autonomous",
                "default_model": "inherit_local_codex_default",
                "default_reasoning_effort": "inherit_local_codex_default",
                "executor_labels": {
                    "codex_cli": "Codex CLI",
                    "hermes_agent": "Hermes-Agent",
                },
                "executor_statuses": {
                    "codex_cli": "default",
                    "hermes_agent": "experimental",
                },
                "chat_completion_only_executor_forbidden": True,
                "hermes_agent_requires_full_agent_loop": True,
                "current_backend_chain": [
                    "med_autoscience.runtime_transport.hermes -> med_autoscience.runtime_transport.med_deepscientist",
                    "med_deepscientist CodexRunner -> codex exec autonomous agent loop",
                ],
                "optional_executor_proofs": [
                    {
                        "executor_kind": "hermes_native_proof",
                        "entrypoint": "MedDeepScientist HermesNativeProofRunner -> run_agent.AIAgent.run_conversation",
                        "requires_full_agent_loop": True,
                        "default_model": "inherit_local_hermes_default",
                        "default_reasoning_effort": "inherit_local_hermes_default",
                    }
                ],
            },
            "phase2_user_product_loop": phase2_user_product_loop,
            "product_entry_guardrails": product_entry_guardrails,
            "phase3_clearance_lane": phase3_clearance_lane,
            "phase4_backend_deconstruction": phase4_backend_deconstruction,
            "phase5_platform_target": phase5_platform_target,
        },
    )
    _validate_product_entry_manifest_contract(payload)
    return payload


def render_product_entry_manifest_markdown(payload: dict[str, Any]) -> str:
    workspace_locator = dict(payload.get("workspace_locator") or {})
    repo_mainline = dict(payload.get("repo_mainline") or {})
    product_entry_shell = dict(payload.get("product_entry_shell") or {})
    shared_handoff = dict(payload.get("shared_handoff") or {})
    gateway_interaction_contract = dict(payload.get("gateway_interaction_contract") or {})
    phase2_user_product_loop = dict(payload.get("phase2_user_product_loop") or {})
    product_entry_guardrails = dict(payload.get("product_entry_guardrails") or {})
    phase3_clearance_lane = dict(payload.get("phase3_clearance_lane") or {})
    phase4_backend_deconstruction = dict(payload.get("phase4_backend_deconstruction") or {})
    phase5_platform_target = dict(payload.get("phase5_platform_target") or {})
    single_project_boundary = dict(payload.get("single_project_boundary") or {})
    lines = [
        "# Product Entry Manifest",
        "",
        f"- manifest 类型: `{payload.get('manifest_kind')}`",
        f"- schema 引用: `{payload.get('schema_ref')}`",
        f"- 目标域: `{payload.get('target_domain_id')}`",
        f"- profile 名称: `{workspace_locator.get('profile_name')}`",
        f"- workspace 根目录: `{workspace_locator.get('workspace_root')}`",
        f"- 当前 program phase: `{repo_mainline.get('current_program_phase_id')}`",
        f"- 当前主线阶段: `{repo_mainline.get('current_stage_id')}`",
        f"- 程序摘要: {repo_mainline.get('summary') or 'none'}",
        f"- 前台入口归属: `{gateway_interaction_contract.get('frontdoor_owner') or 'none'}`",
        f"- 交互模式: {_user_interaction_mode_label(gateway_interaction_contract.get('user_interaction_mode'))}",
        "",
        "## Product Entry Shell",
        "",
    ]
    for name, item in product_entry_shell.items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command')}`")
    lines.extend([""] + _render_single_project_boundary_markdown_lines(single_project_boundary) + [""])
    lines.extend(["", "## Operator Loop Actions", ""])
    for name, item in (payload.get("operator_loop_actions") or {}).items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command')}`")
    lines.extend(["", "## Shared Handoff", ""])
    for name, item in shared_handoff.items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command')}`")
    lines.extend(["", "## Phase 2 User Loop", ""])
    lines.append(f"- program phase 摘要: {phase2_user_product_loop.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase2_user_product_loop.get('recommended_command') or 'none'}`")
    for item in phase2_user_product_loop.get("single_path") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 单一路径 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend(["", "## Guardrails", ""])
    lines.append(f"- 当前摘要: {product_entry_guardrails.get('summary') or 'none'}")
    for item in product_entry_guardrails.get("guardrail_classes") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('guardrail_id')}`: `{item.get('recommended_command') or 'none'}`"
        )
    lines.extend(["", "## Phase 3 Clearance", ""])
    lines.append(f"- 清障重点: {phase3_clearance_lane.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase3_clearance_lane.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase3_clearance_lane.get('recommended_command') or 'none'}`")
    for item in phase3_clearance_lane.get("clearance_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('target_id')}`: `{((item.get('commands') or ['none'])[0])}`")
    for item in phase3_clearance_lane.get("clearance_loop") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 清障步骤 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend(["", "## Phase 4 Deconstruction", ""])
    for item in phase4_backend_deconstruction.get("substrate_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('capability_id')}`: {item.get('summary') or 'none'}")
    lines.extend([""])
    lines.extend(_render_phase5_platform_target_markdown_lines(phase5_platform_target))
    lines.extend(["", "## Remaining Gaps", ""])
    remaining_gaps = list(payload.get("remaining_gaps") or [])
    if remaining_gaps:
        lines.extend(f"- {item}" for item in remaining_gaps)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def build_product_frontdesk(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    manifest = build_product_entry_manifest(
        profile=profile,
        profile_ref=profile_ref,
    )
    workspace_cockpit = read_workspace_cockpit(
        profile=profile,
        profile_ref=profile_ref,
    )
    product_entry_shell = dict(manifest.get("product_entry_shell") or {})
    shared_handoff = dict(manifest.get("shared_handoff") or {})
    product_entry_preflight = dict(manifest.get("product_entry_preflight") or {})
    product_entry_quickstart = dict(manifest.get("product_entry_quickstart") or {})
    workspace_operator_brief = dict(workspace_cockpit.get("operator_brief") or {})
    workspace_attention_queue = list(workspace_cockpit.get("attention_queue") or [])
    top_attention = dict(workspace_attention_queue[0] or {}) if workspace_attention_queue else {}
    top_attention_status_card = dict(top_attention.get("operator_status_card") or {})
    single_project_boundary = _validate_single_project_boundary(
        _single_project_boundary_payload(manifest.get("single_project_boundary")),
        context="product_frontdesk.source.single_project_boundary",
    )
    if not bool(product_entry_preflight.get("ready_to_try_now")):
        operator_brief = {
            "surface_kind": "product_frontdesk_operator_brief",
            "verdict": "preflight_blocked",
            "summary": _non_empty_text(product_entry_preflight.get("summary"))
            or "当前还没有通过前置检查，先不要直接进入研究主线。",
            "should_intervene_now": True,
            "focus_scope": "workspace",
            "focus_study_id": None,
            "recommended_step_id": "preflight_check",
            "recommended_command": _non_empty_text(product_entry_preflight.get("recommended_check_command")),
        }
    elif _non_empty_text(workspace_operator_brief.get("verdict")) == "attention_required":
        operator_brief = {
            "surface_kind": "product_frontdesk_operator_brief",
            "verdict": "attention_required",
            "summary": _operator_status_summary(top_attention_status_card)
            or _non_empty_text(workspace_operator_brief.get("summary"))
            or "当前 workspace 已有需要优先处理的 attention item。",
            "should_intervene_now": True,
            "focus_scope": _non_empty_text(workspace_operator_brief.get("focus_scope")) or "workspace",
            "focus_study_id": _non_empty_text(workspace_operator_brief.get("focus_study_id")),
            "recommended_step_id": _non_empty_text(top_attention.get("recommended_step_id"))
            or _non_empty_text(workspace_operator_brief.get("recommended_step_id"))
            or "open_workspace_cockpit",
            "recommended_command": _non_empty_text(top_attention.get("recommended_command"))
            or _non_empty_text(workspace_operator_brief.get("recommended_command"))
            or _non_empty_text((manifest.get("summary") or {}).get("recommended_command")),
        }
        current_focus = _non_empty_text(top_attention_status_card.get("current_focus")) or _non_empty_text(
            workspace_operator_brief.get("current_focus")
        ) or _quality_execution_focus(top_attention)
        if current_focus is not None:
            operator_brief["current_focus"] = current_focus
        next_confirmation_signal = _non_empty_text(top_attention_status_card.get("next_confirmation_signal")) or _non_empty_text(
            workspace_operator_brief.get("next_confirmation_signal")
        )
        if next_confirmation_signal is not None:
            operator_brief["next_confirmation_signal"] = next_confirmation_signal
    elif _non_empty_text(workspace_operator_brief.get("verdict")) == "ready_for_task":
        operator_brief = {
            "surface_kind": "product_frontdesk_operator_brief",
            "verdict": "ready_for_task",
            "summary": "当前 workspace 已 ready，下一步先给目标 study 下任务，再启动研究。",
            "should_intervene_now": False,
            "focus_scope": "workspace",
            "focus_study_id": None,
            "recommended_step_id": "submit_task",
            "recommended_command": _non_empty_text(workspace_operator_brief.get("recommended_command"))
            or _non_empty_text(
                ((product_entry_quickstart.get("steps") or [None, {}])[1] or {}).get("command")
            ),
        }
    else:
        operator_brief = {
            "surface_kind": "product_frontdesk_operator_brief",
            "verdict": "monitor_only",
            "summary": _non_empty_text(workspace_operator_brief.get("summary"))
            or "当前先进入 workspace cockpit，持续看进度、告警和恢复建议。",
            "should_intervene_now": bool(workspace_operator_brief.get("should_intervene_now")),
            "focus_scope": _non_empty_text(workspace_operator_brief.get("focus_scope")) or "workspace",
            "focus_study_id": _non_empty_text(workspace_operator_brief.get("focus_study_id")),
            "recommended_step_id": "open_workspace_cockpit",
            "recommended_command": _non_empty_text((manifest.get("summary") or {}).get("recommended_command")),
        }

    payload = _build_shared_family_product_frontdesk_from_manifest(
        recommended_action="inspect_or_prepare_research_loop",
        product_entry_manifest=manifest,
        shell_aliases={
            "frontdesk": "product_frontdesk",
            "cockpit": "workspace_cockpit",
            "submit_task": "submit_study_task",
            "launch_study": "launch_study",
            "study_progress": "study_progress",
            "mainline_status": "mainline_status",
            "mainline_phase": "mainline_phase",
        },
        schema_ref=PRODUCT_FRONTDESK_SCHEMA_REF,
        notes=[
            "This frontdesk surface is a controller-owned front door over the current research product-entry shell.",
            "It does not claim that a mature standalone medical frontend is already landed.",
            "It does not include the display / paper-figure asset line.",
        ],
        extra_payload={
            "schema_version": SCHEMA_VERSION,
            "single_project_boundary": single_project_boundary,
            "executor_defaults": dict(manifest.get("executor_defaults") or {}),
            "runtime_inventory": dict(manifest.get("runtime_inventory") or {}),
            "task_lifecycle": dict(manifest.get("task_lifecycle") or {}),
            "skill_catalog": dict(manifest.get("skill_catalog") or {}),
            "automation": dict(manifest.get("automation") or {}),
            "phase2_user_product_loop": dict(manifest.get("phase2_user_product_loop") or {}),
            "product_entry_guardrails": dict(manifest.get("product_entry_guardrails") or {}),
            "phase3_clearance_lane": dict(manifest.get("phase3_clearance_lane") or {}),
            "phase4_backend_deconstruction": dict(manifest.get("phase4_backend_deconstruction") or {}),
            "operator_brief": operator_brief,
            "workspace_operator_brief": workspace_operator_brief,
            "workspace_attention_queue_preview": list((workspace_cockpit.get("attention_queue") or []))[:3],
            "phase5_platform_target": dict(manifest.get("phase5_platform_target") or {}),
        },
    )
    _validate_product_frontdesk_contract(payload)
    return payload


def render_product_frontdesk_markdown(payload: dict[str, Any]) -> str:
    entry_surfaces = dict(payload.get("entry_surfaces") or {})
    gateway_interaction_contract = dict(payload.get("gateway_interaction_contract") or {})
    phase2_user_product_loop = dict(payload.get("phase2_user_product_loop") or {})
    product_entry_guardrails = dict(payload.get("product_entry_guardrails") or {})
    phase3_clearance_lane = dict(payload.get("phase3_clearance_lane") or {})
    phase4_backend_deconstruction = dict(payload.get("phase4_backend_deconstruction") or {})
    phase5_platform_target = dict(payload.get("phase5_platform_target") or {})
    single_project_boundary = dict(payload.get("single_project_boundary") or {})
    operator_brief = dict(payload.get("operator_brief") or {})
    quickstart = dict(payload.get("product_entry_quickstart") or {})
    workspace_operator_brief = dict(payload.get("workspace_operator_brief") or {})
    lines = [
        "# Product Frontdesk",
        "",
        f"- 目标域: `{payload.get('target_domain_id')}`",
        f"- 契约引用: `{payload.get('schema_ref') or 'none'}`",
        f"- 前台归属: `{gateway_interaction_contract.get('frontdoor_owner') or 'none'}`",
        f"- 交互模式: `{gateway_interaction_contract.get('user_interaction_mode') or 'none'}`",
        f"- 前台入口命令: `{(payload.get('summary') or {}).get('frontdesk_command') or 'none'}`",
        f"- 推荐继续命令: `{(payload.get('summary') or {}).get('recommended_command') or 'none'}`",
        f"- 当前 loop 命令: `{(payload.get('summary') or {}).get('operator_loop_command') or 'none'}`",
        "",
        "## Now",
        "",
    ]
    if operator_brief:
        lines.append(f"- 当前状态: {_operator_verdict_label(operator_brief.get('verdict'))}")
        lines.append(f"- 当前判断: {operator_brief.get('summary') or 'none'}")
        lines.append(f"- 是否需要立刻介入: {'是' if operator_brief.get('should_intervene_now') else '否'}")
        lines.append(f"- 推荐动作: `{operator_brief.get('recommended_step_id') or 'none'}`")
        lines.append(f"- 推荐命令: `{operator_brief.get('recommended_command') or 'none'}`")
        if operator_brief.get("focus_study_id"):
            lines.append(f"- 聚焦 study: `{operator_brief.get('focus_study_id')}`")
        if operator_brief.get("current_focus"):
            lines.append(f"- 当前清障重点: {operator_brief.get('current_focus')}")
        if operator_brief.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {operator_brief.get('next_confirmation_signal')}")
    else:
        lines.append("- 当前还没有 frontdesk operator brief。")
    lines.extend([""] + _render_single_project_boundary_markdown_lines(single_project_boundary) + [""])
    lines.extend([
        "",
        "## Single Path",
        "",
    ])
    for step in quickstart.get("steps") or []:
        if not isinstance(step, dict):
            continue
        lines.append(
            f"- `{step.get('step_id')}`: `{step.get('command') or 'none'}` {step.get('summary') or ''}"
        )
    lines.extend([
        "",
        "## Product Entry Overview",
        "",
        f"- 总览判断: `{(payload.get('product_entry_overview') or {}).get('summary') or 'none'}`",
        f"- 启动提示: `{(payload.get('product_entry_start') or {}).get('summary') or 'none'}`",
        f"- 启动后恢复命令: `{((payload.get('product_entry_start') or {}).get('resume_surface') or {}).get('command') or 'none'}`",
        f"- 前置检查已通过: `{'是' if (payload.get('product_entry_preflight') or {}).get('ready_to_try_now') else '否'}`",
        f"- 前置检查命令: `{(payload.get('product_entry_preflight') or {}).get('recommended_check_command') or 'none'}`",
        f"- 查看进度命令: `{((payload.get('product_entry_overview') or {}).get('progress_surface') or {}).get('command') or 'none'}`",
        f"- 恢复当前 loop 命令: `{((payload.get('product_entry_overview') or {}).get('resume_surface') or {}).get('command') or 'none'}`",
        "",
        "## Workspace Preview",
        "",
    ])
    if workspace_operator_brief:
        lines.append(
            f"- 当前 workspace 状态: {_operator_verdict_label(workspace_operator_brief.get('verdict'))}"
        )
        lines.append(f"- 当前 workspace 判断: {workspace_operator_brief.get('summary') or 'none'}")
        lines.append(
            f"- 当前 workspace 推荐命令: `{workspace_operator_brief.get('recommended_command') or 'none'}`"
        )
    else:
        lines.append("- 当前没有 workspace preview。")
    for item in payload.get("workspace_attention_queue_preview") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 当前关注项: {item.get('title') or '未命名关注项'}")
        lines.append(f"- 处理命令: `{item.get('recommended_command') or 'none'}`")
        autonomy_contract = dict(item.get("autonomy_contract") or {})
        if autonomy_contract.get("summary"):
            lines.append(f"- 自治合同: {autonomy_contract.get('summary')}")
        quality_closure_truth = dict(item.get("quality_closure_truth") or {})
        if quality_closure_truth.get("summary"):
            lines.append(f"- 质量闭环: {quality_closure_truth.get('summary')}")
        quality_execution_lane = dict(item.get("quality_execution_lane") or {})
        if quality_execution_lane.get("summary"):
            lines.append(f"- 质量执行线: {quality_execution_lane.get('summary')}")
        quality_review_loop_preview = _quality_review_loop_preview(item.get("quality_review_loop"))
        if quality_review_loop_preview:
            lines.append(f"- 质量评审闭环: {quality_review_loop_preview}")
        restore_point = dict(autonomy_contract.get("restore_point") or {})
        if restore_point.get("summary"):
            lines.append(f"- 恢复点: {restore_point.get('summary')}")
        operator_status_card = dict(item.get("operator_status_card") or {})
        if operator_status_card.get("handling_state"):
            lines.append(f"- 处理状态: `{operator_status_card.get('handling_state')}`")
        if operator_status_card.get("user_visible_verdict"):
            lines.append(f"- 当前处理结论: {operator_status_card.get('user_visible_verdict')}")
        if operator_status_card.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {operator_status_card.get('next_confirmation_signal')}")
    lines.extend([
        "",
        "## Phase 2 User Loop",
        "",
    ])
    lines.append(f"- program phase 摘要: {phase2_user_product_loop.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase2_user_product_loop.get('recommended_command') or 'none'}`")
    for item in phase2_user_product_loop.get("single_path") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 单一路径 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend([
        "",
        "## Guardrails",
        "",
    ])
    guardrail_classes = list(product_entry_guardrails.get("guardrail_classes") or [])
    if not guardrail_classes:
        lines.append("- `workspace_supervision_gap`: `none`")
    for item in guardrail_classes:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('guardrail_id')}`: `{item.get('recommended_command') or 'none'}`"
        )
    lines.extend(
        [
            "",
            "## Phase 3 Clearance",
            "",
        ]
    )
    lines.append(f"- 清障重点: {phase3_clearance_lane.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase3_clearance_lane.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase3_clearance_lane.get('recommended_command') or 'none'}`")
    clearance_targets = list(phase3_clearance_lane.get("clearance_targets") or [])
    if not clearance_targets:
        lines.append("- `external_runtime_contract`: `none`")
    for item in clearance_targets:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('target_id')}`: `{((item.get('commands') or ['none'])[0])}`")
    clearance_loop = list(phase3_clearance_lane.get("clearance_loop") or [])
    if not clearance_loop:
        lines.append("- 清障步骤 `refresh_supervision`: `none`")
    for item in clearance_loop:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 清障步骤 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend(
        [
            "",
            "## Phase 4 Deconstruction",
            "",
        ]
    )
    substrate_targets = list(phase4_backend_deconstruction.get("substrate_targets") or [])
    if not substrate_targets:
        lines.append("- `session_run_watch_recovery`: none")
    for item in substrate_targets:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('capability_id')}`: {item.get('summary') or 'none'}")
    lines.extend([""])
    lines.extend(_render_phase5_platform_target_markdown_lines(phase5_platform_target))
    lines.extend(["", "## Entry Surfaces", ""])
    for name, item in entry_surfaces.items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command') or 'none'}`")
    lines.append("")
    return "\n".join(lines)


def build_product_entry_preflight(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    doctor_report = build_doctor_report(profile)
    return _build_product_entry_preflight(
        doctor_report=doctor_report,
        profile_ref=profile_ref,
    )


def build_product_entry_start(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    manifest = build_product_entry_manifest(
        profile=profile,
        profile_ref=profile_ref,
    )
    return dict(manifest.get("product_entry_start") or {})


def render_product_entry_preflight_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Product Entry Preflight",
        "",
        f"- 当前可直接尝试: {_bool_label(payload.get('ready_to_try_now'))}",
        f"- 当前摘要: {payload.get('summary') or 'none'}",
        f"- 前置检查命令: `{payload.get('recommended_check_command') or 'none'}`",
        f"- 推荐启动命令: `{payload.get('recommended_start_command') or 'none'}`",
        "",
        "## Checks",
        "",
    ]
    checks = list(payload.get("checks") or [])
    if checks:
        for check in checks:
            if not isinstance(check, dict):
                continue
            lines.append(
                "- "
                + f"`{check.get('check_id')}` "
                + f"[{_check_status_label(check.get('status'))}] "
                + f"({'阻塞项' if check.get('blocking') else '非阻塞项'}) "
                + f"{check.get('summary') or ''} "
                + f"`{check.get('command') or 'none'}`"
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def render_product_entry_start_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Product Entry Start",
        "",
        f"- 当前摘要: {payload.get('summary') or 'none'}",
        f"- 建议入口: {_start_mode_label(payload.get('recommended_mode_id'))}",
        f"- 恢复入口: {_surface_kind_label(((payload.get('resume_surface') or {}).get('surface_kind')))}",
        "",
        "## 可用入口",
        "",
    ]
    modes = list(payload.get("modes") or [])
    if modes:
        for mode in modes:
            if not isinstance(mode, dict):
                continue
            lines.append(
                "- "
                + f"{_start_mode_label(mode.get('mode_id'))}: "
                + f"`{mode.get('command') or 'none'}` "
                + f"{mode.get('summary') or ''}"
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def build_product_entry(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    direct_entry_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    selected_direct_entry_mode = _require_direct_entry_mode(direct_entry_mode)
    execution = _execution_payload(study_payload, profile=profile)
    latest_task_payload = read_latest_task_intake(study_root=resolved_study_root)
    if latest_task_payload is None:
        raise ValueError("build-product-entry 需要已有 durable study task intake；请先运行 submit-study-task。")

    task_intent = _non_empty_text(latest_task_payload.get("task_intent"))
    if task_intent is None:
        raise ValueError("latest durable study task intake 缺少 task_intent。")

    managed_entry_mode = (
        _non_empty_text(latest_task_payload.get("entry_mode"))
        or _non_empty_text(execution.get("default_entry_mode"))
        or "full_research"
    )
    runtime_contract = dict(latest_task_payload.get("runtime_session_contract") or {})
    return_contract = dict(latest_task_payload.get("return_surface_contract") or {})
    commands = {
        "workspace_cockpit": f"{_command_prefix(profile_ref)} workspace-cockpit --profile {_profile_arg(profile_ref)}",
        "submit_study_task": (
            f"{_command_prefix(profile_ref)} submit-study-task --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)} --task-intent '<task_intent>'"
        ),
        "launch_study": (
            f"{_command_prefix(profile_ref)} launch-study --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "study_progress": (
            f"{_command_prefix(profile_ref)} study-progress --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "study_runtime_status": (
            f"{_command_prefix(profile_ref)} study-runtime-status --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
    }
    commands["workspace_cockpit"] = _json_surface_command(commands["workspace_cockpit"])
    commands["study_progress"] = _json_surface_command(commands["study_progress"])

    payload = {
        "schema_version": SCHEMA_VERSION,
        "entry_kind": PRODUCT_ENTRY_KIND,
        "target_domain_id": TARGET_DOMAIN_ID,
        "task_intent": task_intent,
        "entry_mode": selected_direct_entry_mode,
        "workspace_locator": {
            "workspace_surface_kind": "med_autoscience_study_workspace",
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "study_id": resolved_study_id,
            "study_root": str(resolved_study_root),
        },
        "runtime_session_contract": {
            "runtime_owner": "upstream_hermes_agent",
            "domain_owner": TARGET_DOMAIN_ID,
            "executor_owner": "med_deepscientist",
            "runtime_substrate": "external_hermes_agent_target",
            "managed_entry_mode": managed_entry_mode,
            "managed_runtime_backend_id": runtime_contract.get("managed_runtime_backend_id") or profile.managed_runtime_backend_id,
            "runtime_root": runtime_contract.get("runtime_root") or str(profile.runtime_root),
            "hermes_agent_repo_root": runtime_contract.get("hermes_agent_repo_root"),
            "hermes_home_root": runtime_contract.get("hermes_home_root") or str(profile.hermes_home_root),
            "start_entry": "launch-study",
            "resume_entry": "launch-study",
        },
        "managed_runtime_contract": _build_managed_runtime_contract(
            domain_owner=TARGET_DOMAIN_ID,
            executor_owner="med_deepscientist",
            supervision_status_surface="study_progress",
            attention_queue_surface="workspace_cockpit",
            recovery_contract_surface="study_runtime_status",
        ),
        "return_surface_contract": {
            "entry_adapter": SERVICE_SAFE_ENTRY_ADAPTER,
            "default_formal_entry": "CLI",
            "supported_entry_modes": list(SUPPORTED_DIRECT_ENTRY_MODES),
            "domain_entry_contract": _build_domain_entry_contract(),
            "gateway_interaction_contract": _build_gateway_interaction_contract(),
            "cockpit_command": commands["workspace_cockpit"],
            "submit_task_command": commands["submit_study_task"],
            "launch_command": commands["launch_study"],
            "progress_command": commands["study_progress"],
            "runtime_status_command": commands["study_runtime_status"],
            "runtime_supervision_path": return_contract.get("runtime_supervision_path"),
            "publication_eval_path": return_contract.get("publication_eval_path"),
            "controller_decision_path": return_contract.get("controller_decision_path"),
        },
        "domain_payload": {
            "study_id": resolved_study_id,
            "journal_target": latest_task_payload.get("journal_target"),
            "evidence_boundary": list(latest_task_payload.get("evidence_boundary") or []),
            "trusted_inputs": list(latest_task_payload.get("trusted_inputs") or []),
            "reference_papers": list(latest_task_payload.get("reference_papers") or []),
            "first_cycle_outputs": list(latest_task_payload.get("first_cycle_outputs") or []),
        },
        "source_task_intake": {
            "task_id": latest_task_payload.get("task_id"),
            "emitted_at": latest_task_payload.get("emitted_at"),
        },
        "commands": commands,
    }
    _validate_domain_entry_contract_shape(
        payload["return_surface_contract"]["domain_entry_contract"],
        context="build_product_entry.return_surface_contract.domain_entry_contract",
    )
    _validate_gateway_interaction_contract_shape(
        payload["return_surface_contract"]["gateway_interaction_contract"],
        context="build_product_entry.return_surface_contract.gateway_interaction_contract",
    )
    return payload


def render_build_product_entry_markdown(payload: dict[str, Any]) -> str:
    commands = dict(payload.get("commands") or {})
    return_surface_contract = dict(payload.get("return_surface_contract") or {})
    domain_payload = dict(payload.get("domain_payload") or {})
    lines = [
        "# Build Product Entry",
        "",
        f"- 目标域: `{payload.get('target_domain_id')}`",
        f"- 当前入口模式: {_direct_entry_mode_label(payload.get('entry_mode'))}",
        f"- 当前任务意图: {payload.get('task_intent')}",
        f"- 当前 study: `{domain_payload.get('study_id') or 'unknown'}`",
        f"- 当前投稿目标: {domain_payload.get('journal_target') or 'none'}",
        "",
        "## Commands",
        "",
    ]
    for name, command in commands.items():
        lines.append(f"- `{name}`: `{command}`")
    lines.extend(
        [
            "",
            "## Return Surface",
            "",
            f"- 运行监管路径: `{return_surface_contract.get('runtime_supervision_path') or 'none'}`",
            f"- 发表评估路径: `{return_surface_contract.get('publication_eval_path') or 'none'}`",
            f"- 控制器决策路径: `{return_surface_contract.get('controller_decision_path') or 'none'}`",
            "",
        ]
    )
    return "\n".join(lines)


def _build_live_task_intake_runtime_message(payload: dict[str, Any]) -> str:
    return (
        "MAS managed task update. Prioritize this latest study task over stale background plans.\n\n"
        f"{render_task_intake_runtime_context(payload)}\n\n"
        "After absorbing this task, report the concrete next action through artifact.interact(...)."
    )


def _runtime_message_id(payload: Mapping[str, Any] | None) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    nested_message = payload.get("message")
    if isinstance(nested_message, Mapping):
        message_id = _non_empty_text(nested_message.get("id")) or _non_empty_text(nested_message.get("message_id"))
        if message_id is not None:
            return message_id
    return _non_empty_text(payload.get("message_id")) or _non_empty_text(payload.get("id"))


def _enqueue_task_intake_for_live_runtime(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    execution: Mapping[str, Any] | None,
    payload: dict[str, Any],
) -> dict[str, Any]:
    layout = build_workspace_runtime_layout_for_profile(profile)
    quest_root = layout.quest_root(study_id)
    runtime_message = _build_live_task_intake_runtime_message(payload)
    result: dict[str, Any] = {
        "quest_root": str(quest_root),
        "quest_status": None,
        "intervention_enqueued": False,
        "message_id": None,
        "reason": None,
        "delivery_mode": None,
        "runtime_backend_id": None,
        "backend_submit_error": None,
    }
    if not (quest_root / "quest.yaml").exists():
        result["reason"] = "quest_not_found"
        return result

    runtime_state = quest_state.load_runtime_state(quest_root)
    quest_status = str(runtime_state.get("status") or "").strip().lower()
    result["quest_status"] = quest_status or None
    if quest_status not in _LIVE_TASK_INTAKE_RUNTIME_STATUSES:
        result["reason"] = "quest_not_live"
        return result

    runtime_state["quest_id"] = study_id
    backend = runtime_backend_contract.resolve_managed_runtime_backend(execution)
    if backend is not None:
        result["runtime_backend_id"] = backend.BACKEND_ID
        try:
            response = backend.chat_quest(
                runtime_root=layout.runtime_root,
                quest_id=study_id,
                text=runtime_message,
                source="codex-study-task-intake",
            )
        except Exception as exc:
            result["backend_submit_error"] = str(exc)
        else:
            result["intervention_enqueued"] = True
            result["delivery_mode"] = "managed_runtime_chat"
            result["message_id"] = _runtime_message_id(response)
            result["reason"] = "live_runtime_task_context_submitted"
            return result

    record = user_message.enqueue_user_message(
        quest_root=quest_root,
        runtime_state=runtime_state,
        message=runtime_message,
        source="codex-study-task-intake",
    )
    result["intervention_enqueued"] = True
    result["delivery_mode"] = "durable_queue_fallback"
    result["message_id"] = record.get("message_id")
    result["reason"] = "live_runtime_task_context_enqueued_fallback"
    return result


def submit_study_task(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    task_intent: str,
    entry_mode: str | None = None,
    journal_target: str | None = None,
    constraints: Iterable[object] = (),
    evidence_boundary: Iterable[object] = (),
    trusted_inputs: Iterable[object] = (),
    reference_papers: Iterable[object] = (),
    first_cycle_outputs: Iterable[object] = (),
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    execution = _execution_payload(study_payload, profile=profile)
    selected_entry_mode = _non_empty_text(entry_mode) or _non_empty_text(execution.get("default_entry_mode")) or "full_research"
    payload = write_task_intake(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        entry_mode=selected_entry_mode,
        task_intent=task_intent,
        journal_target=journal_target,
        constraints=_normalized_strings(constraints),
        evidence_boundary=_normalized_strings(evidence_boundary),
        trusted_inputs=_normalized_strings(trusted_inputs),
        reference_papers=_normalized_strings(reference_papers),
        first_cycle_outputs=_normalized_strings(first_cycle_outputs),
    )
    layout = build_workspace_runtime_layout_for_profile(profile)
    startup_brief_path = layout.startup_brief_path(resolved_study_id)
    startup_brief_payload = study_payload.get("startup_brief")
    if isinstance(startup_brief_payload, str) and startup_brief_payload.strip():
        candidate = Path(startup_brief_payload).expanduser()
        startup_brief_path = (
            candidate.resolve()
            if candidate.is_absolute()
            else (resolved_study_root / candidate).resolve()
        )
    existing_text = startup_brief_path.read_text(encoding="utf-8") if startup_brief_path.exists() else ""
    updated_text = upsert_startup_brief_task_block(existing_text=existing_text, payload=payload)
    startup_brief_path.parent.mkdir(parents=True, exist_ok=True)
    startup_brief_path.write_text(updated_text, encoding="utf-8")
    latest_payload = read_latest_task_intake(study_root=resolved_study_root) or payload
    runtime_intervention = _enqueue_task_intake_for_live_runtime(
        profile=profile,
        study_id=resolved_study_id,
        execution=execution,
        payload=latest_payload,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "study_id": resolved_study_id,
        "study_root": str(resolved_study_root),
        "task_id": latest_payload.get("task_id"),
        "entry_mode": latest_payload.get("entry_mode"),
        "task_intent": latest_payload.get("task_intent"),
        "journal_target": latest_payload.get("journal_target"),
        "constraints": list(latest_payload.get("constraints") or []),
        "evidence_boundary": list(latest_payload.get("evidence_boundary") or []),
        "trusted_inputs": list(latest_payload.get("trusted_inputs") or []),
        "reference_papers": list(latest_payload.get("reference_papers") or []),
        "first_cycle_outputs": list(latest_payload.get("first_cycle_outputs") or []),
        "startup_brief_path": str(startup_brief_path),
        "artifacts": dict(payload.get("artifact_refs") or {}),
        "runtime_intervention": runtime_intervention,
    }


def render_submit_study_task_markdown(payload: dict[str, Any]) -> str:
    lines = render_task_intake_markdown(
        {
            "study_id": payload.get("study_id"),
            "emitted_at": _utc_now(),
            "entry_mode": payload.get("entry_mode"),
            "journal_target": payload.get("journal_target"),
            "task_intent": payload.get("task_intent"),
            "constraints": payload.get("constraints") or [],
            "evidence_boundary": payload.get("evidence_boundary") or [],
            "trusted_inputs": payload.get("trusted_inputs") or [],
            "reference_papers": payload.get("reference_papers") or [],
            "first_cycle_outputs": payload.get("first_cycle_outputs") or [],
        }
    ).rstrip("\n")
    lines += (
        "\n\n## Synced Surfaces\n\n"
        f"- startup_brief_path: `{payload.get('startup_brief_path')}`\n"
        f"- latest_json: `{((payload.get('artifacts') or {}).get('latest_json') or 'none')}`\n"
        f"- latest_markdown: `{((payload.get('artifacts') or {}).get('latest_markdown') or 'none')}`\n"
    )
    return lines
