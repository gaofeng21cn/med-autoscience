from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol


SCHEMA_VERSION = 1
_RECOVERY_DECISIONS = frozenset({"create_and_start", "resume", "relaunch_stopped"})
_ACTIVE_QUEST_STATUSES = frozenset({"running", "active"})
_DROPOUT_REASONS = frozenset(
    {
        "quest_marked_running_but_no_live_session",
        "running_quest_live_session_audit_failed",
        "resume_request_failed",
        "create_request_failed",
    }
)


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _candidate_path(value: object) -> Path | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return Path(text).expanduser().resolve()


def _bool_or_none(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _int_or_zero(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(value, 0)
    text = _non_empty_text(value)
    if text is None:
        return 0
    try:
        return max(int(text), 0)
    except ValueError:
        return 0


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _artifact_slug(recorded_at: str) -> str:
    normalized = recorded_at.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _report_root(study_root: Path) -> Path:
    return study_root / "artifacts" / "runtime" / "runtime_supervision"


def _latest_report_path(study_root: Path) -> Path:
    return _report_root(study_root) / "latest.json"


def _timestamped_report_path(study_root: Path, recorded_at: str) -> Path:
    return _report_root(study_root) / f"{_artifact_slug(recorded_at)}.json"


def _is_managed_runtime_status(status_payload: Mapping[str, Any]) -> bool:
    execution = status_payload.get("execution")
    if not isinstance(execution, Mapping):
        return False
    return (
        _non_empty_text(execution.get("engine")) == "med-deepscientist"
        and _non_empty_text(execution.get("auto_entry")) == "on_managed_research_intent"
    )


def _runtime_facts(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime_liveness_audit = (
        dict(status_payload.get("runtime_liveness_audit") or {})
        if isinstance(status_payload.get("runtime_liveness_audit"), Mapping)
        else {}
    )
    runtime_audit = (
        dict(runtime_liveness_audit.get("runtime_audit") or {})
        if isinstance(runtime_liveness_audit.get("runtime_audit"), Mapping)
        else {}
    )
    active_run_id = (
        _non_empty_text(
            ((status_payload.get("execution_owner_guard") or {}) if isinstance(status_payload.get("execution_owner_guard"), Mapping) else {}).get(
                "active_run_id"
            )
        )
        or _non_empty_text(((status_payload.get("autonomous_runtime_notice") or {}) if isinstance(status_payload.get("autonomous_runtime_notice"), Mapping) else {}).get("active_run_id"))
        or _non_empty_text(runtime_liveness_audit.get("active_run_id"))
        or _non_empty_text(runtime_audit.get("active_run_id"))
    )
    runtime_liveness_status = _non_empty_text(runtime_liveness_audit.get("status")) or "unknown"
    worker_running = _bool_or_none(runtime_audit.get("worker_running"))
    strict_live = runtime_liveness_status == "live" and worker_running is True and active_run_id is not None
    return {
        "runtime_liveness_status": runtime_liveness_status,
        "worker_running": worker_running,
        "active_run_id": active_run_id,
        "strict_live": strict_live,
    }


def _needs_drop_detection(status_payload: Mapping[str, Any], *, strict_live: bool) -> bool:
    if strict_live:
        return False
    decision = _non_empty_text(status_payload.get("decision"))
    reason = _non_empty_text(status_payload.get("reason"))
    quest_status = _non_empty_text(status_payload.get("quest_status"))
    if reason in _DROPOUT_REASONS:
        return True
    if decision in _RECOVERY_DECISIONS:
        return False
    return quest_status in _ACTIVE_QUEST_STATUSES


def _escalation_ref(
    *,
    study_root: Path,
    quest_root: Path | None,
    quest_id: str | None,
    recorded_at: str,
    runtime_reason: str | None,
    latest_report_path: Path,
    runtime_watch_report_path: Path | None,
) -> dict[str, str] | None:
    if quest_root is None or quest_id is None:
        return None
    launch_report_path = _candidate_path(
        latest_report_path.parent.parent / "last_launch_report.json"
    )
    summary_ref = str(launch_report_path) if launch_report_path is not None else str(latest_report_path)
    evidence_refs = [str(latest_report_path)]
    if launch_report_path is not None:
        evidence_refs.append(str(launch_report_path))
    if runtime_watch_report_path is not None:
        evidence_refs.append(str(runtime_watch_report_path))
    record = study_runtime_protocol.RuntimeEscalationRecord(
        schema_version=1,
        record_id=f"runtime-escalation::{study_root.name}::{quest_id}::runtime_supervision_escalated::{recorded_at}",
        study_id=study_root.name,
        quest_id=quest_id,
        emitted_at=recorded_at,
        trigger=study_runtime_protocol.RuntimeEscalationTrigger(
            trigger_id=runtime_reason or "runtime_supervision_escalated",
            source="runtime_supervision",
        ),
        scope="quest",
        severity="quest",
        reason="runtime_supervision_escalated",
        recommended_actions=("manual_runtime_review_required", "controller_review_required"),
        evidence_refs=tuple(evidence_refs),
        runtime_context_refs={
            "runtime_supervision_path": str(latest_report_path),
            "launch_report_path": summary_ref,
        },
        summary_ref=summary_ref,
        artifact_path=None,
    )
    written_record = study_runtime_protocol.write_runtime_escalation_record(
        quest_root=quest_root,
        record=record,
    )
    return written_record.ref().to_dict()


def materialize_runtime_supervision(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
    recorded_at: str,
    apply: bool,
    runtime_watch_report_path: Path | None = None,
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    if not _is_managed_runtime_status(status_payload):
        return None

    latest_report_path = _latest_report_path(resolved_study_root)
    previous_report = _read_json(latest_report_path) or {}
    previous_health_status = _non_empty_text(previous_report.get("health_status"))
    previous_failure_count = _int_or_zero(previous_report.get("consecutive_failure_count"))
    previous_attempt_count = _int_or_zero(previous_report.get("recovery_attempt_count"))

    quest_id = _non_empty_text(status_payload.get("quest_id"))
    quest_root = _candidate_path(status_payload.get("quest_root"))
    decision = _non_empty_text(status_payload.get("decision"))
    runtime_reason = _non_empty_text(status_payload.get("reason"))
    quest_status = _non_empty_text(status_payload.get("quest_status"))
    launch_report_path = _candidate_path(status_payload.get("launch_report_path"))
    facts = _runtime_facts(status_payload)
    strict_live = bool(facts["strict_live"])

    if strict_live:
        health_status = "live"
        last_transition = "recovered" if previous_health_status in {"recovering", "degraded", "escalated"} else "live_confirmed"
        consecutive_failure_count = 0
        recovery_attempt_count = previous_attempt_count
        needs_human_intervention = False
        summary = "托管运行时在线，研究仍在自动推进。"
        clinician_update = "系统确认当前研究运行在线，自动推进仍在继续。"
        next_action = "continue_supervising_runtime"
        next_action_summary = "继续监督当前托管运行，并等待新的阶段事件。"
    elif decision in _RECOVERY_DECISIONS:
        health_status = "recovering"
        last_transition = "recovery_requested"
        consecutive_failure_count = 0
        recovery_attempt_count = previous_attempt_count + 1 if apply else previous_attempt_count
        needs_human_intervention = False
        if runtime_reason == "quest_marked_running_but_no_live_session":
            summary = "系统已检测到运行掉线，正在自动尝试恢复。"
            clinician_update = "系统发现研究表面仍显示在运行，但 live worker 已掉线，已自动发起恢复。"
        else:
            summary = "系统正在自动启动或恢复托管运行。"
            clinician_update = "系统正在推进托管运行进入可监督的 live 状态。"
        next_action = "wait_for_runtime_recovery_confirmation"
        next_action_summary = "等待下一次巡检确认 worker 已重新上线并恢复 live。"
    elif _needs_drop_detection(status_payload, strict_live=strict_live):
        consecutive_failure_count = previous_failure_count + 1 if previous_health_status in {"degraded", "escalated"} else 1
        health_status = "escalated" if consecutive_failure_count >= 2 else "degraded"
        last_transition = "recovery_failed" if runtime_reason in {"resume_request_failed", "create_request_failed"} else "dropout_detected"
        recovery_attempt_count = previous_attempt_count + (
            1 if runtime_reason in {"resume_request_failed", "create_request_failed"} else 0
        )
        needs_human_intervention = health_status == "escalated"
        if health_status == "escalated":
            summary = "托管运行时已连续恢复失败，必须人工介入。"
            clinician_update = "系统确认研究运行已经掉线，自动恢复连续失败，需要医生/PI 看到明确告警。"
            next_action = "manual_intervention_required"
            next_action_summary = "请人工检查 MedDeepScientist 运行面，并决定是否暂停、重启或接管。"
        else:
            summary = "托管运行时健康异常，系统已发现掉线或恢复失败。"
            clinician_update = "系统已发现研究运行异常，当前会优先继续监管并尝试后续恢复。"
            next_action = "continue_runtime_supervision"
            next_action_summary = "继续周期巡检运行健康，并在下一次 supervisor tick 判断是否恢复成功。"
    else:
        health_status = "inactive"
        last_transition = "inactive"
        consecutive_failure_count = 0
        recovery_attempt_count = 0
        needs_human_intervention = False
        summary = "当前没有需要升级的托管运行健康异常。"
        clinician_update = "当前没有新的托管运行掉线信号。"
        next_action = "continue_supervising_runtime"
        next_action_summary = "继续按周期刷新研究状态与前台进度。"

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": recorded_at,
        "study_id": _non_empty_text(status_payload.get("study_id")) or resolved_study_root.name,
        "study_root": str(resolved_study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root) if quest_root is not None else None,
        "runtime_root": str(quest_root.parent) if quest_root is not None else None,
        "health_status": health_status,
        "runtime_decision": decision,
        "runtime_reason": runtime_reason,
        "quest_status": quest_status,
        "runtime_liveness_status": facts["runtime_liveness_status"],
        "worker_running": facts["worker_running"],
        "active_run_id": facts["active_run_id"],
        "recovery_attempt_count": recovery_attempt_count,
        "consecutive_failure_count": consecutive_failure_count,
        "last_transition": last_transition,
        "needs_human_intervention": needs_human_intervention,
        "summary": summary,
        "clinician_update": clinician_update,
        "next_action": next_action,
        "next_action_summary": next_action_summary,
        "refs": {
            "launch_report_path": str(launch_report_path) if launch_report_path is not None else None,
            "runtime_watch_report_path": (
                str(runtime_watch_report_path.expanduser().resolve()) if runtime_watch_report_path is not None else None
            ),
        },
    }

    if health_status == "escalated":
        escalation_ref = _escalation_ref(
            study_root=resolved_study_root,
            quest_root=quest_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            runtime_reason=runtime_reason,
            latest_report_path=latest_report_path,
            runtime_watch_report_path=runtime_watch_report_path,
        )
        if escalation_ref is not None:
            report["runtime_escalation_ref"] = escalation_ref
            report["refs"]["runtime_escalation_path"] = escalation_ref["artifact_path"]

    timestamped_report_path = _timestamped_report_path(resolved_study_root, recorded_at)
    report["artifact_path"] = str(timestamped_report_path)
    report["latest_path"] = str(latest_report_path)
    _write_json(timestamped_report_path, report)
    _write_json(latest_report_path, report)
    return report
