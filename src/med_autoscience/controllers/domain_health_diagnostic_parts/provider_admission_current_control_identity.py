from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    text_items as _text_items,
)


def provider_admission_current_control_study(candidate: Mapping[str, Any]) -> dict[str, Any]:
    action = provider_admission_current_control_action(candidate)
    owner_route = _mapping(action.get("owner_route"))
    study_id = _non_empty_text(candidate.get("study_id"))
    route_key = route_identity_key(candidate)
    attempt_key = attempt_idempotency_key(candidate)
    return {
        "study_id": study_id,
        "quest_id": _non_empty_text(candidate.get("quest_id")),
        "handoff_generated_at": _non_empty_text(candidate.get("recorded_at")),
        "handoff_scan_status": "provider_admission_from_mas_handoff",
        "study_root": _non_empty_text(candidate.get("study_root")),
        "quest_status": "provider_admission_pending",
        "active_run_id": None,
        "active_stage_attempt_id": None,
        "active_workflow_id": None,
        "running_provider_attempt": False,
        "runtime_health": {
            "health_status": "provider_admission_pending",
            "runtime_liveness_status": "not_running",
            "blocked_reason": _non_empty_text(candidate.get("blocked_reason")),
            "summary": "Current MAS owner action is ready for OPL provider admission.",
        },
        "action_queue": [action],
        "provider_admission_identity": dict(candidate),
        "provider_admission_identity_key": route_key,
        "attempt_idempotency_key": attempt_key,
        "provider_admission_candidates": [dict(candidate)],
        "provider_admission_pending_count": 1,
        "why_not_applied": ["provider_admission_current_control_state_required"],
        "blocked_reason": "provider_admission_current_control_state_required",
        "next_owner": "one-person-lab",
        "external_supervisor_required": True,
        "owner_route": owner_route,
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": _non_empty_text(candidate.get("next_executable_owner")) or "one-person-lab",
            "next_work_unit": _non_empty_text(candidate.get("work_unit_id")),
            "typed_blocker": None,
            "parked_state": None,
            "source": "mas_provider_admission_identity",
            "route_identity_key": route_key,
            "attempt_idempotency_key": attempt_key,
        },
    }


def provider_admission_current_control_action(candidate: Mapping[str, Any]) -> dict[str, Any]:
    action_type = _non_empty_text(candidate.get("action_type"))
    study_id = _non_empty_text(candidate.get("study_id"))
    work_unit_id = _non_empty_text(candidate.get("work_unit_id"))
    action_fingerprint = _non_empty_text(candidate.get("action_fingerprint")) or _non_empty_text(
        candidate.get("work_unit_fingerprint")
    )
    route_key = route_identity_key(candidate)
    attempt_key = attempt_idempotency_key(candidate)
    dispatch_ref = _non_empty_text(candidate.get("dispatch_ref")) or _non_empty_text(candidate.get("dispatch_path"))
    stage_packet_ref = _non_empty_text(candidate.get("stage_packet_ref"))
    stage_packet_refs = _text_items(candidate.get("stage_packet_refs"))
    if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
        stage_packet_refs.append(stage_packet_ref)
    checkpoint_refs = _text_items(candidate.get("checkpoint_refs")) or list(stage_packet_refs)
    source_refs = {
        key: value
        for key, value in {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": attempt_key,
            "provider_admission_identity_ref": _non_empty_text(candidate.get("execution_ref")),
            "dispatch_path": _non_empty_text(candidate.get("dispatch_path")),
            "dispatch_ref": dispatch_ref,
            "stage_packet_ref": stage_packet_ref,
            "stage_packet_refs": stage_packet_refs or None,
            "blocked_reason": _non_empty_text(candidate.get("blocked_reason")),
        }.items()
        if value not in (None, "", [], {})
    }
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": _non_empty_text(candidate.get("quest_id")),
        "truth_epoch": _non_empty_text(_mapping(candidate.get("currentness_basis")).get("truth_epoch"))
        or action_fingerprint,
        "runtime_health_epoch": _non_empty_text(
            _mapping(candidate.get("currentness_basis")).get("runtime_health_epoch")
        )
        or action_fingerprint,
        "work_unit_fingerprint": action_fingerprint,
        "failure_signature": action_type,
        "trace_id": f"provider-admission::{study_id}::{action_type}",
        "route_epoch": action_fingerprint,
        "source_fingerprint": action_fingerprint,
        "current_owner": "med-autoscience",
        "next_owner": _non_empty_text(candidate.get("next_executable_owner")),
        "owner_reason": work_unit_id or action_type,
        "active_run_id": None,
        "allowed_actions": [action_type] if action_type is not None else [],
        "blocked_actions": [],
        "source_refs": {
            **source_refs,
            "owner_route_currentness_basis": dict(_mapping(candidate.get("currentness_basis"))),
        },
        "idempotency_key": route_key,
    }
    return {
        key: value
        for key, value in {
            "study_id": study_id,
            "quest_id": _non_empty_text(candidate.get("quest_id")),
            "action_type": action_type,
            "action_id": f"provider-admission::{study_id}::{action_type}",
            "status": "queued",
            "reason": _non_empty_text(candidate.get("blocked_reason")) or "provider_admission_pending",
            "owner": _non_empty_text(candidate.get("next_executable_owner")),
            "request_owner": _non_empty_text(candidate.get("next_executable_owner")),
            "recommended_owner": _non_empty_text(candidate.get("next_executable_owner")),
            "authority": "mas_provider_admission_identity",
            "required_output_surface": _non_empty_text(candidate.get("required_output_surface")),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": attempt_key,
            "idempotency_key": attempt_key,
            "dispatch_ref": dispatch_ref,
            "stage_packet_ref": stage_packet_ref,
            "stage_packet_refs": stage_packet_refs or None,
            "checkpoint_refs": checkpoint_refs or None,
            "source_surface": "mas_opl_runtime_owner_handoff.provider_admission_identity",
            "source_ref": _non_empty_text(candidate.get("execution_ref")),
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "dispatch_path": _non_empty_text(candidate.get("dispatch_path")),
            "blocked_reason": _non_empty_text(candidate.get("blocked_reason")),
            "owner_route": owner_route,
            "handoff_packet": {
                "surface": "provider_admission_current_control_handoff",
                "authority": "mas_provider_admission_identity",
                "owner": _non_empty_text(candidate.get("next_executable_owner")),
                "request_owner": _non_empty_text(candidate.get("next_executable_owner")),
                "recommended_owner": _non_empty_text(candidate.get("next_executable_owner")),
                "next_executable_owner": _non_empty_text(candidate.get("next_executable_owner")),
                "required_output_surface": _non_empty_text(candidate.get("required_output_surface")),
                "next_work_unit": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "route_identity_key": route_key,
                "attempt_idempotency_key": attempt_key,
                "dispatch_ref": dispatch_ref,
                "dispatch_path": _non_empty_text(candidate.get("dispatch_path")),
                "stage_packet_ref": stage_packet_ref,
                "stage_packet_refs": stage_packet_refs or None,
                "checkpoint_refs": checkpoint_refs or None,
                "source_ref": _non_empty_text(candidate.get("execution_ref")),
                "owner_route": owner_route,
            },
        }.items()
        if value not in (None, "", [], {})
    }


def route_identity_key(payload: Mapping[str, Any]) -> str | None:
    return _non_empty_text(payload.get("route_identity_key"))


def attempt_idempotency_key(payload: Mapping[str, Any]) -> str | None:
    return _non_empty_text(payload.get("attempt_idempotency_key"))


def missing_identity_fields(payload: Mapping[str, Any]) -> list[str] | None:
    result = [
        item
        for item in payload.get("missing_identity_fields") or []
        if _non_empty_text(item) is not None
    ]
    return result or None


def candidate_with_identity(candidate: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(candidate)
    fingerprint = _non_empty_text(payload.get("work_unit_fingerprint")) or _non_empty_text(
        payload.get("action_fingerprint")
    )
    can_bind_progress_currentness = (
        _non_empty_text(payload.get("source"))
        == "opl_current_control_state.study_current_executable_owner_action"
    )
    route_key = route_identity_key(payload)
    if route_key is None and can_bind_progress_currentness:
        study_id = _non_empty_text(payload.get("study_id"))
        if study_id is not None and fingerprint is not None:
            route_key = f"provider-admission::{study_id}::{fingerprint}"
    attempt_key = attempt_idempotency_key(payload)
    if attempt_key is None and can_bind_progress_currentness:
        attempt_key = route_key
    if route_key is not None:
        payload["route_identity_key"] = route_key
    if attempt_key is not None:
        payload["attempt_idempotency_key"] = attempt_key
        payload.setdefault("idempotency_key", attempt_key)
    stage_packet_ref = _non_empty_text(payload.get("stage_packet_ref"))
    if stage_packet_ref is not None:
        refs = [
            item
            for item in payload.get("stage_packet_refs") or []
            if _non_empty_text(item) is not None
        ]
        if stage_packet_ref not in refs:
            refs.append(stage_packet_ref)
        payload["stage_packet_refs"] = refs
    return payload


def candidate_with_progress_currentness_identity(
    candidate: Mapping[str, Any],
    *,
    scanned_studies_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    payload = dict(candidate)
    study_id = _non_empty_text(payload.get("study_id"))
    study = _mapping(scanned_studies_by_id.get(study_id)) if study_id is not None else {}
    current_action = _mapping(study.get("current_executable_owner_action"))
    current_work_unit = _mapping(study.get("current_work_unit"))
    basis = _candidate_progress_currentness_basis(
        payload,
        current_action=current_action,
        current_work_unit=current_work_unit,
    )
    closeout_basis = _candidate_closeout_currentness_basis(payload, study=study)
    if closeout_basis:
        basis = {
            **closeout_basis,
            **basis,
            "truth_epoch": _non_empty_text(basis.get("truth_epoch"))
            or _non_empty_text(closeout_basis.get("truth_epoch")),
            "runtime_health_epoch": _non_empty_text(basis.get("runtime_health_epoch"))
            or _non_empty_text(closeout_basis.get("runtime_health_epoch")),
            "source_eval_id": _non_empty_text(basis.get("source_eval_id"))
            or _non_empty_text(closeout_basis.get("source_eval_id")),
        }
    basis = _normalized_currentness_basis(basis)
    if basis:
        payload["currentness_basis"] = basis
    if _non_empty_text(payload.get("dispatch_path")) is None and _non_empty_text(
        payload.get("dispatch_ref")
    ) is None:
        dispatch_ref = _progress_currentness_dispatch_ref(
            payload,
            current_action=current_action,
        )
        if dispatch_ref is None and basis:
            dispatch_ref = _closeout_precedence_dispatch_ref(payload)
        if dispatch_ref is not None:
            payload["dispatch_ref"] = dispatch_ref
    return payload


def _candidate_closeout_currentness_basis(
    candidate: Mapping[str, Any],
    *,
    study: Mapping[str, Any],
) -> dict[str, Any]:
    for receipt in accepted_closeout_receipts(study):
        basis = closeout_owner_route_basis(receipt)
        if not basis:
            continue
        closeout_identity = {
            "action_type": _non_empty_text(receipt.get("action_type"))
            or _non_empty_text(candidate.get("action_type")),
            "work_unit_id": _non_empty_text(receipt.get("work_unit_id"))
            or _non_empty_text(basis.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(receipt.get("work_unit_fingerprint"))
            or _non_empty_text(receipt.get("action_fingerprint"))
            or _non_empty_text(basis.get("work_unit_fingerprint"))
            or _non_empty_text(basis.get("action_fingerprint")),
            "action_fingerprint": _non_empty_text(receipt.get("action_fingerprint"))
            or _non_empty_text(receipt.get("work_unit_fingerprint"))
            or _non_empty_text(basis.get("action_fingerprint"))
            or _non_empty_text(basis.get("work_unit_fingerprint")),
        }
        if _identity_core_matches(closeout_identity, identity=candidate):
            return _normalized_currentness_basis(basis)
    return {}


def _identity_core_matches(
    payload: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    expected_action = _non_empty_text(identity.get("action_type"))
    if expected_action is not None and _non_empty_text(payload.get("action_type")) != expected_action:
        return False
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    if (
        expected_work_unit is not None
        and _non_empty_text(payload.get("work_unit_id")) != expected_work_unit
    ):
        return False
    expected_fingerprint = _non_empty_text(identity.get("work_unit_fingerprint")) or _non_empty_text(
        identity.get("action_fingerprint")
    )
    payload_fingerprint = _non_empty_text(payload.get("work_unit_fingerprint")) or _non_empty_text(
        payload.get("action_fingerprint")
    )
    if expected_fingerprint is None:
        return True
    return payload_fingerprint == expected_fingerprint


def _candidate_progress_currentness_basis(
    candidate: Mapping[str, Any],
    *,
    current_action: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
) -> dict[str, Any]:
    existing = _mapping(candidate.get("currentness_basis"))
    action_matches = _identity_core_matches(current_action, identity=candidate)
    work_unit_matches = _identity_core_matches(current_work_unit, identity=candidate)
    action_basis = (
        _mapping(current_action.get("owner_route_currentness_basis"))
        or _mapping(current_action.get("currentness_basis"))
        if action_matches
        else {}
    )
    work_unit_basis = (
        _mapping(current_work_unit.get("currentness_basis")) if work_unit_matches else {}
    )
    basis = {
        **dict(work_unit_basis),
        **dict(action_basis),
        **dict(existing),
    }
    for key, value in {
        "work_unit_id": _non_empty_text(basis.get("work_unit_id"))
        or _non_empty_text(candidate.get("work_unit_id"))
        or (_non_empty_text(current_action.get("work_unit_id")) if action_matches else None)
        or (_non_empty_text(current_work_unit.get("work_unit_id")) if work_unit_matches else None),
        "work_unit_fingerprint": _non_empty_text(basis.get("work_unit_fingerprint"))
        or _non_empty_text(candidate.get("work_unit_fingerprint"))
        or _non_empty_text(candidate.get("action_fingerprint"))
        or (_non_empty_text(current_action.get("work_unit_fingerprint")) if action_matches else None)
        or (_non_empty_text(current_action.get("action_fingerprint")) if action_matches else None)
        or (_non_empty_text(current_work_unit.get("work_unit_fingerprint")) if work_unit_matches else None)
        or (_non_empty_text(current_work_unit.get("action_fingerprint")) if work_unit_matches else None),
        "source_eval_id": _non_empty_text(basis.get("source_eval_id"))
        or _non_empty_text(candidate.get("source_eval_id"))
        or (
            _current_action_source_eval_id(current_action)
            if action_matches
            else None
        ),
        "current_action_source": _non_empty_text(basis.get("current_action_source"))
        or (_non_empty_text(current_action.get("source")) if action_matches else None),
        "current_work_unit_source": _non_empty_text(basis.get("current_work_unit_source"))
        or (
            _non_empty_text(_mapping(current_work_unit.get("state")).get("source"))
            if work_unit_matches
            else None
        ),
        "truth_epoch": _non_empty_text(basis.get("truth_epoch"))
        or _non_empty_text(candidate.get("truth_epoch"))
        or (_non_empty_text(current_action.get("truth_epoch")) if action_matches else None),
        "runtime_health_epoch": _non_empty_text(basis.get("runtime_health_epoch"))
        or _non_empty_text(candidate.get("runtime_health_epoch"))
        or (_non_empty_text(current_action.get("runtime_health_epoch")) if action_matches else None),
    }.items():
        if value is not None:
            basis[key] = value
    basis = _normalized_currentness_basis(basis)
    if basis_conflicts_with_identity(basis, identity=candidate):
        return {}
    return basis


def basis_conflicts_with_identity(
    basis: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    for basis_key, identity_keys in {
        "work_unit_id": ("work_unit_id",),
        "work_unit_fingerprint": ("work_unit_fingerprint", "action_fingerprint"),
        "action_fingerprint": ("action_fingerprint", "work_unit_fingerprint"),
    }.items():
        basis_value = _non_empty_text(basis.get(basis_key))
        identity_value = next(
            (
                text
                for key in identity_keys
                if (text := _non_empty_text(identity.get(key))) is not None
            ),
            None,
        )
        if basis_value is not None and identity_value is not None and basis_value != identity_value:
            return True
    return False


def _progress_currentness_dispatch_ref(
    candidate: Mapping[str, Any],
    *,
    current_action: Mapping[str, Any],
) -> str | None:
    source_ref = _non_empty_text(candidate.get("execution_ref")) or _non_empty_text(
        current_action.get("source_ref")
    )
    source = _non_empty_text(current_action.get("source")) or _non_empty_text(candidate.get("source"))
    route_key = route_identity_key(candidate)
    if source_ref is None and source is None and route_key is None:
        return None
    return "::".join(
        item
        for item in (
            "study-progress-current-owner-action",
            route_key,
            source,
            source_ref,
        )
        if item is not None
    )


def _closeout_precedence_dispatch_ref(candidate: Mapping[str, Any]) -> str | None:
    route_key = route_identity_key(candidate)
    if route_key is None:
        return None
    return f"terminal-closeout-precedence::{route_key}"


def weak_provider_admission_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    for key in ("study_id", "action_type", "work_unit_id"):
        if _non_empty_text(identity.get(key)) is None:
            missing.append(key)
    if (
        _non_empty_text(identity.get("work_unit_fingerprint")) is None
        and _non_empty_text(identity.get("action_fingerprint")) is None
    ):
        missing.append("work_unit_fingerprint")
    if (
        _non_empty_text(identity.get("dispatch_path")) is None
        and _non_empty_text(identity.get("dispatch_ref")) is None
    ):
        missing.append("dispatch_path_or_ref")
    if _non_empty_text(identity.get("route_identity_key")) is None:
        missing.append("route_identity_key")
    if _non_empty_text(identity.get("attempt_idempotency_key")) is None:
        missing.append("attempt_idempotency_key")
    stage_packet_refs = [
        item
        for item in identity.get("stage_packet_refs") or []
        if _non_empty_text(item) is not None
    ]
    if (
        _non_empty_text(identity.get("stage_packet_ref")) is None
        and not stage_packet_refs
        and not _identity_is_strong_current_owner_delta(identity)
    ):
        missing.append("stage_packet_ref_or_refs")
    if not currentness_basis_strong(_mapping(identity.get("currentness_basis"))):
        missing.append("currentness_basis")
    if not missing:
        return {}
    return {
        "status": "weak_provider_admission_identity",
        "missing_identity_fields": missing,
    }


def currentness_basis_strong(basis: Mapping[str, Any]) -> bool:
    if _non_empty_text(basis.get("work_unit_id")) is None:
        return False
    if _non_empty_text(basis.get("work_unit_fingerprint")) is None:
        return False
    if _non_empty_text(basis.get("truth_epoch")) is None:
        return False
    return (
        _non_empty_text(basis.get("runtime_health_epoch")) is not None
        or _non_empty_text(basis.get("source_eval_id")) is not None
    )


def _identity_is_strong_current_owner_delta(identity: Mapping[str, Any]) -> bool:
    if (
        _non_empty_text(identity.get("source"))
        != "opl_current_control_state.study_current_executable_owner_action"
    ):
        return False
    if _non_empty_text(identity.get("next_executable_owner")) != "write":
        return False
    basis = _mapping(identity.get("currentness_basis"))
    source = _non_empty_text(basis.get("current_action_source")) or _non_empty_text(
        basis.get("current_work_unit_source")
    )
    if source != "publication_eval.recommended_actions.readiness_blocker_repair":
        return False
    if _non_empty_text(basis.get("source_eval_id")) is None:
        return False
    return currentness_basis_strong(basis)


def _current_action_source_eval_id(current_action: Mapping[str, Any]) -> str | None:
    target_surface = _mapping(current_action.get("target_surface"))
    return (
        _non_empty_text(current_action.get("source_eval_id"))
        or _non_empty_text(current_action.get("publication_eval_id"))
        or _non_empty_text(target_surface.get("publication_eval_id"))
    )


def accepted_closeout_receipts(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for key in (
        "default_executor_execution_receipt_consumption",
        "opl_provider_attempt",
        "terminal_closeout_precedence_evidence",
        "stage_attempt_closeout",
        "latest_stage_attempt_closeout",
        "latest_terminal_stage",
    ):
        _append_closeout_receipt(receipts, _mapping(study.get(key)))
    for key in (
        "accepted_closeout_evidence",
        "stage_attempt_closeouts",
        "default_executor_execution_receipt_consumptions",
        "stage_attempt_closeout_receipts",
    ):
        for item in study.get(key) or []:
            _append_closeout_receipt(receipts, _mapping(item))
    return receipts


def _append_closeout_receipt(receipts: list[dict[str, Any]], receipt: Mapping[str, Any]) -> None:
    normalized = _normalized_closeout_receipt(receipt)
    if normalized:
        receipts.append(normalized)


def _normalized_closeout_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if not receipt:
        return {}
    basis = closeout_owner_route_basis(receipt)
    typed_blocker = _mapping(receipt.get("typed_blocker"))
    normalized = dict(receipt)
    for key, value in {
        "work_unit_id": _non_empty_text(receipt.get("work_unit_id"))
        or _non_empty_text(basis.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(receipt.get("work_unit_fingerprint"))
        or _non_empty_text(receipt.get("action_fingerprint"))
        or _non_empty_text(typed_blocker.get("action_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("action_fingerprint")),
        "action_fingerprint": _non_empty_text(receipt.get("action_fingerprint"))
        or _non_empty_text(receipt.get("work_unit_fingerprint"))
        or _non_empty_text(typed_blocker.get("action_fingerprint"))
        or _non_empty_text(basis.get("action_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint")),
        "source_eval_id": _non_empty_text(receipt.get("source_eval_id"))
        or _non_empty_text(basis.get("source_eval_id")),
        "truth_epoch": _non_empty_text(receipt.get("truth_epoch"))
        or _non_empty_text(basis.get("truth_epoch")),
        "runtime_health_epoch": _non_empty_text(receipt.get("runtime_health_epoch"))
        or _non_empty_text(basis.get("runtime_health_epoch")),
    }.items():
        if value is not None:
            normalized[key] = value
    if basis and not _mapping(normalized.get("owner_route")):
        normalized["owner_route"] = {
            "work_unit_fingerprint": _non_empty_text(normalized.get("work_unit_fingerprint")),
            "source_eval_id": _non_empty_text(normalized.get("source_eval_id")),
            "truth_epoch": _non_empty_text(normalized.get("truth_epoch")),
            "runtime_health_epoch": _non_empty_text(normalized.get("runtime_health_epoch")),
            "source_refs": {
                "owner_route_currentness_basis": dict(basis),
                "work_unit_id": _non_empty_text(normalized.get("work_unit_id")),
                "work_unit_fingerprint": _non_empty_text(normalized.get("work_unit_fingerprint")),
                "source_eval_id": _non_empty_text(normalized.get("source_eval_id")),
            },
        }
    return normalized


def closeout_owner_route_basis(receipt: Mapping[str, Any]) -> dict[str, Any]:
    for value in (
        receipt.get("owner_route_basis"),
        receipt.get("owner_route_currentness"),
        _mapping(_mapping(receipt.get("owner_route")).get("source_refs")).get(
            "owner_route_currentness_basis"
        ),
        _mapping(receipt.get("owner_route")).get("source_refs", {}),
        receipt.get("canonical_work_unit_identity"),
        receipt.get("owner_route_currentness_basis"),
    ):
        basis = _mapping(value)
        normalized = _normalized_currentness_basis(basis)
        if normalized:
            return normalized
    return {}


def _normalized_currentness_basis(basis: Mapping[str, Any]) -> dict[str, Any]:
    result = {
        key: _non_empty_text(basis.get(key))
        for key in (
            "work_unit_id",
            "work_unit_fingerprint",
            "action_fingerprint",
            "source_eval_id",
            "truth_epoch",
            "runtime_health_epoch",
            "current_action_source",
            "current_work_unit_source",
        )
    }
    return {key: value for key, value in result.items() if value is not None}


__all__ = [
    "accepted_closeout_receipts",
    "attempt_idempotency_key",
    "basis_conflicts_with_identity",
    "candidate_with_identity",
    "candidate_with_progress_currentness_identity",
    "closeout_owner_route_basis",
    "currentness_basis_strong",
    "provider_admission_current_control_action",
    "provider_admission_current_control_study",
    "route_identity_key",
    "weak_provider_admission_identity",
]
