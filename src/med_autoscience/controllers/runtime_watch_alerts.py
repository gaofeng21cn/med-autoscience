from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.profiles import WorkspaceProfile


RUNTIME_ALERT_NOTIFICATION_HEALTH_STATUSES = frozenset({"recovering", "degraded", "escalated"})
RUNTIME_ALERT_OPEN_NOTIFICATION_STATES = frozenset({"recovering", "degraded", "manual_intervention_required"})


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _non_empty_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _candidate_path(value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return Path(value).expanduser().resolve()


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _write_json_object(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def runtime_alert_delivery_latest_path(study_root: Path) -> Path:
    return study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json"


def runtime_alert_notification_state(supervision_report: Mapping[str, Any]) -> str | None:
    health_status = _non_empty_text(supervision_report.get("health_status"))
    if health_status == "live" and _non_empty_text(supervision_report.get("last_transition")) == "recovered":
        return "recovered"
    if health_status == "escalated" or bool(supervision_report.get("needs_human_intervention")):
        return "manual_intervention_required"
    if health_status in {"recovering", "degraded"}:
        return health_status
    return None


def runtime_alert_target_notification_state(
    *,
    supervision_report: Mapping[str, Any],
    previous_delivery: Mapping[str, Any] | None,
) -> str | None:
    current_state = runtime_alert_notification_state(supervision_report)
    if current_state is not None:
        return current_state
    previous_state = _non_empty_text((previous_delivery or {}).get("notification_state"))
    previous_delivery_status = _non_empty_text((previous_delivery or {}).get("delivery_status"))
    if (
        _non_empty_text(supervision_report.get("health_status")) == "live"
        and previous_state in RUNTIME_ALERT_OPEN_NOTIFICATION_STATES
        and previous_delivery_status == "delivered"
    ):
        return "recovered"
    return None


def should_deliver_runtime_alert(supervision_report: Mapping[str, Any]) -> bool:
    health_status = _non_empty_text(supervision_report.get("health_status"))
    if health_status in RUNTIME_ALERT_NOTIFICATION_HEALTH_STATUSES:
        return True
    return health_status == "live" and _non_empty_text(supervision_report.get("last_transition")) == "recovered"


def runtime_alert_fingerprint(
    supervision_report: Mapping[str, Any],
    *,
    notification_state: str | None,
) -> str:
    health_status = _non_empty_text(supervision_report.get("health_status"))
    payload = {
        "study_id": _non_empty_text(supervision_report.get("study_id")),
        "quest_id": _non_empty_text(supervision_report.get("quest_id")),
        "notification_state": notification_state,
        "health_status": health_status,
        "runtime_reason": _non_empty_text(supervision_report.get("runtime_reason")),
        "next_action": _non_empty_text(supervision_report.get("next_action")),
        "last_transition": _non_empty_text(supervision_report.get("last_transition")) if health_status == "live" else None,
        "active_run_id": _non_empty_text(supervision_report.get("active_run_id")) if health_status == "live" else None,
        "needs_human_intervention": bool(supervision_report.get("needs_human_intervention")),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_runtime_alert_message(supervision_report: Mapping[str, Any], *, notification_state: str | None) -> str:
    study_id = _non_empty_text(supervision_report.get("study_id")) or "当前研究"
    health_status = _non_empty_text(supervision_report.get("health_status"))
    if notification_state == "recovered":
        headline = f"研究 {study_id} 已恢复在线。"
    elif health_status == "recovering":
        headline = f"研究 {study_id} 当前处于自动恢复中。"
    elif health_status == "degraded":
        headline = f"研究 {study_id} 当前出现运行异常。"
    elif health_status == "escalated":
        headline = f"研究 {study_id} 当前需要人工介入。"
    else:
        headline = f"研究 {study_id} 已恢复在线。"
    detail = (
        _non_empty_text(supervision_report.get("clinician_update"))
        or _non_empty_text(supervision_report.get("summary"))
        or "系统已更新当前托管运行状态。"
    )
    next_action_summary = (
        _non_empty_text(supervision_report.get("next_action_summary"))
        or "继续按周期监督当前研究运行状态。"
    )
    return "\n".join((headline, detail, f"下一步：{next_action_summary}"))


def build_runtime_alert_payload(
    supervision_report: Mapping[str, Any],
    *,
    notification_state: str | None,
) -> dict[str, Any]:
    health_status = _non_empty_text(supervision_report.get("health_status"))
    kind = "milestone" if health_status in {"escalated", "live"} or notification_state == "recovered" else "progress"
    importance = "warning"
    if notification_state == "recovered" or health_status == "live":
        importance = "info"
    elif health_status == "escalated":
        importance = "critical"
    return {
        "kind": kind,
        "message": build_runtime_alert_message(supervision_report, notification_state=notification_state),
        "response_phase": "push",
        "importance": importance,
        "deliver_to_bound_conversations": True,
        "include_recent_inbound_messages": False,
        "reply_mode": "threaded",
    }


def resolve_runtime_alert_backend(execution: Mapping[str, Any] | None) -> Any | None:
    managed_backend = runtime_backend_contract.resolve_managed_runtime_backend(execution)
    if managed_backend is None:
        return None
    backend_id = _non_empty_text(getattr(managed_backend, "BACKEND_ID", None))
    if backend_id is None:
        return managed_backend
    try:
        controlled_backend_id, _ = runtime_backend_contract.controlled_research_backend_metadata_for_backend_id(
            backend_id
        )
        return runtime_backend_contract.get_managed_runtime_backend(controlled_backend_id)
    except ValueError:
        return managed_backend


def resolve_runtime_alert_runtime_root(
    *,
    profile: WorkspaceProfile | None,
    supervision_report: Mapping[str, Any],
    backend: Any | None,
) -> Path | None:
    backend_id = _non_empty_text(getattr(backend, "BACKEND_ID", None))
    if backend_id == "med_deepscientist" and profile is not None:
        return Path(profile.med_deepscientist_runtime_root).expanduser().resolve()
    return _candidate_path(supervision_report.get("runtime_root"))


def deliver_runtime_alert(
    *,
    profile: WorkspaceProfile | None,
    study_root: Path,
    status_payload: Mapping[str, Any],
    supervision_report: Mapping[str, Any],
    apply: bool,
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    if not apply:
        return None

    latest_path = runtime_alert_delivery_latest_path(resolved_study_root)
    previous_delivery = _read_json_object(latest_path) or {}
    notification_state = runtime_alert_target_notification_state(
        supervision_report=supervision_report,
        previous_delivery=previous_delivery,
    )
    if notification_state is None:
        return None
    alert_fingerprint = runtime_alert_fingerprint(supervision_report, notification_state=notification_state)
    if (
        _non_empty_text(previous_delivery.get("alert_fingerprint")) == alert_fingerprint
        and _non_empty_text(previous_delivery.get("delivery_status")) == "delivered"
    ):
        return previous_delivery

    quest_id = _non_empty_text(supervision_report.get("quest_id"))
    execution = status_payload.get("execution")
    backend = resolve_runtime_alert_backend(execution if isinstance(execution, Mapping) else None)
    runtime_root = resolve_runtime_alert_runtime_root(
        profile=profile,
        supervision_report=supervision_report,
        backend=backend,
    )
    payload = build_runtime_alert_payload(supervision_report, notification_state=notification_state)
    delivered_at = utc_now()
    delivery_record: dict[str, Any] = {
        "schema_version": 1,
        "delivered_at": delivered_at,
        "study_id": _non_empty_text(supervision_report.get("study_id")) or resolved_study_root.name,
        "quest_id": quest_id,
        "health_status": _non_empty_text(supervision_report.get("health_status")),
        "runtime_reason": _non_empty_text(supervision_report.get("runtime_reason")),
        "next_action": _non_empty_text(supervision_report.get("next_action")),
        "last_transition": _non_empty_text(supervision_report.get("last_transition")),
        "active_run_id": _non_empty_text(supervision_report.get("active_run_id")),
        "needs_human_intervention": bool(supervision_report.get("needs_human_intervention")),
        "notification_state": notification_state,
        "alert_fingerprint": alert_fingerprint,
        "payload": payload,
        "latest_path": str(latest_path),
    }
    try:
        if backend is None:
            raise RuntimeError("managed runtime backend unavailable for runtime alert relay")
        if runtime_root is None:
            raise RuntimeError("runtime root unavailable for runtime alert relay")
        if quest_id is None:
            raise RuntimeError("quest id unavailable for runtime alert relay")
        interaction_result = backend.artifact_interact(
            runtime_root=runtime_root,
            quest_id=quest_id,
            payload=payload,
        )
        delivery_record["delivery_status"] = "delivered"
        if isinstance(interaction_result, Mapping):
            delivery_record["interaction_result"] = dict(interaction_result)
        else:
            delivery_record["interaction_result"] = interaction_result
    except Exception as exc:
        delivery_record["delivery_status"] = "failed"
        delivery_record["error"] = str(exc)
    _write_json_object(latest_path, delivery_record)
    return delivery_record
