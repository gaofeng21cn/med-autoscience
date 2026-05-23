from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers import runtime_dispatch_cost


SCHEMA_VERSION = 1
SURFACE_KIND = "paper_progress_stall"
STALL_REASONS = (
    "same_fingerprint_loop",
    "read_churn_without_artifact_delta",
    "stale_truth_surface",
    "runtime_recovery_retry_budget_exhausted",
)
TERMINAL_REASONS = frozenset({"runtime_recovery_retry_budget_exhausted"})
NEW_RUN_GRACE_SUPPRESSED_REASONS = frozenset(
    {
        "same_fingerprint_loop",
        "read_churn_without_artifact_delta",
    }
)
FRESH_ARTIFACT_DELTA_SUPPRESSED_REASONS = frozenset(
    {
        "same_fingerprint_loop",
        "read_churn_without_artifact_delta",
    }
)


def build_paper_progress_stall_read_model(
    *,
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any] | None = None,
    owner_route: Mapping[str, Any] | None = None,
    action_queue: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    status = _mapping(status_payload)
    progress = _mapping(progress_payload)
    route = _mapping(owner_route)
    actions = [dict(action) for action in action_queue or [] if isinstance(action, Mapping)]
    reasons = _stall_reasons(status=status, progress=progress)
    terminal = any(reason in TERMINAL_REASONS for reason in reasons)
    action_fingerprint = _action_fingerprint(
        status=status,
        progress=progress,
        owner_route=route,
        actions=actions,
        reasons=reasons,
    )
    action_cost = runtime_dispatch_cost.observe_only_contract(
        reason="paper_progress_stall_read_model",
        action_fingerprint=action_fingerprint,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "stalled": bool(reasons),
        "stall_reasons": reasons,
        "terminal": terminal,
        "safe_reconcile_candidate": bool(reasons) and not terminal,
        "action_fingerprint": action_fingerprint,
        "will_start_llm": False,
        "codex_dispatch_count": 0,
        "action_cost": action_cost,
        "source_refs": {
            "study_id": _text(status.get("study_id")) or _text(progress.get("study_id")),
            "quest_id": _text(status.get("quest_id")) or _text(progress.get("quest_id")),
            "owner_route_idempotency_key": _text(route.get("idempotency_key")),
            "owner_route_work_unit_fingerprint": _text(route.get("work_unit_fingerprint")),
            "runtime_health_epoch": _runtime_health_epoch(status, progress),
            "truth_epoch": _truth_epoch(status, progress),
        },
    }


def stall_reasons(value: Mapping[str, Any] | None) -> list[str]:
    payload = _mapping(value)
    return [reason for reason in _string_items(payload.get("stall_reasons")) if reason in STALL_REASONS]


def terminal(value: Mapping[str, Any] | None) -> bool:
    payload = _mapping(value)
    return bool(payload.get("terminal") is True or set(stall_reasons(payload)) & TERMINAL_REASONS)


def action_fingerprint(value: Mapping[str, Any] | None) -> str | None:
    return _text(_mapping(value).get("action_fingerprint"))


def _stall_reasons(*, status: Mapping[str, Any], progress: Mapping[str, Any]) -> list[str]:
    observed: list[str] = []
    observed.extend(reason for reason in _blocking_reasons(status, progress) if reason in STALL_REASONS)
    observed.extend(reason for reason in _autonomy_breach_types(status, progress) if reason in STALL_REASONS)
    observed.extend(_progress_marker_reasons(status, progress))
    if _truth_surface_stale(status, progress):
        observed.append("stale_truth_surface")
    if _retry_exhausted(status, progress):
        observed.append("runtime_recovery_retry_budget_exhausted")
    reasons = [reason for reason in STALL_REASONS if reason in set(observed)]
    if _watching_new_run_grace(status, progress):
        reasons = [reason for reason in reasons if reason not in NEW_RUN_GRACE_SUPPRESSED_REASONS]
    if _fresh_meaningful_artifact_delta(status, progress):
        reasons = [reason for reason in reasons if reason not in FRESH_ARTIFACT_DELTA_SUPPRESSED_REASONS]
    return reasons


def _blocking_reasons(status: Mapping[str, Any], progress: Mapping[str, Any]) -> list[str]:
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    control_plane = _mapping(status.get("authority_snapshot")) or _mapping(progress.get("authority_snapshot"))
    dispatch_gate = _mapping(control_plane.get("dispatch_gate"))
    return list(
        dict.fromkeys(
            [
                *_string_items(status.get("blocking_reasons")),
                *_string_items(progress.get("current_blockers")),
                *_string_items(runtime_health.get("blocking_reasons")),
                *_string_items(control_plane.get("blocking_reasons")),
                *_string_items(dispatch_gate.get("blocking_reasons")),
                _text(status.get("reason")),
                _text(progress.get("runtime_reason")),
            ]
        )
    )


def _autonomy_breach_types(status: Mapping[str, Any], progress: Mapping[str, Any]) -> list[str]:
    breach_types: list[str] = []
    for payload in (_mapping(status.get("autonomy_slo")), _mapping(progress.get("autonomy_slo"))):
        breach_types.extend(_string_items(payload.get("breach_types")))
    return list(dict.fromkeys(breach_types))


def _progress_marker_reasons(status: Mapping[str, Any], progress: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for payload in (_mapping(status.get("autonomy_slo")), _mapping(progress.get("autonomy_slo"))):
        markers = _mapping(payload.get("mds_progress_markers"))
        if (text := _text(markers.get("turn_progress_kind"))) in STALL_REASONS:
            reasons.append(text)
    for payload in (status, progress):
        freshness = _mapping(_mapping(payload.get("progress_freshness")).get("meaningful_artifact_delta_freshness"))
        if (text := _text(freshness.get("turn_progress_kind"))) in STALL_REASONS:
            reasons.append(text)
    return reasons


def _truth_surface_stale(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    for payload in (_mapping(status.get("study_truth_snapshot")), _mapping(progress.get("study_truth_snapshot"))):
        if _text(payload.get("freshness_state")) == "stale":
            return True
        if _text(payload.get("status")) == "stale":
            return True
    return "stale_truth_surface" in set(_blocking_reasons(status, progress))


def _retry_exhausted(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    reasons = set(_blocking_reasons(status, progress))
    attempt_state = _text(runtime_health.get("attempt_state"))
    canonical_runtime_action = _text(runtime_health.get("canonical_runtime_action"))
    quest_status = _text(status.get("quest_status")) or _text(progress.get("quest_status"))
    zero_budget_in_recovery_context = runtime_health.get("retry_budget_remaining") == 0 and (
        quest_status in {"active", "running"}
        or attempt_state in {"recovering", "retrying", "probing", "relaunching", "escalated"}
        or canonical_runtime_action in {"recover_runtime", "probe_runtime", "relaunch_runtime", "external_supervisor_required"}
    )
    return bool(
        "runtime_recovery_retry_budget_exhausted" in reasons
        or _text(status.get("reason")) == "runtime_recovery_retry_budget_exhausted"
        or attempt_state == "escalated"
        or zero_budget_in_recovery_context
    )


def _watching_new_run_grace(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    active_run_id = _active_run_id(status, progress)
    if active_run_id is None:
        return False
    for payload in (status, progress):
        activity_timeout = _mapping(_mapping(payload.get("progress_freshness")).get("activity_timeout"))
        grace = _mapping(activity_timeout.get("new_run_grace"))
        if _text(activity_timeout.get("state")) != "watching_new_run":
            continue
        if _text(grace.get("state")) != "new_run_grace":
            continue
        if _text(grace.get("active_run_id")) == active_run_id:
            return True
    return False


def _fresh_meaningful_artifact_delta(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    for payload in (status, progress):
        freshness = _mapping(payload.get("progress_freshness"))
        delta = _mapping(freshness.get("meaningful_artifact_delta_freshness"))
        activity_timeout = _mapping(freshness.get("activity_timeout"))
        if _text(delta.get("status")) == "fresh" and _text(activity_timeout.get("state")) == "ok":
            return True
    return False


def _active_run_id(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    for payload in (status, progress):
        if text := _text(payload.get("active_run_id")):
            return text
        supervision = _mapping(payload.get("supervision"))
        if text := _text(supervision.get("active_run_id")):
            return text
        liveness = _mapping(payload.get("runtime_liveness_audit"))
        if text := _text(liveness.get("active_run_id")):
            return text
        runtime_audit = _mapping(liveness.get("runtime_audit"))
        if text := _text(runtime_audit.get("active_run_id")):
            return text
        runtime_health = _mapping(payload.get("runtime_health_snapshot"))
        if text := _text(runtime_health.get("active_run_id")):
            return text
    return None


def _action_fingerprint(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    actions: list[Mapping[str, Any]],
    reasons: list[str],
) -> str:
    payload = {
        "surface_kind": SURFACE_KIND,
        "study_id": _text(status.get("study_id")) or _text(progress.get("study_id")),
        "quest_id": _text(status.get("quest_id")) or _text(progress.get("quest_id")),
        "stall_reasons": reasons,
        "owner_route": {
            "idempotency_key": _text(owner_route.get("idempotency_key")),
            "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
            "source_fingerprint": _text(owner_route.get("source_fingerprint")),
        },
        "actions": [
            {
                "action_type": _text(action.get("action_type")),
                "action_id": _text(action.get("action_id")),
                "work_unit_fingerprint": _text(action.get("work_unit_fingerprint")),
            }
            for action in actions
        ],
        "runtime_health_epoch": _runtime_health_epoch(status, progress),
        "truth_epoch": _truth_epoch(status, progress),
    }
    digest = hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()[:16]
    return f"paper_progress_stall:{digest}"


def _runtime_health_epoch(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    return _text(_mapping(status.get("runtime_health_snapshot")).get("runtime_health_epoch")) or _text(
        _mapping(progress.get("runtime_health_snapshot")).get("runtime_health_epoch")
    )


def _truth_epoch(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    return _text(_mapping(status.get("study_truth_snapshot")).get("truth_epoch")) or _text(
        _mapping(progress.get("study_truth_snapshot")).get("truth_epoch")
    )


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
    "STALL_REASONS",
    "SURFACE_KIND",
    "action_fingerprint",
    "build_paper_progress_stall_read_model",
    "stall_reasons",
    "terminal",
]
