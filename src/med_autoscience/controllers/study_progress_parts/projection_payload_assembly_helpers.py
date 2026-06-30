from __future__ import annotations

from typing import Any, Mapping

from .shared import _mapping_copy, _non_empty_text


def active_run_id_with_live_handoff(
    active_run_id: str | None,
    *,
    handoff: Mapping[str, Any],
) -> str | None:
    if _handoff_has_strict_live_provider_attempt(handoff):
        return _non_empty_text(handoff.get("active_run_id")) or active_run_id
    if active_run_id is None:
        observed = _observed_stage_attempt_active_run_id(handoff)
        if observed is not None:
            return observed
    if _handoff_disproves_active_run_id(handoff, active_run_id):
        return None
    return active_run_id


def runtime_refs_with_live_handoff(
    refs: Mapping[str, Any],
    *,
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(refs)
    if _handoff_disproves_active_run_id(handoff, _non_empty_text(result.get("active_run_id"))):
        result["stale_active_run_id"] = result.get("active_run_id")
        result["active_run_id"] = None
        result["active_run_id_source"] = "invalidated_no_running_provider_attempt"
        result["strict_live"] = False
    if not _handoff_has_strict_live_provider_attempt(handoff):
        return result
    active_run_id = active_run_id_with_live_handoff(
        _non_empty_text(result.get("active_run_id")),
        handoff=handoff,
    )
    if active_run_id is None:
        return result
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    result.update(
        {
            "active_run_id": active_run_id,
            "active_run_id_source": "opl_current_control_state_handoff.active_run_id",
            "runtime_liveness_status": _non_empty_text(runtime_health.get("runtime_liveness_status"))
            or _non_empty_text(runtime_health.get("health_status"))
            or "live",
            "worker_running": True,
            "strict_live": True,
            "missing_live_session": False,
            "recovery_pending": False,
        }
    )
    return result


def _observed_stage_attempt_active_run_id(handoff: Mapping[str, Any]) -> str | None:
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    candidate = (
        _non_empty_text(handoff.get("active_run_id"))
        or _non_empty_text(runtime_health.get("last_known_run_id"))
    )
    if candidate is None or not candidate.startswith("opl-stage-attempt://"):
        return None
    return candidate


def _handoff_disproves_active_run_id(
    handoff: Mapping[str, Any],
    active_run_id: str | None,
) -> bool:
    if active_run_id is None:
        return False
    if not active_run_id.startswith("opl-stage-attempt://"):
        return False
    if handoff.get("running_provider_attempt") is True:
        return False
    if not handoff:
        return False
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    if not runtime_health:
        return False
    runtime_liveness_status = _non_empty_text(runtime_health.get("runtime_liveness_status"))
    health_status = _non_empty_text(runtime_health.get("health_status"))
    return not (
        runtime_liveness_status in {
            "attempt_running",
            "provider_admitted",
            "running",
            "live",
        }
        or health_status in {
            "attempt_running",
            "provider_admitted",
            "running",
            "live",
        }
    )


def _handoff_has_strict_live_provider_attempt(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is not True:
        return False
    if _handoff_has_matching_terminal_closeout(handoff):
        return False
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    runtime_liveness_status = _non_empty_text(runtime_health.get("runtime_liveness_status"))
    health_status = _non_empty_text(runtime_health.get("health_status"))
    return runtime_liveness_status in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    } or health_status in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    }


def _handoff_has_matching_terminal_closeout(handoff: Mapping[str, Any]) -> bool:
    terminal = _mapping_copy(handoff.get("latest_terminal_stage_log"))
    if not terminal:
        return False
    active_attempt_id = _handoff_stage_attempt_id(handoff)
    terminal_attempt_id = _non_empty_text(terminal.get("stage_attempt_id"))
    if active_attempt_id is not None and terminal_attempt_id != active_attempt_id:
        return False
    if active_attempt_id is None and terminal_attempt_id is None:
        return False
    status = _non_empty_text(terminal.get("status"))
    if status in {
        "blocked",
        "closed",
        "closed_with_domain_owner_refs",
        "completed",
        "failed",
        "terminal",
        "typed_blocked",
    }:
        return True
    return (
        _non_empty_text(terminal.get("source_path")) is not None
        and _non_empty_text(terminal.get("record_path")) is not None
    )


def _handoff_stage_attempt_id(handoff: Mapping[str, Any]) -> str | None:
    if text := _non_empty_text(handoff.get("active_stage_attempt_id")):
        return text
    active_run_id = _non_empty_text(handoff.get("active_run_id"))
    prefix = "opl-stage-attempt://"
    if active_run_id is not None and active_run_id.startswith(prefix):
        attempt_id = active_run_id[len(prefix) :].strip()
        return attempt_id or None
    return None
