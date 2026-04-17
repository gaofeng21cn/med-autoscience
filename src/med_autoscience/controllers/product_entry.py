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
)
from med_autoscience.doctor import build_doctor_report
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile
from med_autoscience.study_task_intake import (
    read_latest_task_intake,
    render_task_intake_markdown,
    upsert_startup_brief_task_block,
    write_task_intake,
)
from opl_harness_shared.managed_runtime import build_managed_runtime_contract as _build_shared_managed_runtime_contract


SCHEMA_VERSION = 1
PRODUCT_ENTRY_KIND = "med_autoscience_product_entry"
PRODUCT_ENTRY_MANIFEST_KIND = "med_autoscience_product_entry_manifest"
PRODUCT_FRONTDESK_KIND = "product_frontdesk"
TARGET_DOMAIN_ID = "med-autoscience"
SUPPORTED_DIRECT_ENTRY_MODES = ("direct", "opl-handoff")
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
    if not isinstance(contract, Mapping):
        raise ValueError(f"{context} 必须是 mapping。")
    _require_nonempty_string_from_mapping(contract, "entry_adapter", context=context)
    _require_nonempty_string_from_mapping(contract, "service_safe_surface_kind", context=context)
    _require_nonempty_string_from_mapping(contract, "product_entry_builder_command", context=context)
    supported_commands = contract.get("supported_commands")
    if not isinstance(supported_commands, list) or not supported_commands:
        raise ValueError(f"{context} 缺少 supported_commands。")
    command_contracts = contract.get("command_contracts")
    if not isinstance(command_contracts, list) or not command_contracts:
        raise ValueError(f"{context} 缺少 command_contracts。")
    for index, item in enumerate(command_contracts):
        if not isinstance(item, Mapping):
            raise ValueError(f"{context}.command_contracts[{index}] 必须是 mapping。")
        _require_nonempty_string_from_mapping(
            item,
            "command",
            context=f"{context}.command_contracts[{index}]",
        )
        for field_name in ("required_fields", "optional_fields"):
            value = item.get(field_name)
            if not isinstance(value, list):
                raise ValueError(f"{context}.command_contracts[{index}].{field_name} 必须是 list。")


def _validate_gateway_interaction_contract_shape(contract: Mapping[str, Any], *, context: str) -> None:
    if not isinstance(contract, Mapping):
        raise ValueError(f"{context} 必须是 mapping。")
    _require_nonempty_string_from_mapping(contract, "surface_kind", context=context)
    _require_nonempty_string_from_mapping(contract, "frontdoor_owner", context=context)
    _require_nonempty_string_from_mapping(contract, "user_interaction_mode", context=context)
    if not isinstance(contract.get("user_commands_required"), bool):
        raise ValueError(f"{context}.user_commands_required 必须是 bool。")
    if not isinstance(contract.get("command_surfaces_for_agent_consumption_only"), bool):
        raise ValueError(f"{context}.command_surfaces_for_agent_consumption_only 必须是 bool。")
    _require_nonempty_string_from_mapping(contract, "shared_downstream_entry", context=context)
    shared_handoff_envelope = contract.get("shared_handoff_envelope")
    if not isinstance(shared_handoff_envelope, list) or not shared_handoff_envelope:
        raise ValueError(f"{context}.shared_handoff_envelope 必须是非空 list。")


def _validate_product_entry_manifest_contract(payload: Mapping[str, Any]) -> None:
    _require_nonempty_string_from_mapping(payload, "schema_ref", context="product_entry_manifest")
    _validate_domain_entry_contract_shape(
        _require_mapping(payload, "domain_entry_contract", context="product_entry_manifest"),
        context="product_entry_manifest.domain_entry_contract",
    )
    _validate_gateway_interaction_contract_shape(
        _require_mapping(payload, "gateway_interaction_contract", context="product_entry_manifest"),
        context="product_entry_manifest.gateway_interaction_contract",
    )


def _validate_product_frontdesk_contract(payload: Mapping[str, Any]) -> None:
    _require_nonempty_string_from_mapping(payload, "schema_ref", context="product_frontdesk")
    _validate_domain_entry_contract_shape(
        _require_mapping(payload, "domain_entry_contract", context="product_frontdesk"),
        context="product_frontdesk.domain_entry_contract",
    )
    _validate_gateway_interaction_contract_shape(
        _require_mapping(payload, "gateway_interaction_contract", context="product_frontdesk"),
        context="product_frontdesk.gateway_interaction_contract",
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


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
    return alerts


def _build_product_entry_preflight(
    *,
    doctor_report: Any,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    doctor_command = f"{_command_prefix(profile_ref)} doctor --profile {_profile_arg(profile_ref)}"
    start_command = f"{_command_prefix(profile_ref)} product-frontdesk --profile {_profile_arg(profile_ref)}"
    checks = [
        {
            "check_id": "workspace_root_exists",
            "title": "Workspace Root Exists",
            "status": "pass" if doctor_report.workspace_exists else "fail",
            "blocking": True,
            "summary": "workspace 根目录已就位。" if doctor_report.workspace_exists else "workspace 根目录不存在。",
            "command": doctor_command,
        },
        {
            "check_id": "runtime_root_exists",
            "title": "Runtime Root Exists",
            "status": "pass" if doctor_report.runtime_exists else "fail",
            "blocking": True,
            "summary": "runtime root 已就位。" if doctor_report.runtime_exists else "runtime root 不存在。",
            "command": doctor_command,
        },
        {
            "check_id": "studies_root_exists",
            "title": "Studies Root Exists",
            "status": "pass" if doctor_report.studies_exists else "fail",
            "blocking": True,
            "summary": "studies 根目录已就位。" if doctor_report.studies_exists else "studies 根目录不存在。",
            "command": doctor_command,
        },
        {
            "check_id": "portfolio_root_exists",
            "title": "Portfolio Root Exists",
            "status": "pass" if doctor_report.portfolio_exists else "fail",
            "blocking": True,
            "summary": "portfolio 根目录已就位。" if doctor_report.portfolio_exists else "portfolio 根目录不存在。",
            "command": doctor_command,
        },
        {
            "check_id": "research_backend_runtime_ready",
            "title": "Research Backend Runtime Ready",
            "status": "pass" if doctor_report.med_deepscientist_runtime_exists else "fail",
            "blocking": True,
            "summary": (
                "受控 research backend runtime 已就位。"
                if doctor_report.med_deepscientist_runtime_exists
                else "受控 research backend runtime 尚未就位。"
            ),
            "command": doctor_command,
        },
        {
            "check_id": "medical_overlay_ready",
            "title": "Medical Overlay Ready",
            "status": "pass" if doctor_report.medical_overlay_ready else "fail",
            "blocking": True,
            "summary": "medical overlay 已 ready。" if doctor_report.medical_overlay_ready else "medical overlay 尚未 ready。",
            "command": doctor_command,
        },
        {
            "check_id": "external_runtime_contract_ready",
            "title": "External Runtime Contract Ready",
            "status": "pass" if bool((doctor_report.external_runtime_contract or {}).get("ready")) else "fail",
            "blocking": True,
            "summary": (
                "external Hermes runtime contract 已 ready。"
                if bool((doctor_report.external_runtime_contract or {}).get("ready"))
                else "external Hermes runtime contract 尚未 ready。"
            ),
            "command": doctor_command,
        },
    ]
    blocking_check_ids = [
        check["check_id"]
        for check in checks
        if check["blocking"] and check["status"] != "pass"
    ]
    ready_to_try_now = not blocking_check_ids
    summary = (
        "当前 product-entry 前置检查已通过，可以先复核 doctor 输出，再进入 research frontdesk。"
        if ready_to_try_now
        else "当前仍有 blocking preflight check；请先修复 workspace/runtime/overlay/backend/runtime contract 再进入 research frontdesk。"
    )
    return {
        "surface_kind": "product_entry_preflight",
        "summary": summary,
        "ready_to_try_now": ready_to_try_now,
        "recommended_check_command": doctor_command,
        "recommended_start_command": start_command,
        "blocking_check_ids": blocking_check_ids,
        "checks": checks,
    }


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
    return {
        "surface_kind": "product_entry_guardrails",
        "summary": (
            "把卡住、没进度、监管掉线、需要人工决策和质量阻塞显式投影成可执行恢复回路，"
            "避免研究主线失去监管。"
        ),
        "guardrail_classes": [
            {
                "guardrail_id": "workspace_supervision_gap",
                "trigger": "workspace-cockpit attention queue / study-progress supervisor freshness",
                "symptom": "Hermes-hosted supervision 未在线、supervisor tick stale/missing、托管恢复真相不再新鲜。",
                "recommended_command": refresh_command,
            },
            {
                "guardrail_id": "study_progress_gap",
                "trigger": "study-progress progress_freshness / workspace-cockpit attention queue",
                "symptom": "当前 study 进度 stale 或 missing，疑似卡住、空转或没有新的明确推进证据。",
                "recommended_command": progress_command,
            },
            {
                "guardrail_id": "human_decision_gate",
                "trigger": "study-progress needs_physician_decision / controller decision gate",
                "symptom": "当前已前移到医生、PI 或 publication release 的人工判断节点。",
                "recommended_command": progress_command,
            },
            {
                "guardrail_id": "runtime_recovery_required",
                "trigger": "study-progress intervention_lane / runtime_supervision health_status / workspace-cockpit attention queue",
                "symptom": "托管运行恢复失败、健康降级或长期停在恢复态，当前必须优先处理 runtime recovery。",
                "recommended_command": f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>",
            },
            {
                "guardrail_id": "quality_floor_blocker",
                "trigger": "study-progress intervention_lane / runtime watch figure-loop alerts / publication gate",
                "symptom": "研究输出质量、figure/reference floor 或 publication gate 出现硬阻塞，不能继续盲目长跑。",
                "recommended_command": progress_command,
            },
        ],
        "recovery_loop": [
            {
                "step_id": "inspect_workspace_inbox",
                "command": f"{prefix} workspace-cockpit --profile {profile_arg}",
                "surface_kind": "workspace_cockpit",
            },
            {
                "step_id": "refresh_supervision",
                "command": refresh_command,
                "surface_kind": "runtime_watch_refresh",
            },
            {
                "step_id": "inspect_study_progress",
                "command": progress_command,
                "surface_kind": "study_progress",
            },
            {
                "step_id": "continue_or_relaunch",
                "command": f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>",
                "surface_kind": "launch_study",
            },
        ],
    }


def _build_phase5_platform_target() -> dict[str, Any]:
    payload = mainline_status.read_mainline_status()
    platform_target = payload.get("platform_target")
    if isinstance(platform_target, Mapping):
        return dict(platform_target)
    return dict(mainline_status._platform_target())


def _render_phase5_platform_target_markdown_lines(phase5_platform_target: Mapping[str, Any]) -> list[str]:
    lines = [
        "## Platform Target",
        "",
        f"- summary: `{phase5_platform_target.get('summary') or 'none'}`",
        f"- sequence_scope: `{phase5_platform_target.get('sequence_scope') or 'none'}`",
        f"- current_step_id: `{phase5_platform_target.get('current_step_id') or 'none'}`",
        f"- current_readiness_summary: `{phase5_platform_target.get('current_readiness_summary') or 'none'}`",
        f"- monorepo_status: `{((phase5_platform_target.get('north_star_topology') or {}).get('monorepo_status') or 'none')}`",
        f"- recommended_phase_command: `{phase5_platform_target.get('recommended_phase_command') or 'none'}`",
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
    supervisor_service_command = str(profile.workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status")
    refresh_supervision_command = (
        f"{prefix} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
        f"--profile {profile_arg} --ensure-study-runtimes --apply"
    )
    launch_study_command = f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>"
    study_progress_command = f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>"
    return {
        "surface_kind": "phase3_host_clearance_lane",
        "summary": "Phase 3 把 external runtime、Hermes-hosted workspace supervision 和 study recovery proof 扩到更多 workspace/host，并保持 fail-closed。",
        "recommended_step_id": "external_runtime_contract",
        "recommended_command": doctor_command,
        "clearance_targets": [
            {
                "target_id": "external_runtime_contract",
                "title": "Check external Hermes runtime contract",
                "commands": [
                    doctor_command,
                    hermes_runtime_check_command,
                ],
            },
            {
                "target_id": "supervisor_service",
                "title": "Keep Hermes-hosted workspace supervision online",
                "commands": [
                    supervisor_service_command,
                    refresh_supervision_command,
                ],
            },
            {
                "target_id": "study_recovery_proof",
                "title": "Prove live study recovery and supervision",
                "commands": [
                    launch_study_command,
                    study_progress_command,
                ],
            },
        ],
        "clearance_loop": [
            {
                "step_id": "external_runtime_contract",
                "title": "先确认 external Hermes runtime contract ready",
                "surface_kind": "doctor_runtime_contract",
                "command": doctor_command,
            },
            {
                "step_id": "hermes_runtime_check",
                "title": "确认 Hermes runtime 绑定证据",
                "surface_kind": "hermes_runtime_check",
                "command": hermes_runtime_check_command,
            },
            {
                "step_id": "supervisor_service",
                "title": "确认 workspace 常驻监管在线",
                "surface_kind": "workspace_supervisor_service",
                "command": supervisor_service_command,
            },
            {
                "step_id": "refresh_supervision",
                "title": "刷新 Hermes-hosted supervision tick",
                "surface_kind": "runtime_watch_refresh",
                "command": refresh_supervision_command,
            },
            {
                "step_id": "study_recovery_proof",
                "title": "证明 live study recovery / progress supervision 成立",
                "surface_kind": "launch_study",
                "command": launch_study_command,
            },
            {
                "step_id": "inspect_study_progress",
                "title": "读取 study-progress proof",
                "surface_kind": "study_progress",
                "command": study_progress_command,
            },
        ],
        "proof_surfaces": [
            {
                "surface_kind": "doctor.external_runtime_contract",
                "command": doctor_command,
            },
            {
                "surface_kind": "study_runtime_status.autonomous_runtime_notice",
                "command": f"{prefix} study-runtime-status --profile {profile_arg} --study-id <study_id>",
            },
            {
                "surface_kind": "runtime_watch",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "runtime_watch" / "latest.json"),
            },
            {
                "surface_kind": "runtime_supervision",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "runtime_supervision" / "latest.json"),
            },
            {
                "surface_kind": "controller_decisions",
                "ref": str(profile.studies_root / "<study_id>" / "artifacts" / "controller_decisions" / "latest.json"),
            },
        ],
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_3_multi_workspace_host_clearance"
        ),
    }


def _build_phase4_backend_deconstruction() -> dict[str, Any]:
    return {
        "surface_kind": "phase4_backend_deconstruction_lane",
        "summary": "Phase 4 把可迁出的通用 runtime 能力继续迁向 substrate，同时诚实保留 controlled backend executor。",
        "substrate_targets": [
            {
                "capability_id": "session_run_watch_recovery",
                "owner": "upstream Hermes-Agent",
                "summary": "session / run / watch / recovery / scheduling / interruption 继续收归 outer runtime substrate。",
            },
            {
                "capability_id": "backend_generic_runtime_contract",
                "owner": "MedAutoScience controller boundary",
                "summary": "controller / transport / durable surface 只认 backend-generic contract 与 explicit runtime handle。",
            },
        ],
        "backend_retained_now": [
            "MedDeepScientist CodexRunner autonomous executor chain",
            "backend-local agent/tool routing and Codex skills",
            "quest-local research execution, paper worktree, and daemon side effects",
        ],
        "current_backend_chain": [
            "med_autoscience.runtime_transport.hermes -> med_autoscience.runtime_transport.med_deepscientist",
            "med_deepscientist CodexRunner -> codex exec autonomous agent loop",
        ],
        "optional_executor_proofs": [
            {
                "executor_kind": "hermes_native_proof",
                "entrypoint": "MedDeepScientist HermesNativeProofRunner -> run_agent.AIAgent.run_conversation",
                "default_model": "inherit_local_hermes_default",
                "default_reasoning_effort": "inherit_local_hermes_default",
            }
        ],
        "promotion_rules": [
            "no claim of backend retirement without owner + contract + tests + proof",
            "executor replacement must be explicit and proof-backed",
            "no physical monorepo absorb before the external gate is cleared",
        ],
        "deconstruction_map_doc": "docs/program/med_deepscientist_deconstruction_map.md",
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_4_backend_deconstruction"
        ),
    }


def _build_product_entry_start(
    *,
    product_entry_shell: dict[str, Any],
    operator_loop_actions: dict[str, Any],
    family_orchestration: dict[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "product_entry_start",
        "summary": (
            "先从 MAS research frontdesk 进入当前 workspace frontdoor；"
            "需要新任务时先写 durable study task intake，已有 study 时直接恢复研究运行。"
        ),
        "recommended_mode_id": "open_frontdesk",
        "modes": [
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
        "resume_surface": dict(family_orchestration["resume_contract"]),
        "human_gate_ids": [
            gate["gate_id"]
            for gate in family_orchestration["human_gates"]
            if isinstance(gate, dict) and _non_empty_text(gate.get("gate_id")) is not None
        ],
    }


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
    }


def _attention_item(
    *,
    code: str,
    title: str,
    summary: str,
    recommended_command: str | None,
    scope: str,
    study_id: str | None = None,
) -> dict[str, Any]:
    return {
        "priority": _ATTENTION_PRIORITIES.get(code, 999),
        "scope": scope,
        "study_id": study_id,
        "code": code,
        "title": title,
        "summary": summary,
        "recommended_command": recommended_command,
    }


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
        return {
            "surface_kind": "workspace_operator_brief",
            "verdict": "attention_required",
            "summary": _non_empty_text(top.get("summary"))
            or _non_empty_text(top.get("title"))
            or "当前 workspace 有需要优先处理的 attention item。",
            "should_intervene_now": True,
            "focus_scope": _non_empty_text(top.get("scope")) or "workspace",
            "focus_study_id": _non_empty_text(top.get("study_id")),
            "recommended_step_id": "handle_attention_item",
            "recommended_command": _non_empty_text(top.get("recommended_command")) or commands.get("doctor"),
        }
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
    recommended_command = _non_empty_text(lead_study.get("recommended_command")) or _non_empty_text(
        ((lead_study.get("commands") or {}).get("progress"))
    )
    summary = (
        f"当前没有新的 workspace 级硬告警，继续盯住 {lead_study_id} 的进度与监管即可。"
        if lead_study_id is not None
        else "当前没有新的 workspace 级硬告警，继续保持对活跃 study 的监管即可。"
    )
    return {
        "surface_kind": "workspace_operator_brief",
        "verdict": "monitor_only",
        "summary": summary,
        "should_intervene_now": False,
        "focus_scope": "study",
        "focus_study_id": lead_study_id,
        "recommended_step_id": "inspect_progress",
        "recommended_command": recommended_command or user_loop.get("open_workspace_cockpit"),
    }


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
    if not service_loaded and (
        study_counts.get("supervisor_gap", 0) > 0
        or study_counts.get("progress_stale", 0) > 0
        or study_counts.get("progress_missing", 0) > 0
    ):
        queue.append(
            _attention_item(
                code="workspace_supervisor_service_not_loaded",
                title="先恢复 Hermes-hosted 常驻监管",
                summary=_non_empty_text(service.get("summary"))
                or "当前 workspace 还没有稳定的 Hermes-hosted 常驻监管入口。",
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
        lane_summary = (
            _non_empty_text(operator_verdict.get("summary"))
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
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                )
            )
            continue
        if lane_id == "workspace_supervision_gap" or supervisor_tick_status in {"stale", "missing", "invalid"}:
            queue.append(
                _attention_item(
                    code="study_supervision_gap",
                    title=f"{study_id} 当前失去新鲜监管心跳",
                    summary=lane_summary or "Hermes-hosted 托管监管存在缺口。",
                    recommended_command=preferred_command or commands.get("supervisor_tick") or progress_command,
                    scope="study",
                    study_id=study_id,
                )
            )
            continue
        if lane_id == "runtime_recovery_required":
            queue.append(
                _attention_item(
                    code="study_runtime_recovery_required",
                    title=f"{study_id} 当前需要优先处理 runtime recovery",
                    summary=lane_summary or "托管运行恢复失败或健康降级，需要尽快介入。",
                    recommended_command=preferred_command or launch_command or progress_command,
                    scope="study",
                    study_id=study_id,
                )
            )
            continue
        if lane_id == "quality_floor_blocker":
            queue.append(
                _attention_item(
                    code="study_quality_floor_blocker",
                    title=f"{study_id} 当前存在质量硬阻塞",
                    summary=(
                        lane_summary
                        or _non_empty_text(blocker_list[0] if blocker_list else None)
                        or "当前 study 存在质量或发表门控硬阻塞。"
                    ),
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
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
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
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
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
                )
            )
            continue
        if blocker_list or workspace_status in {"attention_required", "blocked"}:
            queue.append(
                _attention_item(
                    code="study_blocked",
                    title=f"{study_id} 仍有主线阻塞",
                    summary=_non_empty_text(blocker_list[0] if blocker_list else None)
                    or current_stage_summary
                    or next_system_action
                    or "当前 study 仍有待收口问题。",
                    recommended_command=preferred_command or progress_command,
                    scope="study",
                    study_id=study_id,
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
    recommended_command = _non_empty_text(progress_payload.get("recommended_command"))
    recommended_commands = [
        dict(item)
        for item in (progress_payload.get("recommended_commands") or [])
        if isinstance(item, dict)
    ]
    recovery_contract = dict(progress_payload.get("recovery_contract") or {})
    return {
        "study_id": study_id,
        "current_stage": progress_payload.get("current_stage"),
        "current_stage_summary": progress_payload.get("current_stage_summary"),
        "current_blockers": list(progress_payload.get("current_blockers") or []),
        "next_system_action": progress_payload.get("next_system_action"),
        "intervention_lane": intervention_lane or None,
        "operator_verdict": operator_verdict or None,
        "recommended_command": recommended_command,
        "recommended_commands": recommended_commands,
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
        not bool(service.get("loaded"))
        and workspace_supervision["study_counts"]["supervisor_gap"] > 0
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
        "service_install": str(profile.workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"),
        "service_status": str(profile.workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status"),
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
        f"- workspace_status: `{payload.get('workspace_status')}`",
        "",
        "## Now",
        "",
    ]
    if operator_brief:
        lines.append(f"- verdict: `{operator_brief.get('verdict') or 'none'}`")
        lines.append(f"- summary: {operator_brief.get('summary') or 'none'}")
        lines.append(f"- should_intervene_now: `{operator_brief.get('should_intervene_now')}`")
        lines.append(f"- recommended_step_id: `{operator_brief.get('recommended_step_id') or 'none'}`")
        lines.append(f"- recommended_command: `{operator_brief.get('recommended_command') or 'none'}`")
        if operator_brief.get("focus_study_id"):
            lines.append(f"- focus_study_id: `{operator_brief.get('focus_study_id')}`")
    else:
        lines.append("- 当前还没有 operator brief。")
    lines.extend([
        "",
        "## Mainline Snapshot",
        "",
    ])
    if mainline_snapshot:
        lines.append(f"- program_id: `{mainline_snapshot.get('program_id') or 'unknown'}`")
        lines.append(f"- current_stage: `{mainline_snapshot.get('current_stage_id') or 'unknown'}`")
        if mainline_snapshot.get("current_stage_summary"):
            lines.append(f"- stage_summary: {mainline_snapshot.get('current_stage_summary')}")
        if mainline_snapshot.get("current_program_phase_id"):
            lines.append(
                f"- current_program_phase: `{mainline_snapshot.get('current_program_phase_id')}`"
            )
        if mainline_snapshot.get("current_program_phase_summary"):
            lines.append(f"- phase_summary: {mainline_snapshot.get('current_program_phase_summary')}")
        next_focus = list(mainline_snapshot.get("next_focus") or [])
        if next_focus:
            lines.append(f"- next_focus: {next_focus[0]}")
    else:
        lines.append("- 当前还没有 repo 主线快照。")
    lines.extend([
        "",
        "## Workspace Supervision",
        "",
    ])
    if workspace_supervision:
        lines.append(f"- summary: {workspace_supervision.get('summary')}")
        if service.get("summary"):
            lines.append(f"- service: {service.get('summary')}")
        if study_counts:
            lines.append(
                "- counts: "
                f"supervisor_gap={study_counts.get('supervisor_gap', 0)}, "
                f"recovery_required={study_counts.get('recovery_required', 0)}, "
                f"quality_blocked={study_counts.get('quality_blocked', 0)}, "
                f"progress_stale={study_counts.get('progress_stale', 0)}, "
                f"progress_missing={study_counts.get('progress_missing', 0)}, "
                f"needs_physician_decision={study_counts.get('needs_physician_decision', 0)}"
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
            lines.append(f"- {title}: {item.get('summary')}")
            if item.get("recommended_command"):
                lines.append(f"  command: `{item.get('recommended_command')}`")
    else:
        lines.append("- 当前没有新的 attention item。")
    lines.extend(["", "## User Loop", ""])
    for name, command in (payload.get("user_loop") or {}).items():
        lines.append(f"- `{name}`: `{command}`")
    lines.extend(["", "## Phase 2 User Loop", ""])
    lines.append(f"- recommended_step_id: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`")
    lines.append(f"- recommended_command: `{phase2_user_product_loop.get('recommended_command') or 'none'}`")
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
                f"- current_stage: `{item.get('current_stage')}`",
                f"- summary: {item.get('current_stage_summary')}",
                f"- next_system_action: {item.get('next_system_action')}",
                f"- browser_url: `{((item.get('monitoring') or {}).get('browser_url') or 'none')}`",
                f"- active_run_id: `{((item.get('monitoring') or {}).get('active_run_id') or 'none')}`",
            ]
        )
        task_intake = dict(item.get("task_intake") or {})
        if task_intake:
            lines.append(f"- task_intent: {task_intake.get('task_intent') or '未提供'}")
            lines.append(f"- journal_target: {task_intake.get('journal_target') or 'none'}")
        progress_freshness = dict(item.get("progress_freshness") or {})
        if progress_freshness.get("summary"):
            lines.append(f"- progress_signal: {progress_freshness.get('summary')}")
        intervention_lane = dict(item.get("intervention_lane") or {})
        if intervention_lane.get("title"):
            lines.append(f"- intervention_lane: {intervention_lane.get('title')}")
        if intervention_lane.get("summary"):
            lines.append(f"- intervention_summary: {intervention_lane.get('summary')}")
        operator_verdict = dict(item.get("operator_verdict") or {})
        if operator_verdict.get("decision_mode"):
            lines.append(f"- operator_verdict: `{operator_verdict.get('decision_mode')}`")
        if operator_verdict.get("summary"):
            lines.append(f"- operator_summary: {operator_verdict.get('summary')}")
        recovery_contract = dict(item.get("recovery_contract") or {})
        if recovery_contract.get("action_mode"):
            lines.append(f"- recovery_contract: `{recovery_contract.get('action_mode')}`")
        if item.get("recommended_command"):
            lines.append(f"- recommended_command: `{item.get('recommended_command')}`")
        blockers = list(item.get("current_blockers") or [])
        lines.append(f"- blockers: {', '.join(blockers) if blockers else 'none'}")
        lines.append(f"- launch: `{((item.get('commands') or {}).get('launch') or '')}`")
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
        f"- study_id: `{payload.get('study_id')}`",
        f"- runtime_decision: `{((payload.get('runtime_status') or {}).get('decision') or 'unknown')}`",
        f"- browser_url: `{supervision.get('browser_url') or 'none'}`",
        f"- active_run_id: `{supervision.get('active_run_id') or 'none'}`",
        f"- current_stage: `{progress_payload.get('current_stage')}`",
        f"- current_stage_summary: {progress_payload.get('current_stage_summary')}",
        f"- next_system_action: {progress_payload.get('next_system_action')}",
    ]
    if task_intake:
        lines.extend(
            [
                f"- task_intent: {task_intake.get('task_intent') or '未提供'}",
                f"- journal_target: {task_intake.get('journal_target') or 'none'}",
            ]
        )
    if progress_freshness.get("summary"):
        lines.append(f"- progress_signal: {progress_freshness.get('summary')}")
    lines.extend(["", "## Blockers", ""])
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- 当前没有新的硬阻塞。")
    if recovery_contract:
        lines.extend(["", "## 恢复合同", ""])
        if recovery_contract.get("action_mode"):
            lines.append(f"- action_mode: `{recovery_contract.get('action_mode')}`")
        if recovery_contract.get("summary"):
            lines.append(f"- summary: {recovery_contract.get('summary')}")
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

    product_entry_shell = {
        "product_frontdesk": {
            "command": f"{prefix} product-frontdesk --profile {profile_arg}",
            "purpose": "当前 research product frontdesk，先暴露当前 frontdoor、workspace inbox 与 shared handoff 入口。",
        },
        "workspace_cockpit": {
            "command": _json_surface_command(f"{prefix} workspace-cockpit --profile {profile_arg}"),
            "purpose": "当前 workspace 级用户 inbox，聚合 attention queue、监督在线态与研究入口回路。",
        },
        "submit_study_task": {
            "command": (
                f"{prefix} submit-study-task --profile {profile_arg} "
                "--study-id <study_id> --task-intent '<task_intent>'"
            ),
            "purpose": "先把用户任务写成 durable study task intake，再启动研究执行。",
        },
        "launch_study": {
            "command": f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>",
            "purpose": "创建或恢复 study runtime，并进入当前研究主线。",
        },
        "study_progress": {
            "command": _json_surface_command(
                f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>"
            ),
            "purpose": "持续读取当前 study 的阶段摘要、阻塞、监督 freshness 与下一步。",
        },
        "mainline_status": {
            "command": f"{prefix} mainline-status",
            "purpose": "查看 repo 理想形态、当前阶段、剩余缺口与下一步焦点。",
        },
        "mainline_phase": {
            "command": f"{prefix} mainline-phase --phase <current|next|phase_id>",
            "purpose": "查看某一阶段当前可用入口、退出条件与关键文档。",
        },
    }
    shared_handoff = {
        "direct_entry_builder": {
            "command": (
                f"{prefix} build-product-entry --profile {profile_arg} "
                "--study-id <study_id> --entry-mode direct"
            ),
            "entry_mode": "direct",
        },
        "opl_handoff_builder": {
            "command": (
                f"{prefix} build-product-entry --profile {profile_arg} "
                "--study-id <study_id> --entry-mode opl-handoff"
            ),
            "entry_mode": "opl-handoff",
        },
    }
    operator_loop_actions = {
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
    }
    family_action_graph = {
        "version": "family-action-graph.v1",
        "graph_id": "mas_workspace_frontdoor_study_runtime_graph",
        "target_domain_id": TARGET_DOMAIN_ID,
        "graph_kind": "study_runtime_orchestration",
        "graph_version": "2026-04-13",
        "nodes": [
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
        "edges": [
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
        "entry_nodes": ["step:open_frontdesk"],
        "exit_nodes": ["step:continue_study", "step:inspect_progress"],
        "human_gates": [
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
        "checkpoint_policy": {
            "mode": "explicit_nodes",
            "checkpoint_nodes": [
                "step:submit_task",
                "step:continue_study",
                "step:inspect_progress",
            ],
        },
    }
    family_orchestration = {
        "action_graph_ref": {
            "ref_kind": "json_pointer",
            "ref": "/family_orchestration/action_graph",
            "label": "mas family action graph",
        },
        "action_graph": family_action_graph,
        "human_gates": [
            {
                "gate_id": "study_physician_decision_gate",
                "title": "Study physician decision gate",
            },
            {
                "gate_id": "publication_release_gate",
                "title": "Publication release gate",
            },
        ],
        "resume_contract": {
            "surface_kind": "launch_study",
            "session_locator_field": "study_id",
            "checkpoint_locator_field": "controller_decision_path",
        },
        "event_envelope_surface": {
            "ref_kind": "workspace_locator",
            "ref": "studies/<study_id>/artifacts/runtime_watch/latest.json",
            "label": "runtime watch event companion",
        },
        "checkpoint_lineage_surface": {
            "ref_kind": "workspace_locator",
            "ref": "studies/<study_id>/artifacts/controller_decisions/latest.json",
            "label": "controller checkpoint lineage companion",
        },
    }
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
    product_entry_quickstart = {
        "surface_kind": "product_entry_quickstart",
        "recommended_step_id": "open_frontdesk",
        "summary": (
            "先从 product frontdesk 进入当前 research frontdoor，"
            "需要新任务时先写 durable study task intake，再继续某个 study 或读取进度。"
        ),
        "steps": [
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
        "resume_contract": dict(family_orchestration["resume_contract"]),
        "human_gate_ids": [
            gate["gate_id"]
            for gate in family_orchestration["human_gates"]
            if isinstance(gate, dict) and _non_empty_text(gate.get("gate_id")) is not None
        ],
    }
    product_entry_start = _build_product_entry_start(
        product_entry_shell=product_entry_shell,
        operator_loop_actions=operator_loop_actions,
        family_orchestration=family_orchestration,
    )
    product_entry_overview = {
        "surface_kind": "product_entry_overview",
        "summary": (
            mainline_snapshot.get("current_stage_summary")
            or mainline_snapshot.get("current_program_phase_summary")
        ),
        "frontdesk_command": product_entry_shell["product_frontdesk"]["command"],
        "recommended_command": product_entry_shell["workspace_cockpit"]["command"],
        "operator_loop_command": product_entry_shell["workspace_cockpit"]["command"],
        "progress_surface": {
            "surface_kind": "study_progress",
            "command": product_entry_shell["study_progress"]["command"],
            "step_id": "inspect_progress",
        },
        "resume_surface": {
            "surface_kind": family_orchestration["resume_contract"]["surface_kind"],
            "command": product_entry_shell["launch_study"]["command"],
            "session_locator_field": family_orchestration["resume_contract"]["session_locator_field"],
            "checkpoint_locator_field": family_orchestration["resume_contract"]["checkpoint_locator_field"],
        },
        "recommended_step_id": product_entry_quickstart["recommended_step_id"],
        "next_focus": list(mainline_snapshot.get("next_focus") or []),
        "remaining_gaps_count": len(list(mainline_payload.get("remaining_gaps") or [])),
        "human_gate_ids": list(product_entry_quickstart["human_gate_ids"]),
    }
    product_entry_readiness = {
        "surface_kind": "product_entry_readiness",
        "verdict": "runtime_ready_not_standalone_product",
        "usable_now": True,
        "good_to_use_now": False,
        "fully_automatic": False,
        "summary": (
            "当前可以作为 research frontdesk / CLI 主线使用，并通过稳定的 runtime 回路持续推进研究；"
            "但还不是成熟的独立医学产品前台。"
        ),
        "recommended_start_surface": PRODUCT_FRONTDESK_KIND,
        "recommended_start_command": product_entry_shell["product_frontdesk"]["command"],
        "recommended_loop_surface": "workspace_cockpit",
        "recommended_loop_command": product_entry_shell["workspace_cockpit"]["command"],
        "blocking_gaps": [
            "独立医学前台 / hosted product entry 仍未 landed。",
            "更多 workspace / host 的真实 clearance 与 study-local blocker 收口仍在继续。",
        ],
    }
    managed_runtime_contract = _build_managed_runtime_contract(
        domain_owner=TARGET_DOMAIN_ID,
        executor_owner="med_deepscientist",
        supervision_status_surface="study_progress",
        attention_queue_surface="workspace_cockpit",
        recovery_contract_surface="study_runtime_status",
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "manifest_version": 2,
        "surface_kind": "product_entry_manifest",
        "manifest_kind": PRODUCT_ENTRY_MANIFEST_KIND,
        "schema_ref": PRODUCT_ENTRY_MANIFEST_SCHEMA_REF,
        "target_domain_id": TARGET_DOMAIN_ID,
        "formal_entry": {
            "default": "CLI",
            "supported_protocols": ["MCP"],
            "internal_surface": "controller",
        },
        "runtime": {
            "runtime_owner": "upstream_hermes_agent",
            "domain_owner": TARGET_DOMAIN_ID,
            "executor_owner": "med_deepscientist",
            "runtime_substrate": "external_hermes_agent_target",
            "managed_runtime_backend_id": profile.managed_runtime_backend_id,
            "runtime_root": str(profile.runtime_root),
            "hermes_home_root": str(profile.hermes_home_root),
        },
        "managed_runtime_contract": managed_runtime_contract,
        "executor_defaults": {
            "default_executor": "codex_cli_autonomous",
            "default_model": "inherit_local_codex_default",
            "default_reasoning_effort": "inherit_local_codex_default",
            "chat_completion_only_executor_forbidden": True,
            "hermes_native_requires_full_agent_loop": True,
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
        "workspace_locator": {
            "workspace_surface_kind": "med_autoscience_workspace_profile",
            "profile_name": profile.name,
            "workspace_root": workspace_root,
            "profile_ref": str(Path(profile_ref).expanduser().resolve()) if profile_ref is not None else None,
        },
        "domain_entry_contract": domain_entry_contract,
        "gateway_interaction_contract": gateway_interaction_contract,
        "recommended_shell": "workspace_cockpit",
        "recommended_command": product_entry_shell["workspace_cockpit"]["command"],
        "frontdesk_surface": {
            "shell_key": "product_frontdesk",
            "command": product_entry_shell["product_frontdesk"]["command"],
            "surface_kind": PRODUCT_FRONTDESK_KIND,
            "summary": product_entry_shell["product_frontdesk"]["purpose"],
        },
        "operator_loop_surface": {
            "shell_key": "workspace_cockpit",
            "command": product_entry_shell["workspace_cockpit"]["command"],
            "surface_kind": "workspace_cockpit",
            "summary": product_entry_shell["workspace_cockpit"]["purpose"],
        },
        "operator_loop_actions": operator_loop_actions,
        "repo_mainline": {
            "program_id": mainline_snapshot.get("program_id"),
            "current_stage_id": mainline_snapshot.get("current_stage_id"),
            "current_stage_status": mainline_snapshot.get("current_stage_status"),
            "current_stage_summary": mainline_snapshot.get("current_stage_summary"),
            "current_program_phase_id": mainline_snapshot.get("current_program_phase_id"),
            "current_program_phase_status": mainline_snapshot.get("current_program_phase_status"),
            "current_program_phase_summary": mainline_snapshot.get("current_program_phase_summary"),
            "next_focus": list(mainline_snapshot.get("next_focus") or []),
        },
        "product_entry_status": {
            "summary": mainline_snapshot.get("current_stage_summary")
            or mainline_snapshot.get("current_program_phase_summary"),
            "next_focus": list(mainline_snapshot.get("next_focus") or []),
            "remaining_gaps_count": len(list(mainline_payload.get("remaining_gaps") or [])),
        },
        "product_entry_shell": product_entry_shell,
        "shared_handoff": shared_handoff,
        "product_entry_start": product_entry_start,
        "product_entry_overview": product_entry_overview,
        "product_entry_preflight": product_entry_preflight,
        "product_entry_readiness": product_entry_readiness,
        "phase2_user_product_loop": phase2_user_product_loop,
        "product_entry_guardrails": product_entry_guardrails,
        "phase3_clearance_lane": phase3_clearance_lane,
        "phase4_backend_deconstruction": phase4_backend_deconstruction,
        "product_entry_quickstart": product_entry_quickstart,
        "family_orchestration": family_orchestration,
        "phase5_platform_target": phase5_platform_target,
        "remaining_gaps": list(mainline_payload.get("remaining_gaps") or []),
        "notes": [
            "This manifest freezes the current MAS repo-tracked research product-entry shell only.",
            "It does not include the display / paper-figure asset line.",
            "It does not claim that a mature standalone medical frontend is already landed.",
        ],
    }
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
    lines = [
        "# Product Entry Manifest",
        "",
        f"- manifest_kind: `{payload.get('manifest_kind')}`",
        f"- schema_ref: `{payload.get('schema_ref')}`",
        f"- target_domain_id: `{payload.get('target_domain_id')}`",
        f"- profile_name: `{workspace_locator.get('profile_name')}`",
        f"- workspace_root: `{workspace_locator.get('workspace_root')}`",
        f"- current_program_phase: `{repo_mainline.get('current_program_phase_id')}`",
        f"- current_stage: `{repo_mainline.get('current_stage_id')}`",
        f"- frontdoor_owner: `{gateway_interaction_contract.get('frontdoor_owner') or 'none'}`",
        f"- user_interaction_mode: `{gateway_interaction_contract.get('user_interaction_mode') or 'none'}`",
        "",
        "## Product Entry Shell",
        "",
    ]
    for name, item in product_entry_shell.items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command')}`")
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
    lines.append(f"- recommended_step_id: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`")
    lines.append(f"- recommended_command: `{phase2_user_product_loop.get('recommended_command') or 'none'}`")
    for item in phase2_user_product_loop.get("single_path") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- single_path `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend(["", "## Guardrails", ""])
    lines.append(f"- summary: {product_entry_guardrails.get('summary') or 'none'}")
    for item in product_entry_guardrails.get("guardrail_classes") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('guardrail_id')}`: `{item.get('recommended_command') or 'none'}`"
        )
    lines.extend(["", "## Phase 3 Clearance", ""])
    lines.append(f"- recommended_step_id: `{phase3_clearance_lane.get('recommended_step_id') or 'none'}`")
    lines.append(f"- recommended_command: `{phase3_clearance_lane.get('recommended_command') or 'none'}`")
    for item in phase3_clearance_lane.get("clearance_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('target_id')}`: `{((item.get('commands') or ['none'])[0])}`")
    for item in phase3_clearance_lane.get("clearance_loop") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- clearance_step `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
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
            "summary": _non_empty_text(workspace_operator_brief.get("summary"))
            or "当前 workspace 已有需要优先处理的 attention item。",
            "should_intervene_now": True,
            "focus_scope": _non_empty_text(workspace_operator_brief.get("focus_scope")) or "workspace",
            "focus_study_id": _non_empty_text(workspace_operator_brief.get("focus_study_id")),
            "recommended_step_id": "open_workspace_cockpit",
            "recommended_command": _non_empty_text(workspace_operator_brief.get("recommended_command"))
            or _non_empty_text((manifest.get("summary") or {}).get("recommended_command")),
        }
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

    payload = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": PRODUCT_FRONTDESK_KIND,
        "schema_ref": PRODUCT_FRONTDESK_SCHEMA_REF,
        "recommended_action": "inspect_or_prepare_research_loop",
        "target_domain_id": TARGET_DOMAIN_ID,
        "workspace_locator": dict(manifest.get("workspace_locator") or {}),
        "runtime": dict(manifest.get("runtime") or {}),
        "executor_defaults": dict(manifest.get("executor_defaults") or {}),
        "domain_entry_contract": dict(manifest.get("domain_entry_contract") or {}),
        "gateway_interaction_contract": dict(manifest.get("gateway_interaction_contract") or {}),
        "product_entry_status": dict(manifest.get("product_entry_status") or {}),
        "frontdesk_surface": dict(manifest.get("frontdesk_surface") or {}),
        "operator_loop_surface": dict(manifest.get("operator_loop_surface") or {}),
        "operator_loop_actions": dict(manifest.get("operator_loop_actions") or {}),
        "product_entry_start": dict(manifest.get("product_entry_start") or {}),
        "product_entry_overview": dict(manifest.get("product_entry_overview") or {}),
        "product_entry_preflight": dict(manifest.get("product_entry_preflight") or {}),
        "product_entry_readiness": dict(manifest.get("product_entry_readiness") or {}),
        "phase2_user_product_loop": dict(manifest.get("phase2_user_product_loop") or {}),
        "product_entry_guardrails": dict(manifest.get("product_entry_guardrails") or {}),
        "phase3_clearance_lane": dict(manifest.get("phase3_clearance_lane") or {}),
        "phase4_backend_deconstruction": dict(manifest.get("phase4_backend_deconstruction") or {}),
        "product_entry_quickstart": dict(manifest.get("product_entry_quickstart") or {}),
        "operator_brief": operator_brief,
        "workspace_operator_brief": workspace_operator_brief,
        "workspace_attention_queue_preview": list((workspace_cockpit.get("attention_queue") or []))[:3],
        "family_orchestration": dict(manifest.get("family_orchestration") or {}),
        "phase5_platform_target": dict(manifest.get("phase5_platform_target") or {}),
        "product_entry_manifest": manifest,
        "entry_surfaces": {
            "frontdesk": dict(product_entry_shell.get("product_frontdesk") or {}),
            "cockpit": dict(product_entry_shell.get("workspace_cockpit") or {}),
            "submit_task": dict(product_entry_shell.get("submit_study_task") or {}),
            "launch_study": dict(product_entry_shell.get("launch_study") or {}),
            "study_progress": dict(product_entry_shell.get("study_progress") or {}),
            "mainline_status": dict(product_entry_shell.get("mainline_status") or {}),
            "mainline_phase": dict(product_entry_shell.get("mainline_phase") or {}),
            "direct_entry_builder": dict(shared_handoff.get("direct_entry_builder") or {}),
            "opl_handoff_builder": dict(shared_handoff.get("opl_handoff_builder") or {}),
        },
        "summary": {
            "frontdesk_command": _non_empty_text((manifest.get("frontdesk_surface") or {}).get("command")),
            "recommended_command": _non_empty_text(manifest.get("recommended_command")),
            "operator_loop_command": _non_empty_text((manifest.get("operator_loop_surface") or {}).get("command")),
        },
        "notes": [
            "This frontdesk surface is a controller-owned front door over the current research product-entry shell.",
            "It does not claim that a mature standalone medical frontend is already landed.",
            "It does not include the display / paper-figure asset line.",
        ],
    }
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
    operator_brief = dict(payload.get("operator_brief") or {})
    quickstart = dict(payload.get("product_entry_quickstart") or {})
    workspace_operator_brief = dict(payload.get("workspace_operator_brief") or {})
    lines = [
        "# Product Frontdesk",
        "",
        f"- target_domain_id: `{payload.get('target_domain_id')}`",
        f"- schema_ref: `{payload.get('schema_ref') or 'none'}`",
        f"- recommended_action: `{payload.get('recommended_action')}`",
        f"- frontdoor_owner: `{gateway_interaction_contract.get('frontdoor_owner') or 'none'}`",
        f"- user_interaction_mode: `{gateway_interaction_contract.get('user_interaction_mode') or 'none'}`",
        f"- frontdesk_command: `{(payload.get('summary') or {}).get('frontdesk_command') or 'none'}`",
        f"- recommended_command: `{(payload.get('summary') or {}).get('recommended_command') or 'none'}`",
        f"- operator_loop_command: `{(payload.get('summary') or {}).get('operator_loop_command') or 'none'}`",
        "",
        "## Now",
        "",
    ]
    if operator_brief:
        lines.append(f"- verdict: `{operator_brief.get('verdict') or 'none'}`")
        lines.append(f"- summary: {operator_brief.get('summary') or 'none'}")
        lines.append(f"- should_intervene_now: `{operator_brief.get('should_intervene_now')}`")
        lines.append(f"- recommended_step_id: `{operator_brief.get('recommended_step_id') or 'none'}`")
        lines.append(f"- recommended_command: `{operator_brief.get('recommended_command') or 'none'}`")
        if operator_brief.get("focus_study_id"):
            lines.append(f"- focus_study_id: `{operator_brief.get('focus_study_id')}`")
    else:
        lines.append("- 当前还没有 frontdesk operator brief。")
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
        f"- summary: `{(payload.get('product_entry_overview') or {}).get('summary') or 'none'}`",
        f"- start_summary: `{(payload.get('product_entry_start') or {}).get('summary') or 'none'}`",
        f"- start_resume_command: `{((payload.get('product_entry_start') or {}).get('resume_surface') or {}).get('command') or 'none'}`",
        f"- preflight_ready: `{(payload.get('product_entry_preflight') or {}).get('ready_to_try_now')}`",
        f"- preflight_check_command: `{(payload.get('product_entry_preflight') or {}).get('recommended_check_command') or 'none'}`",
        f"- progress_command: `{((payload.get('product_entry_overview') or {}).get('progress_surface') or {}).get('command') or 'none'}`",
        f"- resume_command: `{((payload.get('product_entry_overview') or {}).get('resume_surface') or {}).get('command') or 'none'}`",
        "",
        "## Workspace Preview",
        "",
    ])
    if workspace_operator_brief:
        lines.append(f"- verdict: `{workspace_operator_brief.get('verdict') or 'none'}`")
        lines.append(f"- summary: {workspace_operator_brief.get('summary') or 'none'}")
        lines.append(f"- recommended_command: `{workspace_operator_brief.get('recommended_command') or 'none'}`")
    else:
        lines.append("- 当前没有 workspace preview。")
    for item in payload.get("workspace_attention_queue_preview") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- attention: {item.get('title') or '未命名关注项'} / `{item.get('recommended_command') or 'none'}`"
        )
    lines.extend([
        "",
        "## Phase 2 User Loop",
        "",
    ])
    lines.append(f"- recommended_step_id: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`")
    lines.append(f"- recommended_command: `{phase2_user_product_loop.get('recommended_command') or 'none'}`")
    for item in phase2_user_product_loop.get("single_path") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- single_path `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend([
        "",
        "## Guardrails",
        "",
    ])
    for item in product_entry_guardrails.get("guardrail_classes") or []:
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
    lines.append(f"- recommended_step_id: `{phase3_clearance_lane.get('recommended_step_id') or 'none'}`")
    lines.append(f"- recommended_command: `{phase3_clearance_lane.get('recommended_command') or 'none'}`")
    for item in phase3_clearance_lane.get("clearance_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('target_id')}`: `{((item.get('commands') or ['none'])[0])}`")
    for item in phase3_clearance_lane.get("clearance_loop") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- clearance_step `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend(
        [
            "",
            "## Phase 4 Deconstruction",
            "",
        ]
    )
    for item in phase4_backend_deconstruction.get("substrate_targets") or []:
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
        f"- ready_to_try_now: `{payload.get('ready_to_try_now')}`",
        f"- summary: `{payload.get('summary') or 'none'}`",
        f"- recommended_check_command: `{payload.get('recommended_check_command') or 'none'}`",
        f"- recommended_start_command: `{payload.get('recommended_start_command') or 'none'}`",
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
                + f"[{check.get('status')}] "
                + f"(blocking={check.get('blocking')}) "
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
        f"- summary: `{payload.get('summary') or 'none'}`",
        f"- recommended_mode_id: `{payload.get('recommended_mode_id') or 'none'}`",
        f"- resume_surface: `{((payload.get('resume_surface') or {}).get('surface_kind') or 'none')}`",
        "",
        "## Modes",
        "",
    ]
    modes = list(payload.get("modes") or [])
    if modes:
        for mode in modes:
            if not isinstance(mode, dict):
                continue
            lines.append(
                "- "
                + f"`{mode.get('mode_id')}` "
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
        f"- target_domain_id: `{payload.get('target_domain_id')}`",
        f"- entry_mode: `{payload.get('entry_mode')}`",
        f"- task_intent: {payload.get('task_intent')}",
        f"- study_id: `{domain_payload.get('study_id') or 'unknown'}`",
        f"- journal_target: {domain_payload.get('journal_target') or 'none'}",
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
            f"- runtime_supervision_path: `{return_surface_contract.get('runtime_supervision_path') or 'none'}`",
            f"- publication_eval_path: `{return_surface_contract.get('publication_eval_path') or 'none'}`",
            f"- controller_decision_path: `{return_surface_contract.get('controller_decision_path') or 'none'}`",
            "",
        ]
    )
    return "\n".join(lines)


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
