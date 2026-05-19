from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


SURFACE_KIND = "mas_production_blocker_impact_projection"
AUTHORITY = {
    "kind": "read_model_projection",
    "writes_authority_surface": False,
    "writes_study_truth": False,
    "writes_runtime_truth": False,
    "writes_publication_truth": False,
    "writes_controller_decisions": False,
    "writes_paper_package": False,
}


def build_production_blocker_impact_projection(
    progress: Mapping[str, Any] | None = None,
    runtime: Mapping[str, Any] | None = None,
    *,
    study_id: str | None = None,
) -> dict[str, Any]:
    progress_payload = _mapping(progress)
    runtime_payload = _mapping(runtime)
    runtime_session = _runtime_session(progress_payload, runtime_payload)
    recovery_intent = _recovery_intent(progress_payload, runtime_payload)
    trigger = _first_mapping(progress_payload.get("runtime_reconcile_trigger"), runtime_payload.get("runtime_reconcile_trigger"))
    owner_route = _owner_route(progress_payload, runtime_payload)
    stall = _paper_progress_stall(progress_payload, runtime_payload)
    route = _route_projection(owner_route, recovery_intent=recovery_intent, trigger=trigger)
    same_fingerprint_or_handoff = _same_fingerprint_or_handoff(
        stall=stall,
        route=route,
        trigger=trigger,
        progress=progress_payload,
        runtime=runtime_payload,
    )
    source_refs = _source_refs(
        runtime_session,
        recovery_intent,
        trigger,
        owner_route,
        stall,
        progress_payload.get("refs"),
        runtime_payload.get("refs"),
    )
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": 1,
        "study_id": _text(study_id) or _text(progress_payload.get("study_id")) or _text(runtime_payload.get("study_id")),
        "affects_output": _affects_output(
            runtime_session=runtime_session,
            recovery_intent=recovery_intent,
            trigger=trigger,
            stall=stall,
            progress=progress_payload,
            runtime=runtime_payload,
        ),
        "next_owner": _first_text(
            recovery_intent.get("next_owner"),
            route.get("next_owner"),
            owner_route.get("next_owner"),
            _mapping(progress_payload.get("control_plane_snapshot")).get("canonical_next_action_owner"),
        ),
        "why_not_running": _why_not_running(
            stall=stall,
            runtime_session=runtime_session,
            recovery_intent=recovery_intent,
            progress=progress_payload,
            runtime=runtime_payload,
        ),
        "same_fingerprint_or_handoff": same_fingerprint_or_handoff,
        "will_start_llm": _first_bool(trigger.get("will_start_llm"), runtime_session.get("will_start_llm")),
        "safe_reconcile_command": _safe_reconcile_command(trigger),
        "route": route,
        "source_refs": source_refs,
        "authority": dict(AUTHORITY),
    }


def _runtime_session(progress: Mapping[str, Any], runtime: Mapping[str, Any]) -> dict[str, Any]:
    continuity = _mapping(progress.get("runtime_continuity")) or _mapping(runtime.get("runtime_continuity"))
    return _first_mapping(
        progress.get("runtime_session"),
        runtime.get("runtime_session"),
        continuity.get("runtime_session"),
    )


def _recovery_intent(progress: Mapping[str, Any], runtime: Mapping[str, Any]) -> dict[str, Any]:
    continuity = _mapping(progress.get("runtime_continuity")) or _mapping(runtime.get("runtime_continuity"))
    return _first_mapping(
        progress.get("recovery_intent"),
        runtime.get("recovery_intent"),
        continuity.get("recovery_intent"),
    )


def _owner_route(progress: Mapping[str, Any], runtime: Mapping[str, Any]) -> dict[str, Any]:
    control = _mapping(progress.get("control_plane_snapshot")) or _mapping(runtime.get("control_plane_snapshot"))
    route_authorization = _mapping(control.get("route_authorization"))
    return _first_mapping(
        progress.get("owner_route"),
        runtime.get("owner_route"),
        route_authorization.get("owner_route"),
    )


def _paper_progress_stall(progress: Mapping[str, Any], runtime: Mapping[str, Any]) -> dict[str, Any]:
    generated = _mapping(progress.get("paper_progress_stall"))
    source = _mapping(runtime.get("paper_progress_stall"))
    if not generated:
        return source
    if not source:
        return generated
    merged = dict(generated)
    for key in ("why_not_running", "same_fingerprint_or_handoff", "handoff_state", "summary"):
        if source.get(key) is not None:
            merged[key] = source.get(key)
    source_refs = _source_refs(generated.get("source_refs"), source.get("source_refs"))
    if source_refs:
        merged["source_refs"] = source_refs
    return merged


def _route_projection(
    owner_route: Mapping[str, Any],
    *,
    recovery_intent: Mapping[str, Any],
    trigger: Mapping[str, Any],
) -> dict[str, Any]:
    keys = (
        "study_id",
        "quest_id",
        "route_epoch",
        "truth_epoch",
        "runtime_health_epoch",
        "trace_id",
        "idempotency_key",
        "current_owner",
        "next_owner",
        "owner_reason",
        "failure_signature",
        "source_fingerprint",
        "work_unit_fingerprint",
        "allowed_actions",
    )
    route = {key: owner_route.get(key) for key in keys if owner_route.get(key) is not None}
    route.setdefault("next_owner", _text(recovery_intent.get("next_owner")))
    route.setdefault("source_fingerprint", _first_text(owner_route.get("source_fingerprint"), trigger.get("dedupe_fingerprint")))
    route.setdefault(
        "work_unit_fingerprint",
        _first_text(owner_route.get("work_unit_fingerprint"), trigger.get("dedupe_fingerprint")),
    )
    route_refs = _source_refs(owner_route.get("source_refs"))
    if route_refs:
        route["source_refs"] = route_refs
    return {key: value for key, value in route.items() if value is not None}


def _affects_output(
    *,
    runtime_session: Mapping[str, Any],
    recovery_intent: Mapping[str, Any],
    trigger: Mapping[str, Any],
    stall: Mapping[str, Any],
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> bool:
    if stall:
        return True
    if trigger.get("safe_to_request") is True:
        return True
    if _text(recovery_intent.get("current_action")):
        return True
    if _text(runtime_session.get("freshness_state")) in {"stale", "missing"}:
        return True
    if _text(runtime_session.get("worker_state")) in {"stale", "degraded", "missing", "stopped"}:
        return True
    if runtime_session.get("worker_running") is False:
        return True
    if _blocking_reasons(progress, runtime):
        return True
    if _text(runtime.get("worker_state")) in {"stale", "degraded", "missing", "stopped"}:
        return True
    return _text(progress.get("current_stage")) in {
        "managed_runtime_recovering",
        "managed_runtime_degraded",
        "managed_runtime_escalated",
        "runtime_blocked",
    }


def _why_not_running(
    *,
    stall: Mapping[str, Any],
    runtime_session: Mapping[str, Any],
    recovery_intent: Mapping[str, Any],
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> str | None:
    return _first_text(
        stall.get("why_not_running"),
        stall.get("summary"),
        runtime_session.get("stale_reason"),
        recovery_intent.get("reason"),
        progress.get("runtime_reason"),
        runtime.get("reason"),
        *(_blocking_reasons(progress, runtime)[:1]),
    )


def _same_fingerprint_or_handoff(
    *,
    stall: Mapping[str, Any],
    route: Mapping[str, Any],
    trigger: Mapping[str, Any],
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> str | None:
    explicit = _first_text(stall.get("same_fingerprint_or_handoff"), stall.get("handoff_state"))
    if explicit is not None:
        return explicit
    trigger_fingerprint = _text(trigger.get("dedupe_fingerprint"))
    route_fingerprints = {
        _text(route.get("source_fingerprint")),
        _text(route.get("work_unit_fingerprint")),
    }
    route_fingerprints.discard(None)
    if trigger_fingerprint and trigger_fingerprint in route_fingerprints:
        return "same_fingerprint"
    if "same_fingerprint_loop" in set(_blocking_reasons(progress, runtime)):
        return "same_fingerprint"
    if _text(progress.get("parked_state")) or _text(runtime.get("parked_state")):
        return "handoff"
    return None


def _safe_reconcile_command(trigger: Mapping[str, Any]) -> str | None:
    if trigger.get("safe_to_request") is False:
        return None
    return _first_text(
        trigger.get("recommended_command"),
        trigger.get("canonical_one_shot_reconcile_domain_routes_command"),
    )


def _blocking_reasons(progress: Mapping[str, Any], runtime: Mapping[str, Any]) -> list[str]:
    health = _mapping(progress.get("runtime_health_snapshot")) or _mapping(runtime.get("runtime_health_snapshot"))
    control = _mapping(progress.get("control_plane_snapshot")) or _mapping(runtime.get("control_plane_snapshot"))
    return list(
        dict.fromkeys(
            [
                *_string_list(progress.get("current_blockers")),
                *_string_list(runtime.get("blocking_reasons")),
                *_string_list(health.get("blocking_reasons")),
                *_string_list(control.get("blocking_reasons")),
            ]
        )
    )


def _source_refs(*values: object) -> list[str]:
    refs: list[str] = []
    for value in values:
        refs.extend(_refs_from_value(value))
    return list(dict.fromkeys(refs))


def _refs_from_value(value: object) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, Mapping):
        refs: list[str] = []
        for key, item in value.items():
            if str(key).endswith("_refs") or str(key).endswith("_ref") or key in {"source_refs", "refs", "path"}:
                refs.extend(_refs_from_value(item))
            elif isinstance(item, Mapping | list | tuple):
                refs.extend(_refs_from_value(item))
        return refs
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        refs: list[str] = []
        for item in value:
            refs.extend(_refs_from_value(item))
        return refs
    return []


def _first_mapping(*values: object) -> dict[str, Any]:
    for value in values:
        mapping = _mapping(value)
        if mapping:
            return mapping
    return {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _first_bool(*values: object) -> bool | None:
    for value in values:
        if isinstance(value, bool):
            return value
    return None


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, Iterable) or isinstance(value, (bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None:
            result.append(text)
    return result


__all__ = ["SURFACE_KIND", "build_production_blocker_impact_projection"]
