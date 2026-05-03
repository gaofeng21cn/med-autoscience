from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROUTE_ACTIONS = frozenset(
    {
        "paper_write",
        "bundle_build",
        "submission_materialize",
        "delivery_sync",
        "runtime_recovery",
        "cleanup_apply",
    }
)

_ACTION_AUTHORIZATION_FIELDS = {
    "paper_write": "paper_write_allowed",
    "bundle_build": "bundle_build_allowed",
    "submission_materialize": "paper_write_allowed",
    "delivery_sync": "bundle_build_allowed",
    "runtime_recovery": "runtime_recovery_allowed",
    "cleanup_apply": "cleanup_apply_allowed",
}

_GENERATED_AUTHORITY_NAMES = {
    "current_package",
    "submission_minimal",
}

_GENERATED_AUTHORITY_SUFFIXES = (".docx", ".pdf", ".zip")


def authorize_control_plane_route(
    action: str,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_action = str(action or "").strip()
    if normalized_action not in ROUTE_ACTIONS:
        raise ValueError(f"unsupported control plane route action: {action}")
    route_context = context if isinstance(context, Mapping) else {}
    projection_only = bool(route_context.get("projection_only"))
    snapshot = _mapping(route_context.get("control_plane_snapshot"))
    blocking_reasons: list[str] = []

    if projection_only:
        blocking_reasons.extend(_generated_authority_blockers(route_context))
        return _gate_payload(
            action=normalized_action,
            authorized=True,
            projection_only=True,
            blocking_reasons=blocking_reasons,
            snapshot=snapshot,
        )

    if not snapshot:
        blocking_reasons.append("control_plane_snapshot_missing")
        return _gate_payload(
            action=normalized_action,
            authorized=False,
            projection_only=False,
            blocking_reasons=blocking_reasons,
            snapshot=snapshot,
        )

    if not _has_authority_epoch(snapshot):
        blocking_reasons.append("control_plane_authority_epoch_missing")
    dispatch_gate = _mapping(snapshot.get("dispatch_gate"))
    if dispatch_gate.get("state") != "open":
        blocking_reasons.append("dispatch_gate_blocked")
        for reason in _list(dispatch_gate.get("blocking_reasons")):
            reason_text = _text(reason)
            if reason_text and reason_text not in blocking_reasons:
                blocking_reasons.append(reason_text)

    route_authorization = _mapping(snapshot.get("route_authorization"))
    authorization_field = _ACTION_AUTHORIZATION_FIELDS[normalized_action]
    if route_authorization.get(authorization_field) is False:
        blocking_reasons.append(f"{authorization_field}_false")
    elif authorization_field not in route_authorization:
        blocking_reasons.append(f"{authorization_field}_missing")

    return _gate_payload(
        action=normalized_action,
        authorized=not blocking_reasons,
        projection_only=False,
        blocking_reasons=blocking_reasons,
        snapshot=snapshot,
    )


def assert_control_plane_route_authorized(
    action: str,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    gate = authorize_control_plane_route(action, context)
    if not gate["authorized"]:
        raise PermissionError(
            "control plane route blocked "
            f"{gate['action']}: {', '.join(gate['blocking_reasons'])}"
        )
    return gate


def attach_control_plane_route_gate(
    payload: Mapping[str, Any],
    gate: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(payload)
    result["control_plane_route_gate"] = dict(gate)
    return result


def _gate_payload(
    *,
    action: str,
    authorized: bool,
    projection_only: bool,
    blocking_reasons: list[str],
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface": "control_plane_route_gate",
        "schema_version": 1,
        "action": action,
        "authorized": authorized,
        "allowed": authorized,
        "projection_only": projection_only,
        "blocking_reasons": blocking_reasons,
        "route_authorization_flag": _ACTION_AUTHORIZATION_FIELDS[action],
        "snapshot_ref": _snapshot_ref(snapshot),
        "authority_policy": {
            "generated_delivery_surfaces_can_be_edit_source": False,
            "generated_delivery_surfaces_can_be_quality_authority": False,
            "generated_delivery_surfaces_can_be_dispatch_authority": False,
        },
    }


def _snapshot_ref(snapshot: Mapping[str, Any]) -> dict[str, Any] | None:
    if not snapshot:
        return None
    authority_refs = _mapping(snapshot.get("authority_refs"))
    study_truth = _mapping(authority_refs.get("study_truth"))
    runtime_health = _mapping(authority_refs.get("runtime_health"))
    return {
        "surface": _text(snapshot.get("surface")) or "control_plane_snapshot",
        "control_state": _text(snapshot.get("control_state")),
        "canonical_next_action": _text(snapshot.get("canonical_next_action")),
        "study_truth_epoch": _text(study_truth.get("epoch")),
        "runtime_health_epoch": _text(runtime_health.get("epoch")),
    }


def _has_authority_epoch(snapshot: Mapping[str, Any]) -> bool:
    authority_refs = _mapping(snapshot.get("authority_refs"))
    for key in ("study_truth", "runtime_health"):
        ref = _mapping(authority_refs.get(key))
        if _text(ref.get("epoch")) is None:
            return False
    return True


def _generated_authority_blockers(context: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    paths = _list(context.get("paths"))
    for item in paths:
        path_text = _text(item)
        if path_text is None:
            continue
        path = Path(path_text)
        if path.name in _GENERATED_AUTHORITY_NAMES or path.suffix.lower() in _GENERATED_AUTHORITY_SUFFIXES:
            blockers.append(f"projection_only_generated_surface:{path.name}")
    return blockers


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ROUTE_ACTIONS",
    "assert_control_plane_route_authorized",
    "attach_control_plane_route_gate",
    "authorize_control_plane_route",
]
