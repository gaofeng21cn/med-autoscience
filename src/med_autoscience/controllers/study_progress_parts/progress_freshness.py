from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)

_ACTIVITY_TIMEOUT_REASONS = {
    "read_churn_without_artifact_delta",
    "same_fingerprint_loop",
}
_NEW_RUN_ACTIVITY_GRACE_SECONDS = 30 * 60


def _freshness_from_timestamp(
    *,
    timestamp: object,
    source: str | None,
    summary: str | None,
    stale_after_seconds: int = _PROGRESS_STALE_AFTER_SECONDS,
) -> dict[str, Any]:
    normalized = _normalize_timestamp(_non_empty_text(timestamp))
    if normalized is None:
        return {
            "status": "missing",
            "required": True,
            "summary": "未观察到该维度的新鲜度信号。",
            "stale_after_seconds": stale_after_seconds,
            "latest_progress_at": None,
            "latest_progress_time_label": None,
            "latest_progress_source": source,
            "latest_progress_summary": summary,
            "seconds_since_latest_progress": None,
        }
    progress_freshness_now = _controller_override("_progress_freshness_now", _progress_freshness_now)
    age_seconds = max(
        0,
        int((progress_freshness_now() - datetime.fromisoformat(normalized)).total_seconds()),
    )
    status = "stale" if age_seconds > stale_after_seconds else "fresh"
    return {
        "status": status,
        "required": True,
        "summary": summary or ("该维度信号已过期。" if status == "stale" else "该维度信号新鲜。"),
        "stale_after_seconds": stale_after_seconds,
        "latest_progress_at": normalized,
        "latest_progress_time_label": _time_label(normalized),
        "latest_progress_source": source,
        "latest_progress_summary": summary,
        "seconds_since_latest_progress": age_seconds,
    }


def _timestamp_value(value: object) -> datetime | None:
    normalized = _normalize_timestamp(value)
    if normalized is None:
        return None
    return datetime.fromisoformat(normalized)


def _latest_runtime_observed_at(
    *,
    status: Mapping[str, Any] | None,
    runtime_supervision_payload: Mapping[str, Any] | None,
) -> str | None:
    status_payload = _mapping_copy(status)
    supervision_payload = _mapping_copy(runtime_supervision_payload)
    status_health = _mapping_copy(status_payload.get("runtime_health_snapshot"))
    supervision_health = _mapping_copy(supervision_payload.get("runtime_health_snapshot"))
    runtime_health = supervision_health or status_health
    candidates: list[str] = []
    refs = runtime_health.get("dominant_runtime_refs")
    if isinstance(refs, list):
        for item in refs:
            if isinstance(item, dict):
                value = _non_empty_text(item.get("recorded_at"))
                if value is not None:
                    candidates.append(value)
    supervisor_state = _mapping_copy(runtime_health.get("supervisor_state"))
    for value in (
        runtime_health.get("generated_at"),
        supervisor_state.get("latest_recorded_at"),
        supervision_payload.get("recorded_at"),
        status_payload.get("recorded_at"),
    ):
        text = _non_empty_text(value)
        if text is not None:
            candidates.append(text)
    dated = [
        (parsed, text)
        for text in candidates
        if (parsed := _timestamp_value(text)) is not None
    ]
    if not dated:
        return None
    return max(dated, key=lambda item: item[0])[1]


def _new_run_activity_grace(
    *,
    status: Mapping[str, Any] | None,
    runtime_facts: Any,
    artifact_delta_at: str | None,
    runtime_supervision_payload: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    active_run_id = _non_empty_text(getattr(runtime_facts, "active_run_id", None))
    if active_run_id is None:
        return None
    observed_text = _latest_runtime_observed_at(
        status=status,
        runtime_supervision_payload=runtime_supervision_payload,
    )
    observed_at = _timestamp_value(observed_text)
    if observed_at is None:
        return None
    artifact_at = _timestamp_value(artifact_delta_at)
    if artifact_at is not None and artifact_at >= observed_at:
        return None
    progress_freshness_now = _controller_override("_progress_freshness_now", _progress_freshness_now)
    age_seconds = max(0, int((progress_freshness_now() - observed_at).total_seconds()))
    if age_seconds > _NEW_RUN_ACTIVITY_GRACE_SECONDS:
        return None
    return {
        "state": "new_run_grace",
        "active_run_id": active_run_id,
        "observed_at": observed_at.isoformat(),
        "artifact_delta_at": artifact_at.isoformat() if artifact_at is not None else None,
        "grace_after_seconds": _NEW_RUN_ACTIVITY_GRACE_SECONDS,
        "seconds_since_observed": age_seconds,
    }


def _split_progress_freshness(
    *,
    progress_freshness: dict[str, Any],
    status: dict[str, Any],
    supervisor_tick_audit: dict[str, Any],
    autonomy_slo_status: dict[str, Any] | None,
    runtime_facts: Any,
    runtime_supervision_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    supervisor_status = _non_empty_text(supervisor_tick_audit.get("status"))
    supervisor_tick = {
        "status": supervisor_status or "missing",
        "required": bool(supervisor_tick_audit.get("required")),
        "summary": _non_empty_text(supervisor_tick_audit.get("summary")),
        "latest_progress_at": _non_empty_text(supervisor_tick_audit.get("latest_recorded_at")),
        "latest_progress_source": "supervisor_tick_audit",
    }
    if supervisor_tick["latest_progress_at"] is None:
        supervisor_tick["latest_progress_at"] = _non_empty_text((runtime_supervision_payload or {}).get("recorded_at"))
        if supervisor_tick["latest_progress_at"] is not None:
            supervisor_tick["latest_progress_source"] = "runtime_supervision"
    if supervisor_tick["latest_progress_at"] is not None:
        supervisor_tick.update(
            _freshness_from_timestamp(
                timestamp=supervisor_tick["latest_progress_at"],
                source=supervisor_tick["latest_progress_source"],
                summary=supervisor_tick["summary"],
            )
        )
        if supervisor_status in {"missing", "stale", "invalid"}:
            supervisor_tick["status"] = supervisor_status

    if runtime_facts.strict_live:
        worker_liveness = {
            "status": "fresh",
            "required": True,
            "summary": "worker has a live active_run_id.",
            "active_run_id": runtime_facts.active_run_id,
            "worker_running": runtime_facts.worker_running,
            "runtime_liveness_status": runtime_facts.runtime_liveness_status,
        }
    elif runtime_facts.worker_running is True and runtime_facts.active_run_id is None:
        worker_liveness = {
            "status": "invalid",
            "required": True,
            "summary": "worker_running=true without active_run_id is invalid liveness.",
            "active_run_id": None,
            "worker_running": True,
            "runtime_liveness_status": runtime_facts.runtime_liveness_status,
        }
    elif runtime_facts.recovery_pending or runtime_facts.missing_live_session:
        worker_liveness = {
            "status": "recovering",
            "required": True,
            "summary": "worker liveness is missing and runtime recovery is pending.",
            "active_run_id": runtime_facts.active_run_id,
            "worker_running": runtime_facts.worker_running,
            "runtime_liveness_status": runtime_facts.runtime_liveness_status,
        }
    else:
        worker_liveness = {
            "status": "missing",
            "required": True,
            "summary": "no strict live worker liveness signal is present.",
            "active_run_id": runtime_facts.active_run_id,
            "worker_running": runtime_facts.worker_running,
            "runtime_liveness_status": runtime_facts.runtime_liveness_status,
        }

    markers = _mapping_copy((autonomy_slo_status or {}).get("mds_progress_markers"))
    artifact_delta_at = _non_empty_text(markers.get("meaningful_artifact_delta_at"))
    artifact_delta_freshness = _freshness_from_timestamp(
        timestamp=artifact_delta_at,
        source="mds_artifact_delta",
        summary=_non_empty_text(markers.get("meaningful_artifact_delta_kind"))
        or _non_empty_text(markers.get("turn_progress_kind")),
    )
    breach_types = {
        text
        for item in (autonomy_slo_status or {}).get("breach_types") or []
        if (text := _non_empty_text(item)) is not None
    }
    activity_timeout = {
        "state": "ok",
        "required": bool(runtime_facts.strict_live),
        "summary": "live worker is within the meaningful artifact delta activity window.",
        "active_run_id": runtime_facts.active_run_id,
        "timeout_after_seconds": artifact_delta_freshness.get("stale_after_seconds"),
        "seconds_without_artifact_delta": artifact_delta_freshness.get("seconds_since_latest_progress"),
        "breach_types": sorted(breach_types),
    }
    new_run_grace = _new_run_activity_grace(
        status=status,
        runtime_facts=runtime_facts,
        artifact_delta_at=artifact_delta_at,
        runtime_supervision_payload=runtime_supervision_payload,
    )
    if (
        runtime_facts.strict_live
        and artifact_delta_freshness["status"] in {"missing", "stale"}
        and new_run_grace is not None
    ):
        activity_timeout["state"] = "watching_new_run"
        activity_timeout["summary"] = (
            "live worker was observed on a newer run than the last meaningful artifact delta; "
            "wait within the new-run grace window before classifying activity timeout."
        )
        activity_timeout["new_run_grace"] = new_run_grace
    elif runtime_facts.strict_live and artifact_delta_freshness["status"] in {"missing", "stale"}:
        activity_timeout["state"] = "timed_out"
        activity_timeout["summary"] = (
            "live worker has exceeded the meaningful artifact delta activity window; "
            "supervisor ticks alone cannot prove paper progress."
        )
    elif runtime_facts.strict_live and breach_types & _ACTIVITY_TIMEOUT_REASONS:
        activity_timeout["state"] = "at_risk"
        activity_timeout["summary"] = (
            "live worker has autonomy SLO churn signals and must produce artifact delta before closeout."
        )

    updated = dict(progress_freshness)
    updated["supervisor_tick_freshness"] = supervisor_tick
    updated["worker_liveness_freshness"] = worker_liveness
    updated["meaningful_artifact_delta_freshness"] = artifact_delta_freshness
    updated["activity_timeout"] = activity_timeout
    base_summary = _non_empty_text(updated.get("summary"))
    if worker_liveness["status"] in {"invalid", "recovering"}:
        updated["status"] = "stale"
        detail_summary = "监管心跳不能单独证明论文推进；worker liveness 或 artifact delta 需要恢复。"
        updated["summary"] = f"{base_summary} {detail_summary}" if base_summary else detail_summary
    elif activity_timeout["state"] == "timed_out":
        updated["status"] = "stale"
        detail_summary = "live worker 已超过 meaningful artifact delta 活动窗口，必须先恢复产物增量或写出平台修复终态。"
        updated["summary"] = f"{base_summary} {detail_summary}" if base_summary else detail_summary
    elif artifact_delta_freshness["status"] == "stale":
        updated["status"] = "stale"
        detail_summary = "最近监管可能新鲜，但 meaningful artifact delta 已过期。"
        updated["summary"] = f"{base_summary} {detail_summary}" if base_summary else detail_summary
    updated["canonical_progress_sources"] = [
        "worker_liveness_freshness",
        "meaningful_artifact_delta_freshness",
    ]
    return updated
