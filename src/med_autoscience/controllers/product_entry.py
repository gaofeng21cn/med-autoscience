from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from med_autoscience.controllers import study_progress, study_runtime_router
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
    commands = {
        "doctor": f"{_command_prefix(profile_ref)} doctor --profile {_profile_arg(profile_ref)}",
        "bootstrap": f"{_command_prefix(profile_ref)} bootstrap --profile {_profile_arg(profile_ref)}",
        "supervisor_tick": (
            f"{_command_prefix(profile_ref)} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {_profile_arg(profile_ref)} --ensure-study-runtimes --apply"
        ),
        "service_install": str(profile.workspace_root / "ops" / "medautoscience" / "bin" / "install-watch-runtime-service"),
        "service_status": str(profile.workspace_root / "ops" / "medautoscience" / "bin" / "watch-runtime-service-status"),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "profile_name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "workspace_status": workspace_status,
        "workspace_alerts": workspace_alerts,
        "workspace_supervision": workspace_supervision,
        "studies": studies,
        "commands": commands,
    }


def render_workspace_cockpit_markdown(payload: dict[str, Any]) -> str:
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
        "## Workspace Supervision",
        "",
    ]
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
