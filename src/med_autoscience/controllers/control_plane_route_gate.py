from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.gate_clearing_batch_work_units import UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS


ROUTE_ACTIONS = frozenset(
    {
        "paper_write",
        "bundle_build",
        "submission_materialize",
        "submission_notice_materialize",
        "delivery_sync",
        "runtime_recovery",
        "cleanup_apply",
    }
)

_ACTION_AUTHORIZATION_FIELDS = {
    "paper_write": "paper_write_allowed",
    "bundle_build": "bundle_build_allowed",
    "submission_materialize": "paper_write_allowed",
    "submission_notice_materialize": "bundle_build_allowed",
    "delivery_sync": "bundle_build_allowed",
    "runtime_recovery": "runtime_recovery_allowed",
    "cleanup_apply": "cleanup_apply_allowed",
}

_UPSTREAM_PUBLISHABILITY_REPAIR_BYPASS_REASONS = frozenset(
    {
        "execution_owner_guard.supervisor_only",
        "live_worker_meaningful_artifact_delta_timeout",
        "publication_supervisor_state.bundle_tasks_downstream_only",
        "runtime_recovery_retry_budget_exhausted",
        "same_fingerprint_loop",
    }
)

_CONTROLLER_ROUTE_ALLOWED_ACTIONS_BY_WORK_UNIT = {
    "analysis_claim_evidence_repair": frozenset({"paper_write"}),
    "controller_owned_publication_repair": frozenset(
        {"bundle_build", "delivery_sync", "submission_materialize", "submission_notice_materialize"}
    ),
    "display_reporting_contract_repair": frozenset({"bundle_build"}),
    "figure_results_trace_repair": frozenset({"paper_write"}),
    "local_architecture_overview_repair": frozenset({"bundle_build"}),
    "manuscript_story_repair": frozenset({"paper_write"}),
    "publication_gate_replay": frozenset(
        {"bundle_build", "delivery_sync", "submission_notice_materialize"}
    ),
    "submission_delivery_sync_closure": frozenset(
        {"bundle_build", "delivery_sync", "submission_notice_materialize"}
    ),
    "submission_authority_sync_closure": frozenset(
        {"bundle_build", "delivery_sync", "submission_materialize", "submission_notice_materialize"}
    ),
    "submission_minimal_refresh": frozenset(
        {"bundle_build", "delivery_sync", "submission_materialize", "submission_notice_materialize"}
    ),
    "treatment_gap_reporting_repair": frozenset({"paper_write"}),
}
_CONTROLLER_ROUTE_ACTION_TYPES = {
    "run_gate_clearing_batch",
    "run_quality_repair_batch",
}
_CONTROLLER_ROUTE_SURFACES = {
    "gate_clearing_batch",
    "quality_repair_batch",
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
    controller_route_gate = _controller_route_gate(normalized_action, route_context)
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

    if not snapshot and not bool(controller_route_gate.get("authorized")):
        blocking_reasons.append("control_plane_snapshot_missing")
        return _controller_or_gate_payload(
            controller_route_gate=controller_route_gate,
            snapshot_blocking_reasons=blocking_reasons,
            action=normalized_action,
            projection_only=False,
            snapshot=snapshot,
        )
    if not snapshot:
        return _controller_or_gate_payload(
            controller_route_gate=controller_route_gate,
            snapshot_blocking_reasons=blocking_reasons,
            action=normalized_action,
            projection_only=False,
            snapshot=snapshot,
        )

    if not _has_authority_epoch(snapshot):
        blocking_reasons.append("control_plane_authority_epoch_missing")
    dispatch_gate = _mapping(snapshot.get("dispatch_gate"))
    dispatch_gate_reasons = [
        reason_text
        for reason in _list(dispatch_gate.get("blocking_reasons"))
        if (reason_text := _text(reason)) is not None
    ]
    if dispatch_gate.get("state") != "open" and not _controller_route_can_bypass_dispatch_reasons(
        normalized_action,
        controller_route_gate,
        dispatch_gate_reasons,
    ):
        blocking_reasons.append("dispatch_gate_blocked")
        for reason_text in dispatch_gate_reasons:
            if reason_text not in blocking_reasons:
                blocking_reasons.append(reason_text)

    route_authorization = _mapping(snapshot.get("route_authorization"))
    authorization_field = _ACTION_AUTHORIZATION_FIELDS[normalized_action]
    if route_authorization.get(authorization_field) is False:
        if not _controller_route_can_bypass_action_authorization(
            normalized_action,
            controller_route_gate,
            dispatch_gate_reasons,
        ):
            blocking_reasons.append(f"{authorization_field}_false")
    elif authorization_field not in route_authorization:
        blocking_reasons.append(f"{authorization_field}_missing")

    return _controller_or_gate_payload(
        controller_route_gate=controller_route_gate,
        snapshot_blocking_reasons=blocking_reasons,
        action=normalized_action,
        projection_only=False,
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


def _controller_or_gate_payload(
    *,
    controller_route_gate: Mapping[str, Any],
    snapshot_blocking_reasons: list[str],
    action: str,
    projection_only: bool,
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    blocking_reasons = list(snapshot_blocking_reasons)
    controller_route_present = bool(controller_route_gate.get("present"))
    if controller_route_present and not bool(controller_route_gate.get("authorized")):
        blocking_reasons.append("controller_repair_authorization_blocked")
        for reason in _list(controller_route_gate.get("blocking_reasons")):
            reason_text = _text(reason)
            if reason_text and reason_text not in blocking_reasons:
                blocking_reasons.append(reason_text)
    payload = _gate_payload(
        action=action,
        authorized=not blocking_reasons,
        projection_only=projection_only,
        blocking_reasons=blocking_reasons,
        snapshot=snapshot,
    )
    if controller_route_present:
        payload["controller_route_gate"] = dict(controller_route_gate)
        payload["controller_repair_authorization_ref"] = _controller_repair_authorization_ref(controller_route_gate)
    return payload


def _controller_route_gate(action: str, route_context: Mapping[str, Any]) -> dict[str, Any]:
    controller_route = _controller_route_context(route_context)
    if not controller_route:
        return {"present": False, "authorized": False, "blocking_reasons": []}
    blocking_reasons: list[str] = []
    work_unit_id = _text(controller_route.get("work_unit_id"))
    controller_action_type = _text(controller_route.get("controller_action_type"))
    control_surface = _text(controller_route.get("control_surface"))
    if bool(controller_route.get("requires_human_confirmation")):
        blocking_reasons.append("controller_route_requires_human_confirmation")
    if work_unit_id not in _CONTROLLER_ROUTE_ALLOWED_ACTIONS_BY_WORK_UNIT:
        blocking_reasons.append("controller_route_work_unit_unsupported")
    elif action not in _CONTROLLER_ROUTE_ALLOWED_ACTIONS_BY_WORK_UNIT[work_unit_id]:
        blocking_reasons.append("controller_route_action_not_allowed_for_work_unit")
    if controller_action_type not in _CONTROLLER_ROUTE_ACTION_TYPES:
        blocking_reasons.append("controller_route_action_type_unsupported")
    if control_surface not in _CONTROLLER_ROUTE_SURFACES:
        blocking_reasons.append("controller_route_surface_unsupported")
    return {
        "present": True,
        "surface": "controller_route_gate",
        "schema_version": 1,
        "authorized": not blocking_reasons,
        "action": action,
        "work_unit_id": work_unit_id,
        "controller_action_type": controller_action_type,
        "control_surface": control_surface,
        "blocking_reasons": blocking_reasons,
        "authority_ref": {
            key: _text(controller_route.get(key))
            for key in ("gate_fingerprint", "work_unit_fingerprint", "source_eval_id")
            if _text(controller_route.get(key)) is not None
        },
    }


def _controller_route_context(route_context: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("controller_route_context", "explicit_controller_route_context"):
        value = route_context.get(key)
        if isinstance(value, Mapping):
            return value
    return {}


def _controller_route_can_bypass_dispatch_reasons(
    action: str,
    controller_route_gate: Mapping[str, Any],
    dispatch_gate_reasons: list[str],
) -> bool:
    if not bool(controller_route_gate.get("authorized")):
        return False
    if not dispatch_gate_reasons:
        return False
    if _controller_route_is_upstream_publishability_repair(controller_route_gate, action=action):
        return set(dispatch_gate_reasons) <= _UPSTREAM_PUBLISHABILITY_REPAIR_BYPASS_REASONS
    return set(dispatch_gate_reasons) <= {"runtime_recovery_retry_budget_exhausted"}


def _controller_route_can_bypass_action_authorization(
    action: str,
    controller_route_gate: Mapping[str, Any],
    dispatch_gate_reasons: list[str],
) -> bool:
    return (
        bool(dispatch_gate_reasons)
        and _controller_route_is_upstream_publishability_repair(controller_route_gate, action=action)
        and set(dispatch_gate_reasons) <= _UPSTREAM_PUBLISHABILITY_REPAIR_BYPASS_REASONS
    )


def _controller_route_is_upstream_publishability_repair(
    controller_route_gate: Mapping[str, Any],
    *,
    action: str,
) -> bool:
    return (
        action == "paper_write"
        and _text(controller_route_gate.get("work_unit_id")) in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS
    )


def _controller_repair_authorization_ref(controller_route_gate: Mapping[str, Any]) -> dict[str, Any]:
    authority_ref = _mapping(controller_route_gate.get("authority_ref"))
    return {
        "surface": "controller_repair_authorization",
        "authorized": bool(controller_route_gate.get("authorized")),
        "action": _text(controller_route_gate.get("action")),
        "work_unit_id": _text(controller_route_gate.get("work_unit_id")),
        "controller_action_type": _text(controller_route_gate.get("controller_action_type")),
        "control_surface": _text(controller_route_gate.get("control_surface")),
        "gate_fingerprint": _text(authority_ref.get("gate_fingerprint")),
        "work_unit_fingerprint": _text(authority_ref.get("work_unit_fingerprint")),
        "source_eval_id": _text(authority_ref.get("source_eval_id")),
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
