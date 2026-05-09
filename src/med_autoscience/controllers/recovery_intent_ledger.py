from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.runtime_control import owner_route as owner_route_part


ALLOWED_CURRENT_ACTIONS = frozenset(
    {
        "await_next_tick",
        "safe_reconcile_ready",
        "recovering",
        "parked",
        "human_gate_required",
        "escalated",
    }
)
SURFACE = "runtime_recovery_intent"
SCHEMA_VERSION = 1
RECOVERY_INTENT_RELATIVE_PATH = Path("artifacts/runtime/recovery_intent/latest.json")
RECOVERY_INTENT_HISTORY_RELATIVE_PATH = Path("artifacts/runtime/recovery_intent/history.jsonl")
_RUNTIME_REDRIVE_ACTIONS = frozenset({"runtime_platform_repair"})
_RETRY_EXHAUSTED_REDRIVE_REASONS = frozenset(
    {
        "abnormal_stopped_runtime_resume_required",
        "failed_quest_runtime_relaunch_required",
        "runtime_controller_redrive_required",
    }
)
_PUBLICATION_GATE_REASONS = frozenset(
    {
        "publication_gate_specificity_required",
        "publication_gate_missing",
    }
)


def project_recovery_intent(
    *,
    study_id: str,
    quest_id: str | None,
    study_root: Path,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    action_queue: Iterable[Mapping[str, Any]],
    generated_at: str,
    persist: bool = False,
) -> dict[str, Any]:
    normalized_route = owner_route_part.ensure_owner_route_v2(_mapping(owner_route))
    actions = [dict(action) for action in action_queue if isinstance(action, Mapping)]
    latest_path = latest_path_for_study(study_root)
    previous = _read_json_object(latest_path)
    block = _fail_closed_block(
        status=status,
        progress=progress,
        owner_route=normalized_route,
        actions=actions,
    )
    if block is None:
        reason = _text(normalized_route.get("owner_reason")) or "awaiting_runtime_recovery_intent"
        current_action = _ready_current_action(status=status, actions=actions)
        last_result = None
    else:
        reason = block["reason"]
        current_action = block["current_action"]
        last_result = {
            "dispatch_status": "blocked",
            "reason": reason,
            "source": SURFACE,
        }
    intent = {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "quest_id": quest_id,
        "generated_at": generated_at,
        "reason": reason,
        "next_owner": _text(normalized_route.get("next_owner")),
        "retry_budget": _retry_budget(status, progress),
        "dedupe_fingerprint": _dedupe_fingerprint(normalized_route, actions),
        "last_attempt": _mapping(previous).get("last_attempt") if previous is not None else None,
        "last_result": last_result if last_result is not None else _mapping(previous).get("last_result"),
        "next_eligible_tick": generated_at if current_action == "safe_reconcile_ready" else None,
        "current_action": current_action,
        "evidence_refs": _evidence_refs(
            study_root=study_root,
            owner_route=normalized_route,
            status=status,
            progress=progress,
            actions=actions,
        ),
        "quality_ready_authorized": False,
        "publication_ready_authorized": False,
        "submission_ready_authorized": False,
    }
    _assert_current_action(intent["current_action"])
    if persist:
        _write_json(latest_path, intent)
        _append_json_line(history_path_for_study(study_root), intent)
    return intent


def latest_path_for_study(study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / RECOVERY_INTENT_RELATIVE_PATH


def history_path_for_study(study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / RECOVERY_INTENT_HISTORY_RELATIVE_PATH


def _fail_closed_block(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    actions: list[dict[str, Any]],
) -> dict[str, str] | None:
    if _completed(status, progress):
        return {"reason": "completed", "current_action": "parked"}
    if _manual_parked(status, progress):
        return {"reason": "manual_parked", "current_action": "parked"}
    if _human_gate_required(status, progress):
        return {"reason": "human_gate_required", "current_action": "human_gate_required"}
    redrive_actions = [action for action in actions if _text(action.get("action_type")) in _RUNTIME_REDRIVE_ACTIONS]
    for action in redrive_actions:
        if not _route_identity_matches(dispatch=action, current_route=owner_route):
            return {"reason": "owner_route_stale", "current_action": "parked"}
        if not owner_route_part.route_allows_action(action=action, owner_route=owner_route):
            return {"reason": "owner_route_mismatch", "current_action": "parked"}
        if not owner_route_part.owner_route_matches(dispatch=action, current_route=owner_route):
            return {"reason": "owner_route_mismatch", "current_action": "parked"}
    if _publication_gate_missing(status, progress, owner_route, actions):
        return {"reason": "publication_gate_missing", "current_action": "human_gate_required"}
    if _retry_exhausted(status, progress) and not _has_bounded_retry_exhausted_redrive(redrive_actions):
        return {"reason": "retry_exhausted", "current_action": "escalated"}
    if _external_supervisor_without_dispatch(owner_route, actions):
        return {
            "reason": _text(owner_route.get("owner_reason")) or "external_supervisor_required",
            "current_action": "escalated",
        }
    if not redrive_actions:
        return {"reason": "awaiting_fresh_owner_route", "current_action": "await_next_tick"}
    return None


def _ready_current_action(*, status: Mapping[str, Any], actions: list[dict[str, Any]]) -> str:
    if any(_text(action.get("action_type")) in _RUNTIME_REDRIVE_ACTIONS for action in actions):
        return "safe_reconcile_ready"
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    if _text(runtime_health.get("attempt_state")) in {"recovering", "retrying", "probing", "relaunching"}:
        return "recovering"
    return "await_next_tick"


def _completed(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _text(status.get("decision")) == "completed":
        return True
    if _text(status.get("quest_status")) != "completed":
        return False
    contract = _mapping(status.get("study_completion_contract")) or _mapping(progress.get("study_completion_contract"))
    return not contract or contract.get("ready") is True or _text(contract.get("status")) == "resolved"


def _manual_parked(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _failed_non_resumable_auto_redrive(status, progress):
        return False
    macro_state = _mapping(status.get("study_macro_state")) or _mapping(progress.get("study_macro_state"))
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    parked_state = _text(auto_parked.get("parked_state"))
    reason = _text(status.get("reason"))
    return bool(
        (_text(macro_state.get("writer_state")) == "parked" and _text(macro_state.get("reason")) == "user_stop")
        or parked_state in {"manual_hold", "explicit_resume_pending"}
        or _text(runtime_health.get("canonical_runtime_action")) == "await_explicit_resume"
        or reason == "quest_waiting_for_explicit_wakeup_after_manual_hold"
    )


def _failed_non_resumable_auto_redrive(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _text(status.get("quest_status")) != "failed":
        return False
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    observed_state = _mapping(runtime_health.get("observed_quest_state"))
    continuation_state = _mapping(status.get("continuation_state")) or _mapping(progress.get("continuation_state"))
    policy = _text(continuation_state.get("continuation_policy"))
    if policy in {"wait_for_user_or_resume", "manual", "manual_hold"}:
        return False
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    failure = _mapping(auto_parked.get("runtime_failure_classification"))
    if failure.get("requires_human_gate") is True or failure.get("external_blocker") is True:
        return False
    return bool(
        _text(status.get("reason")) == "quest_exists_with_non_resumable_state"
        or _text(observed_state.get("reason")) == "quest_exists_with_non_resumable_state"
    )


def _human_gate_required(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _mapping(status.get("execution_owner_guard")).get("supervisor_only") is True:
        return True
    control_plane = _mapping(status.get("control_plane_snapshot")) or _mapping(progress.get("control_plane_snapshot"))
    if control_plane.get("human_gate_required") is True:
        return True
    if status.get("requires_human_confirmation") is True:
        return True
    return "execution_owner_guard.supervisor_only" in set(_string_items(status.get("blocking_reasons")))


def _publication_gate_missing(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    actions: list[dict[str, Any]],
) -> bool:
    reasons = {
        _text(status.get("reason")),
        *(_text(action.get("reason")) for action in actions),
        *_string_items(status.get("blocking_reasons")),
        *_string_items(progress.get("current_blockers")),
    }
    reasons.discard(None)
    return bool(reasons & _PUBLICATION_GATE_REASONS)


def _retry_exhausted(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _has_live_worker(status, progress):
        return False
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    reasons = {
        *_string_items(status.get("blocking_reasons")),
        *_string_items(runtime_health.get("blocking_reasons")),
        *_string_items(_mapping(status.get("control_plane_snapshot")).get("blocking_reasons")),
        *_string_items(_mapping(progress.get("control_plane_snapshot")).get("blocking_reasons")),
    }
    return bool(
        "runtime_recovery_retry_budget_exhausted" in reasons
        or _text(status.get("reason")) == "runtime_recovery_retry_budget_exhausted"
        or _text(runtime_health.get("attempt_state")) == "escalated"
        or runtime_health.get("retry_budget_remaining") == 0
    )


def _has_live_worker(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _text(status.get("active_run_id")) or _text(progress.get("active_run_id")):
        return True
    supervision = _mapping(progress.get("supervision"))
    if _text(supervision.get("active_run_id")):
        return True
    liveness = _mapping(status.get("runtime_liveness_audit"))
    runtime_audit = _mapping(liveness.get("runtime_audit"))
    if _text(liveness.get("active_run_id")) or _text(runtime_audit.get("active_run_id")):
        return True
    return runtime_audit.get("worker_running") is True or liveness.get("worker_running") is True


def _retry_budget(status: Mapping[str, Any], progress: Mapping[str, Any]) -> dict[str, Any]:
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    remaining = runtime_health.get("retry_budget_remaining")
    if not isinstance(remaining, int):
        remaining = None
    return {
        "remaining": remaining,
        "exhausted": bool(remaining == 0 or _retry_exhausted(status, progress)),
    }


def _has_bounded_retry_exhausted_redrive(actions: list[dict[str, Any]]) -> bool:
    for action in actions:
        if _text(action.get("action_type")) not in _RUNTIME_REDRIVE_ACTIONS:
            continue
        if _text(action.get("reason")) in _RETRY_EXHAUSTED_REDRIVE_REASONS:
            return True
    return False


def _external_supervisor_without_dispatch(owner_route: Mapping[str, Any], actions: list[dict[str, Any]]) -> bool:
    if _text(owner_route.get("next_owner")) != "external_supervisor":
        return False
    if actions:
        return False
    return _text(owner_route.get("owner_reason")) is not None


def _dedupe_fingerprint(owner_route: Mapping[str, Any], actions: list[dict[str, Any]]) -> str | None:
    if text := _text(owner_route.get("idempotency_key")):
        return text
    for action in actions:
        if text := _text(action.get("action_id")):
            return text
    return _text(owner_route.get("source_fingerprint"))


def _route_identity_matches(*, dispatch: Mapping[str, Any], current_route: Mapping[str, Any]) -> bool:
    dispatch_route = owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_route))
    if not dispatch_route or not route:
        return False
    return (
        _text(dispatch_route.get("idempotency_key")) == _text(route.get("idempotency_key"))
        and _text(dispatch_route.get("route_epoch")) == _text(route.get("route_epoch"))
        and _text(dispatch_route.get("source_fingerprint")) == _text(route.get("source_fingerprint"))
    )


def _evidence_refs(
    *,
    study_root: Path,
    owner_route: Mapping[str, Any],
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[dict[str, Any]],
) -> dict[str, Any]:
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    refs = _mapping(progress.get("refs"))
    return {
        "owner_route_trace_id": _text(owner_route.get("trace_id")),
        "owner_route_idempotency_key": _text(owner_route.get("idempotency_key")),
        "runtime_health_epoch": _text(runtime_health.get("runtime_health_epoch")),
        "publication_eval_path": _text(refs.get("publication_eval_path"))
        or str(Path(study_root).expanduser().resolve() / "artifacts" / "publication_eval" / "latest.json"),
        "controller_decision_path": str(
            Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
        ),
        "action_ids": [_text(action.get("action_id")) for action in actions if _text(action.get("action_id")) is not None],
    }


def _assert_current_action(value: object) -> None:
    if _text(value) not in ALLOWED_CURRENT_ACTIONS:
        raise ValueError(f"unsupported recovery intent current_action: {value!r}")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, Iterable) or isinstance(value, Mapping | bytes):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ALLOWED_CURRENT_ACTIONS",
    "RECOVERY_INTENT_HISTORY_RELATIVE_PATH",
    "RECOVERY_INTENT_RELATIVE_PATH",
    "latest_path_for_study",
    "history_path_for_study",
    "project_recovery_intent",
]
