from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from med_autoscience.controllers import mainline_status, study_progress, study_runtime_router
from med_autoscience.controllers.study_runtime_resolution import _execution_payload, _resolve_study
from med_autoscience.doctor import build_doctor_report
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile
from med_autoscience.study_task_intake import (
    read_latest_task_intake,
    render_task_intake_markdown,
    upsert_startup_brief_task_block,
    write_task_intake,
)


SCHEMA_VERSION = 1
PRODUCT_ENTRY_KIND = "med_autoscience_product_entry"
PRODUCT_ENTRY_MANIFEST_KIND = "med_autoscience_product_entry_manifest"
PRODUCT_FRONTDESK_KIND = "product_frontdesk"
TARGET_DOMAIN_ID = "med-autoscience"
SUPPORTED_DIRECT_ENTRY_MODES = ("direct", "opl-handoff")
_ATTENTION_PRIORITIES = {
    "workspace_supervisor_service_not_loaded": 0,
    "study_needs_physician_decision": 1,
    "study_supervision_gap": 2,
    "study_progress_stale": 3,
    "study_progress_missing": 4,
    "study_blocked": 5,
}


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


def _slugify_workspace_name(workspace_name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", workspace_name.strip()).strip("-").lower()
    return normalized or "workspace"


def _run_command(*, command: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    return completed.returncode, output


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


def _watch_runtime_launchd_label(profile: WorkspaceProfile) -> str:
    return f"ai.medautoscience.{_slugify_workspace_name(profile.name)}.watch-runtime"


def _watch_runtime_systemd_name(profile: WorkspaceProfile) -> str:
    return f"medautoscience-watch-runtime-{_slugify_workspace_name(profile.name)}"


def _inspect_watch_runtime_service(profile: WorkspaceProfile) -> dict[str, Any]:
    if sys.platform == "darwin":
        service_label = _watch_runtime_launchd_label(profile)
        service_file = Path.home() / "Library" / "LaunchAgents" / f"{service_label}.plist"
        exit_code, output = _run_command(command=["launchctl", "print", f"gui/{os.getuid()}/{service_label}"])
        loaded = exit_code == 0
        service_file_exists = service_file.is_file()
        status = "loaded" if loaded else ("not_loaded" if service_file_exists else "not_installed")
        if loaded:
            summary = "MAS supervisor service 已常驻在线，workspace 级监管会持续刷新。"
        elif service_file_exists:
            summary = "MAS supervisor service 已安装但当前未常驻在线；需要先拉起 watch-runtime service。"
        else:
            summary = "MAS supervisor service 尚未安装；如需持续监管，请先安装 watch-runtime service。"
        return {
            "manager": "launchd",
            "service_label": service_label,
            "service_file": str(service_file),
            "service_file_exists": service_file_exists,
            "loaded": loaded,
            "status": status,
            "summary": summary,
            "raw_output": output,
        }
    if sys.platform.startswith("linux"):
        service_name = _watch_runtime_systemd_name(profile)
        service_file = Path.home() / ".config" / "systemd" / "user" / f"{service_name}.service"
        exit_code, output = _run_command(command=["systemctl", "--user", "is-active", f"{service_name}.service"])
        loaded = exit_code == 0
        service_file_exists = service_file.is_file()
        status = "loaded" if loaded else ("not_loaded" if service_file_exists else "not_installed")
        if loaded:
            summary = "MAS supervisor service 已常驻在线，workspace 级监管会持续刷新。"
        elif service_file_exists:
            summary = "MAS supervisor service 已安装但当前未常驻在线；需要先拉起 watch-runtime service。"
        else:
            summary = "MAS supervisor service 尚未安装；如需持续监管，请先安装 watch-runtime service。"
        return {
            "manager": "systemd",
            "service_name": service_name,
            "service_file": str(service_file),
            "service_file_exists": service_file_exists,
            "loaded": loaded,
            "status": status,
            "summary": summary,
            "raw_output": output,
        }
    return {
        "manager": None,
        "service_file_exists": False,
        "loaded": False,
        "status": "unsupported",
        "summary": "当前平台不支持自动检查 MAS supervisor service；必要时请手工运行 watch。",
        "raw_output": "",
    }


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
                "title": "Open research frontdesk",
                "command": product_entry_shell["product_frontdesk"]["command"],
                "surface_kind": PRODUCT_FRONTDESK_KIND,
                "summary": product_entry_shell["product_frontdesk"]["purpose"],
                "requires": [],
            },
            {
                "mode_id": "submit_task",
                "title": "Write durable study task",
                "command": product_entry_shell["submit_study_task"]["command"],
                "surface_kind": "study_task_intake",
                "summary": operator_loop_actions["submit_task"]["summary"],
                "requires": list(operator_loop_actions["submit_task"]["requires"]),
            },
            {
                "mode_id": "continue_study",
                "title": "Continue or relaunch a study",
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
                title="先恢复 MAS supervisor 常驻监管",
                summary=_non_empty_text(service.get("summary"))
                or "当前 workspace 还没有稳定的 MAS supervisor 常驻监管入口。",
                recommended_command=commands.get("service_status") or commands.get("service_install"),
                scope="workspace",
            )
        )

    for item in studies:
        study_id = _non_empty_text(item.get("study_id")) or "unknown-study"
        monitoring = dict(item.get("monitoring") or {})
        progress_freshness = dict(item.get("progress_freshness") or {})
        blocker_list = list(item.get("current_blockers") or [])
        progress_command = _non_empty_text(((item.get("commands") or {}).get("progress")))
        supervisor_tick_status = _non_empty_text(monitoring.get("supervisor_tick_status"))
        progress_status = _non_empty_text(progress_freshness.get("status"))
        current_stage_summary = _non_empty_text(item.get("current_stage_summary"))
        next_system_action = _non_empty_text(item.get("next_system_action"))

        if bool(item.get("needs_physician_decision")):
            queue.append(
                _attention_item(
                    code="study_needs_physician_decision",
                    title=f"{study_id} 需要医生或 PI 判断",
                    summary=current_stage_summary or next_system_action or "当前 study 已到需要人工明确决策的节点。",
                    recommended_command=progress_command,
                    scope="study",
                    study_id=study_id,
                )
            )
            continue
        if supervisor_tick_status in {"stale", "missing", "invalid"}:
            queue.append(
                _attention_item(
                    code="study_supervision_gap",
                    title=f"{study_id} 当前失去新鲜监管心跳",
                    summary=current_stage_summary or "MAS 外环监管存在缺口。",
                    recommended_command=commands.get("supervisor_tick") or progress_command,
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
                    recommended_command=progress_command,
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
                    recommended_command=progress_command,
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
                    recommended_command=progress_command,
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
    return {
        "study_id": study_id,
        "current_stage": progress_payload.get("current_stage"),
        "current_stage_summary": progress_payload.get("current_stage_summary"),
        "current_blockers": list(progress_payload.get("current_blockers") or []),
        "next_system_action": progress_payload.get("next_system_action"),
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
    service = _inspect_watch_runtime_service(profile)
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
        "user_loop": _user_loop(profile=profile, profile_ref=profile_ref),
        "studies": studies,
        "commands": commands,
    }


def render_workspace_cockpit_markdown(payload: dict[str, Any]) -> str:
    mainline_snapshot = dict(payload.get("mainline_snapshot") or {})
    workspace_supervision = dict(payload.get("workspace_supervision") or {})
    service = dict(workspace_supervision.get("service") or {})
    study_counts = dict(workspace_supervision.get("study_counts") or {})
    lines = [
        "# Workspace Cockpit",
        "",
        f"- profile: `{payload.get('profile_name')}`",
        f"- workspace_root: `{payload.get('workspace_root')}`",
        f"- workspace_status: `{payload.get('workspace_status')}`",
        "",
        "## Mainline Snapshot",
        "",
    ]
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
    profile_arg = _profile_arg(profile_ref)
    prefix = _command_prefix(profile_ref)
    workspace_root = str(profile.workspace_root)

    product_entry_shell = {
        "product_frontdesk": {
            "command": f"{prefix} product-frontdesk --profile {profile_arg}",
            "purpose": "当前 research product frontdesk，先暴露当前 frontdoor、workspace inbox 与 shared handoff 入口。",
        },
        "workspace_cockpit": {
            "command": f"{prefix} workspace-cockpit --profile {profile_arg}",
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
            "command": f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>",
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
                "title": "Open research frontdesk",
                "command": product_entry_shell["product_frontdesk"]["command"],
                "surface_kind": PRODUCT_FRONTDESK_KIND,
                "summary": product_entry_shell["product_frontdesk"]["purpose"],
                "requires": [],
            },
            {
                "step_id": "submit_task",
                "title": "Write durable study task",
                "command": product_entry_shell["submit_study_task"]["command"],
                "surface_kind": "study_task_intake",
                "summary": operator_loop_actions["submit_task"]["summary"],
                "requires": list(operator_loop_actions["submit_task"]["requires"]),
            },
            {
                "step_id": "continue_study",
                "title": "Continue or relaunch a study",
                "command": product_entry_shell["launch_study"]["command"],
                "surface_kind": "launch_study",
                "summary": operator_loop_actions["continue_study"]["summary"],
                "requires": list(operator_loop_actions["continue_study"]["requires"]),
            },
            {
                "step_id": "inspect_progress",
                "title": "Inspect current study progress",
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

    return {
        "schema_version": SCHEMA_VERSION,
        "manifest_version": 2,
        "surface_kind": "product_entry_manifest",
        "manifest_kind": PRODUCT_ENTRY_MANIFEST_KIND,
        "target_domain_id": TARGET_DOMAIN_ID,
        "formal_entry": {
            "default": "CLI",
            "supported_protocols": ["MCP"],
            "internal_surface": "controller",
        },
        "runtime": {
            "runtime_owner": "med_autoscience_gateway",
            "runtime_substrate": "external_hermes_agent_target",
            "managed_runtime_backend_id": profile.managed_runtime_backend_id,
            "runtime_root": str(profile.runtime_root),
            "hermes_home_root": str(profile.hermes_home_root),
        },
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
        },
        "workspace_locator": {
            "workspace_surface_kind": "med_autoscience_workspace_profile",
            "profile_name": profile.name,
            "workspace_root": workspace_root,
            "profile_ref": str(Path(profile_ref).expanduser().resolve()) if profile_ref is not None else None,
        },
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
        "product_entry_quickstart": product_entry_quickstart,
        "family_orchestration": family_orchestration,
        "remaining_gaps": list(mainline_payload.get("remaining_gaps") or []),
        "notes": [
            "This manifest freezes the current MAS repo-tracked research product-entry shell only.",
            "It does not include the display / paper-figure asset line.",
            "It does not claim that a mature standalone medical frontend is already landed.",
        ],
    }


def render_product_entry_manifest_markdown(payload: dict[str, Any]) -> str:
    workspace_locator = dict(payload.get("workspace_locator") or {})
    repo_mainline = dict(payload.get("repo_mainline") or {})
    product_entry_shell = dict(payload.get("product_entry_shell") or {})
    shared_handoff = dict(payload.get("shared_handoff") or {})
    lines = [
        "# Product Entry Manifest",
        "",
        f"- manifest_kind: `{payload.get('manifest_kind')}`",
        f"- target_domain_id: `{payload.get('target_domain_id')}`",
        f"- profile_name: `{workspace_locator.get('profile_name')}`",
        f"- workspace_root: `{workspace_locator.get('workspace_root')}`",
        f"- current_program_phase: `{repo_mainline.get('current_program_phase_id')}`",
        f"- current_stage: `{repo_mainline.get('current_stage_id')}`",
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
    product_entry_shell = dict(manifest.get("product_entry_shell") or {})
    shared_handoff = dict(manifest.get("shared_handoff") or {})

    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": PRODUCT_FRONTDESK_KIND,
        "recommended_action": "inspect_or_prepare_research_loop",
        "target_domain_id": TARGET_DOMAIN_ID,
        "workspace_locator": dict(manifest.get("workspace_locator") or {}),
        "runtime": dict(manifest.get("runtime") or {}),
        "executor_defaults": dict(manifest.get("executor_defaults") or {}),
        "product_entry_status": dict(manifest.get("product_entry_status") or {}),
        "frontdesk_surface": dict(manifest.get("frontdesk_surface") or {}),
        "operator_loop_surface": dict(manifest.get("operator_loop_surface") or {}),
        "operator_loop_actions": dict(manifest.get("operator_loop_actions") or {}),
        "product_entry_start": dict(manifest.get("product_entry_start") or {}),
        "product_entry_overview": dict(manifest.get("product_entry_overview") or {}),
        "product_entry_preflight": dict(manifest.get("product_entry_preflight") or {}),
        "product_entry_readiness": dict(manifest.get("product_entry_readiness") or {}),
        "product_entry_quickstart": dict(manifest.get("product_entry_quickstart") or {}),
        "family_orchestration": dict(manifest.get("family_orchestration") or {}),
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


def render_product_frontdesk_markdown(payload: dict[str, Any]) -> str:
    entry_surfaces = dict(payload.get("entry_surfaces") or {})
    lines = [
        "# Product Frontdesk",
        "",
        f"- target_domain_id: `{payload.get('target_domain_id')}`",
        f"- recommended_action: `{payload.get('recommended_action')}`",
        f"- frontdesk_command: `{(payload.get('summary') or {}).get('frontdesk_command') or 'none'}`",
        f"- recommended_command: `{(payload.get('summary') or {}).get('recommended_command') or 'none'}`",
        f"- operator_loop_command: `{(payload.get('summary') or {}).get('operator_loop_command') or 'none'}`",
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
        "## Entry Surfaces",
        "",
    ]
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

    return {
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
            "runtime_owner": "med_autoscience_gateway",
            "runtime_substrate": "external_hermes_agent_target",
            "managed_entry_mode": managed_entry_mode,
            "managed_runtime_backend_id": runtime_contract.get("managed_runtime_backend_id") or profile.managed_runtime_backend_id,
            "runtime_root": runtime_contract.get("runtime_root") or str(profile.runtime_root),
            "hermes_agent_repo_root": runtime_contract.get("hermes_agent_repo_root"),
            "hermes_home_root": runtime_contract.get("hermes_home_root") or str(profile.hermes_home_root),
            "start_entry": "launch-study",
            "resume_entry": "launch-study",
        },
        "return_surface_contract": {
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
