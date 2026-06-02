from __future__ import annotations

from datetime import datetime
from pathlib import Path
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


def _freshest_freshness(*freshnesses: dict[str, Any]) -> dict[str, Any]:
    present = [
        item
        for item in freshnesses
        if _timestamp_value(item.get("latest_progress_at")) is not None
    ]
    if not present:
        return freshnesses[0] if freshnesses else {}
    return max(
        present,
        key=lambda item: _timestamp_value(item.get("latest_progress_at")) or datetime.min,
    )


def _timestamp_value(value: object) -> datetime | None:
    normalized = _normalize_timestamp(value)
    if normalized is None:
        return None
    return datetime.fromisoformat(normalized)


def _gate_clearing_artifact_delta_freshness(
    *,
    gate_clearing_batch_payload: Mapping[str, Any] | None,
    publication_eval_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(gate_clearing_batch_payload, Mapping):
        return _freshness_from_timestamp(
            timestamp=None,
            source="gate_clearing_batch",
            summary=None,
        )
    if not _same_publication_eval(
        gate_clearing_batch_payload=gate_clearing_batch_payload,
        publication_eval_payload=publication_eval_payload,
    ):
        return _freshness_from_timestamp(
            timestamp=None,
            source="gate_clearing_batch",
            summary=None,
        )
    if _non_empty_text(gate_clearing_batch_payload.get("status")) != "executed":
        return _freshness_from_timestamp(
            timestamp=None,
            source="gate_clearing_batch",
            summary=None,
        )

    changed_paths = _paper_artifact_delta_paths(gate_clearing_batch_payload)
    if not changed_paths:
        return _freshness_from_timestamp(
            timestamp=None,
            source="gate_clearing_batch",
            summary=None,
        )
    display_count = sum(1 for path in changed_paths if "/paper/figures/" in path or "/paper/tables/" in path)
    summary = (
        "controller-owned gate-clearing batch updated "
        f"{len(changed_paths)} paper-facing artifact(s)"
    )
    if display_count:
        summary += f", including {display_count} table/figure artifact(s)"
    summary += "."
    freshness = _freshness_from_timestamp(
        timestamp=_gate_clearing_timestamp(gate_clearing_batch_payload),
        source="gate_clearing_batch",
        summary=summary,
    )
    freshness["changed_refs"] = changed_paths
    return freshness


def _runtime_turn_closeout_artifact_delta_freshness(
    *,
    quest_root: Path | None,
) -> dict[str, Any]:
    missing = _freshness_from_timestamp(
        timestamp=None,
        source="runtime_turn_closeout",
        summary=None,
    )
    if quest_root is None:
        return missing
    closeout_root = quest_root / "artifacts" / "runtime" / "turn_closeouts"
    if not closeout_root.is_dir():
        return missing

    candidates: list[tuple[datetime, dict[str, Any], list[str]]] = []
    for path in closeout_root.glob("*.json"):
        payload = _read_json_object(path)
        if payload is None:
            continue
        if _non_empty_text(payload.get("status")) not in {None, "completed"}:
            continue
        if payload.get("meaningful_artifact_delta") is not True:
            continue
        timestamp = _timestamp_value(
            payload.get("completed_at")
            or payload.get("finished_at")
            or payload.get("recorded_at")
            or payload.get("generated_at")
        )
        if timestamp is None:
            continue
        paper_refs = _closeout_paper_artifact_delta_refs(payload)
        if not paper_refs:
            continue
        candidates.append((timestamp, payload, paper_refs))
    if not candidates:
        return missing

    timestamp, _payload, paper_refs = max(candidates, key=lambda item: item[0])
    display_count = sum(1 for ref in paper_refs if "/paper/figures/" in ref or "/paper/tables/" in ref)
    summary = f"runtime turn closeout reported {len(paper_refs)} paper-facing artifact(s)"
    if display_count:
        summary += f", including {display_count} table/figure artifact(s)"
    summary += "."
    freshness = _freshness_from_timestamp(
        timestamp=timestamp.isoformat(),
        source="runtime_turn_closeout",
        summary=summary,
    )
    freshness["changed_refs"] = paper_refs
    return freshness


def _closeout_paper_artifact_delta_refs(closeout_payload: Mapping[str, Any]) -> list[str]:
    refs = closeout_payload.get("artifact_refs")
    if not isinstance(refs, list):
        return []
    paper_refs: list[str] = []
    for ref in refs:
        text = _non_empty_text(ref)
        if text is None:
            continue
        if _canonical_paper_artifact_delta_path(text):
            paper_refs.append(text.replace("\\", "/"))
    return sorted(dict.fromkeys(paper_refs))


def _canonical_paper_artifact_delta_path(path: str) -> bool:
    normalized = path.strip().replace("\\", "/").lstrip("./")
    if not _paper_facing_artifact_path(normalized):
        return False
    parts = tuple(part.lower() for part in normalized.split("/") if part not in {"", "."})
    if "current_package" in parts or "submission_minimal" in parts:
        return False
    if parts and parts[-1] in {"current_package.zip", "current_package.tar.gz", "delivery_manifest.json"}:
        return False
    return True


def _same_publication_eval(
    *,
    gate_clearing_batch_payload: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any] | None,
) -> bool:
    current_eval_id = _non_empty_text((publication_eval_payload or {}).get("eval_id"))
    source_eval_id = _non_empty_text(gate_clearing_batch_payload.get("source_eval_id"))
    if current_eval_id is not None and source_eval_id is not None:
        return current_eval_id == source_eval_id
    return True


def _paper_artifact_delta_paths(gate_clearing_batch_payload: Mapping[str, Any]) -> list[str]:
    paths: list[str] = []
    for unit in gate_clearing_batch_payload.get("unit_results") or []:
        unit_payload = _mapping_copy(unit)
        if not unit_payload:
            continue
        unit_status = _non_empty_text(unit_payload.get("status"))
        if unit_status not in {"updated", "materialized", "synced", "created"}:
            continue
        result = _mapping_copy(unit_payload.get("result"))
        result_status = _non_empty_text(result.get("status"))
        if result_status is not None and result_status in {
            "authority_route_blocked",
            "failed",
            "missing",
            "skipped_failed_dependency",
        }:
            continue
        for key in ("written_files", "repaired_files", "materialized_files"):
            for path in result.get(key) or []:
                if (text := _non_empty_text(path)) is not None and _paper_facing_artifact_path(text):
                    paths.append(text)
    return sorted(dict.fromkeys(paths))


def _paper_facing_artifact_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith("paper/") or "/paper/" in normalized


def _gate_clearing_timestamp(gate_clearing_batch_payload: Mapping[str, Any]) -> str | None:
    gate_replay_step = _mapping_copy(gate_clearing_batch_payload.get("gate_replay_step"))
    for value in (
        gate_replay_step.get("finished_at"),
        gate_clearing_batch_payload.get("finished_at"),
        gate_clearing_batch_payload.get("generated_at"),
        gate_clearing_batch_payload.get("emitted_at"),
        gate_clearing_batch_payload.get("recorded_at"),
    ):
        if (text := _non_empty_text(value)) is not None:
            return text
    return None


def _latest_runtime_observed_at(
    *,
    status: Mapping[str, Any] | None,
) -> str | None:
    status_payload = _mapping_copy(status)
    stable_run_anchor = _stable_runtime_run_anchor(status_payload)
    if stable_run_anchor is not None:
        return stable_run_anchor
    status_health = _mapping_copy(status_payload.get("runtime_health_snapshot"))
    runtime_health = status_health
    candidates: list[str] = []
    refs = runtime_health.get("dominant_runtime_refs")
    if isinstance(refs, list):
        for item in refs:
            if isinstance(item, dict):
                value = _non_empty_text(item.get("recorded_at"))
                if value is not None:
                    candidates.append(value)
    dated = [
        (parsed, text)
        for text in candidates
        if (parsed := _timestamp_value(text)) is not None
    ]
    if not dated:
        return None
    return max(dated, key=lambda item: item[0])[1]


def _stable_runtime_run_anchor(*payloads: Mapping[str, Any]) -> str | None:
    candidates: list[str] = []
    for payload in payloads:
        candidates.extend(_stable_run_anchor_candidates(payload))
    for candidate in candidates:
        if _timestamp_value(candidate) is not None:
            return candidate
    return None


def _stable_run_anchor_candidates(payload: Mapping[str, Any]) -> list[str]:
    candidates: list[str] = []
    for value in (
        payload.get("started_at"),
        payload.get("run_started_at"),
        payload.get("last_turn_started_at"),
    ):
        text = _non_empty_text(value)
        if text is not None:
            candidates.append(text)
    for watchdog in _worker_watchdog_payloads(payload):
        for key in ("started_at", "run_started_at", "last_output_at"):
            text = _non_empty_text(watchdog.get(key))
            if text is not None:
                candidates.append(text)
    return candidates


def _worker_watchdog_payloads(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []

    def append_watchdog(value: object) -> None:
        watchdog = _mapping_copy(value)
        if watchdog and watchdog not in payloads:
            payloads.append(watchdog)

    append_watchdog(payload.get("worker_watchdog"))
    runtime_audit = _mapping_copy(payload.get("runtime_audit"))
    append_watchdog(runtime_audit.get("worker_watchdog"))
    liveness = _mapping_copy(payload.get("runtime_liveness_audit"))
    append_watchdog(liveness.get("worker_watchdog"))
    liveness_runtime_audit = _mapping_copy(liveness.get("runtime_audit"))
    append_watchdog(liveness_runtime_audit.get("worker_watchdog"))
    runtime_health = _mapping_copy(payload.get("runtime_health_snapshot"))
    append_watchdog(runtime_health.get("worker_watchdog"))
    return payloads


def _new_run_activity_grace(
    *,
    status: Mapping[str, Any] | None,
    runtime_facts: Any,
    artifact_delta_at: str | None,
) -> dict[str, Any] | None:
    active_run_id = _non_empty_text(getattr(runtime_facts, "active_run_id", None))
    if active_run_id is None:
        return None
    observed_text = _latest_runtime_observed_at(
        status=status,
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
    gate_clearing_batch_payload: dict[str, Any] | None,
    publication_eval_payload: dict[str, Any] | None,
    runtime_facts: Any,
    quest_root: Path | None = None,
) -> dict[str, Any]:
    supervisor_status = _non_empty_text(supervisor_tick_audit.get("status"))
    supervisor_tick = {
        "status": supervisor_status or "missing",
        "required": bool(supervisor_tick_audit.get("required")),
        "summary": _non_empty_text(supervisor_tick_audit.get("summary")),
        "latest_progress_at": _non_empty_text(supervisor_tick_audit.get("latest_recorded_at")),
        "latest_progress_source": "supervisor_tick_audit",
    }
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
    gate_artifact_delta_freshness = _gate_clearing_artifact_delta_freshness(
        gate_clearing_batch_payload=gate_clearing_batch_payload,
        publication_eval_payload=publication_eval_payload,
    )
    closeout_artifact_delta_freshness = _runtime_turn_closeout_artifact_delta_freshness(
        quest_root=quest_root,
    )
    artifact_delta_freshness = _freshest_freshness(
        artifact_delta_freshness,
        gate_artifact_delta_freshness,
        closeout_artifact_delta_freshness,
    )
    artifact_delta_at = _non_empty_text(artifact_delta_freshness.get("latest_progress_at"))
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
        activity_timeout["progress_pressure"] = _activity_timeout_progress_pressure()
    elif (
        runtime_facts.strict_live
        and artifact_delta_freshness["status"] != "fresh"
        and breach_types & _ACTIVITY_TIMEOUT_REASONS
    ):
        activity_timeout["state"] = "at_risk"
        activity_timeout["summary"] = (
            "live worker has autonomy SLO churn signals and must produce artifact delta before closeout."
        )
        activity_timeout["progress_pressure"] = _activity_timeout_progress_pressure()

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


def _activity_timeout_progress_pressure() -> dict[str, Any]:
    return {
        "surface": "progress_first_activity_timeout_pressure",
        "status": "advance_now",
        "purpose": "continue_progress",
        "timeout_is_terminal_failure": False,
        "no_progress_is_terminal_failure": False,
        "continuation_required": True,
        "next_owner": "one-person-lab",
        "next_action_type": "continue_or_relaunch",
        "quality_gate_relaxation_allowed": False,
    }
