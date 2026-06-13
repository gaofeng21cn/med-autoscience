from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    required_output_contract,
)

from .primitives import mapping as _mapping
from .primitives import text as _text
from .primitives import text_items as _text_items


ActionSupersedesTypedBlocker = Callable[..., bool]
OWNER_ANSWER_IDENTITY_BASIS_KEYS = frozenset(
    {
        "source_eval_id",
        "truth_epoch",
        "runtime_health_epoch",
        "work_unit_id",
        "work_unit_fingerprint",
        "action_fingerprint",
        "source_fingerprint",
        "idempotency_key",
        "stage_attempt_id",
    }
)


def owner_answer_typed_blocker(
    *,
    blocker: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    currentness_basis: Mapping[str, Any],
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
    action_fingerprint: str | None,
) -> dict[str, Any]:
    payload = dict(blocker)
    answer_ref = typed_blocker_answer_ref(payload)
    if answer_ref is not None:
        payload["typed_blocker_ref"] = answer_ref
        payload["latest_owner_answer_ref"] = answer_ref
        payload["latest_owner_answer_kind"] = "typed_blocker"
    basis = _typed_blocker_owner_answer_basis(
        blocker=payload,
        action=action,
        currentness_basis=currentness_basis,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        action_fingerprint=action_fingerprint,
    )
    if basis:
        payload["currentness_basis"] = basis
        payload["owner_route_currentness_basis"] = basis
    payload["owner_answer_shape"] = "typed_blocker_ref"
    return payload


def owner_answer_binding(
    *,
    blocker: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    currentness_basis: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    status_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    typed_blocker_ref = typed_blocker_answer_ref(blocker)
    if typed_blocker_ref is None:
        return None
    basis = _mapping(blocker.get("currentness_basis")) or dict(currentness_basis)
    return {
        "answer_kind": "typed_blocker_ref",
        "typed_blocker_ref": typed_blocker_ref,
        "latest_owner_answer_ref": typed_blocker_ref,
        "accepted_answer_shape": [
            "domain_owner_receipt_ref",
            "quality_gate_receipt_ref",
            "typed_blocker_ref",
            "human_gate_ref",
            "route_back_evidence_ref",
        ],
        "stage_id": _stage_id(action=action, progress=progress_payload, status=status_payload),
        "work_unit_id": _text(basis.get("work_unit_id")) or _text(blocker.get("work_unit_id")),
        "work_unit_fingerprint": _text(basis.get("work_unit_fingerprint"))
        or _text(blocker.get("work_unit_fingerprint")),
        "source_fingerprint": _text(basis.get("source_fingerprint")) or _text(blocker.get("source_fingerprint")),
        "idempotency_key": _text(basis.get("idempotency_key")) or _text(blocker.get("idempotency_key")),
        "stage_attempt_id": _text(basis.get("stage_attempt_id")) or _text(blocker.get("stage_attempt_id")),
        "currentness_basis": basis,
        "stage_run_closeout_policy": {
            "owner_answer_required": True,
            "accepted_terminal_results": ["owner_receipt", "typed_blocker"],
            "provider_completion_is_domain_completion": False,
            "domain_ready_authorized": False,
        },
    }


def typed_blocker_required_output_contract(blocker: Mapping[str, Any]) -> dict[str, Any]:
    contract = required_output_contract(blocker)
    typed_blocker_ref = typed_blocker_answer_ref(blocker)
    if typed_blocker_ref is None:
        return contract
    accepted = list(contract.get("accepted_terminal_results") or [])
    for item in ("owner_receipt", "typed_blocker"):
        if item not in accepted:
            accepted.append(item)
    return {
        **contract,
        "owner_receipt_required": contract.get("owner_receipt_required") is not False,
        "typed_blocker_accepted": True,
        "accepted_terminal_results": accepted,
        "accepted_return_shape": [
            "domain_owner_receipt_ref",
            "quality_gate_receipt_ref",
            "typed_blocker_ref",
            "human_gate_ref",
            "route_back_evidence_ref",
        ],
        "typed_blocker_ref": typed_blocker_ref,
        "provider_completion_is_domain_completion": False,
        "domain_ready_authorized": False,
    }


def typed_blocker_answer_ref(blocker: Mapping[str, Any]) -> str | None:
    closeout_refs = _text_items(blocker.get("closeout_refs"))
    for ref in closeout_refs:
        if ref.endswith("#typed_blocker"):
            return ref
    return _text(blocker.get("typed_blocker_ref")) or _text(blocker.get("source_ref"))


def typed_blocker_has_owner_answer_currentness(blocker: Mapping[str, Any] | None) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return False
    if typed_blocker_answer_ref(payload) is not None:
        return True
    if _text(payload.get("latest_owner_answer_ref")) is not None:
        return True
    if _text_items(payload.get("closeout_refs")):
        return True
    if _mapping(payload.get("owner_answer_binding")):
        return True
    basis = _mapping(payload.get("currentness_basis")) or _mapping(
        payload.get("owner_route_currentness_basis")
    )
    return bool(
        _text(basis.get("work_unit_id"))
        and (
            _text(basis.get("work_unit_fingerprint"))
            or _text(basis.get("source_fingerprint"))
            or _text(basis.get("stage_attempt_id"))
        )
    )


def typed_blocker_is_stage_owner_answer(blocker: Mapping[str, Any] | None) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return False
    basis = _mapping(payload.get("currentness_basis")) or _mapping(
        payload.get("owner_route_currentness_basis")
    )
    return (
        _text(basis.get("source")) == "stage_owner_answer.typed_blocker"
        or _text(payload.get("latest_owner_answer_kind")) == "typed_blocker"
        and _text(payload.get("action_type")) == "complete_medical_paper_readiness_surface"
    )


def typed_blocker_precedes_stage_owner_answer(
    *,
    blocker: Mapping[str, Any] | None,
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
    action_supersedes_typed_blocker: ActionSupersedesTypedBlocker,
) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return False
    if typed_blocker_is_stage_owner_answer(payload):
        return False
    if action is not None and action_supersedes_typed_blocker(
        action=action,
        blocker=payload,
        progress=progress,
    ):
        return False
    if not typed_blocker_has_owner_answer_currentness(payload):
        return False
    return (
        _text(payload.get("stage_attempt_id")) is not None
        or _text(payload.get("terminal_closeout_status")) is not None
        or _text(payload.get("terminal_closeout_outcome")) is not None
        or bool(_text_items(payload.get("closeout_refs")))
        or default_executor_closeout_ref(payload)
    )


def default_executor_closeout_ref(blocker: Mapping[str, Any]) -> bool:
    for value in (
        _text(blocker.get("typed_blocker_ref")),
        _text(blocker.get("source_ref")),
        _text(blocker.get("latest_owner_answer_ref")),
        *_text_items(blocker.get("acceptance_refs")),
    ):
        if value is not None and "default_executor_execution/" in value:
            return True
    return False


def _typed_blocker_owner_answer_basis(
    *,
    blocker: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    currentness_basis: Mapping[str, Any],
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
    action_fingerprint: str | None,
) -> dict[str, Any]:
    action_payload = _mapping(action)
    action_source_refs = _mapping(action_payload.get("source_refs"))
    existing = _mapping(blocker.get("currentness_basis")) or _mapping(
        blocker.get("owner_route_currentness_basis")
    )
    basis = {
        key: value
        for key, value in existing.items()
        if value not in (None, "", [], {}) and key not in OWNER_ANSWER_IDENTITY_BASIS_KEYS
    }
    basis.update(
        {
            key: value
            for key, value in currentness_basis.items()
            if value not in (None, "", [], {})
        }
    )
    for key, value in {
        "source_eval_id": _text(action_payload.get("source_eval_id"))
        or _text(action_source_refs.get("source_eval_id")),
        "truth_epoch": _text(action_payload.get("truth_epoch")),
        "runtime_health_epoch": _text(action_payload.get("runtime_health_epoch")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": action_fingerprint,
        "source_fingerprint": _text(blocker.get("source_fingerprint"))
        or _text(action_payload.get("source_fingerprint")),
        "idempotency_key": _text(blocker.get("idempotency_key")) or _text(action_payload.get("idempotency_key")),
        "stage_attempt_id": _text(blocker.get("stage_attempt_id")) or _text(action_payload.get("stage_attempt_id")),
    }.items():
        if value is not None:
            basis[key] = value
    return {key: value for key, value in basis.items() if value not in (None, "", [], {})}


def _stage_id(
    *,
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
    status: Mapping[str, Any],
) -> str | None:
    action_payload = _mapping(action)
    return (
        _text(action_payload.get("stage_id"))
        or _text(progress.get("current_stage"))
        or _text(status.get("current_stage"))
        or _text(status.get("stage_id"))
    )


__all__ = [
    "default_executor_closeout_ref",
    "owner_answer_binding",
    "owner_answer_typed_blocker",
    "typed_blocker_answer_ref",
    "typed_blocker_has_owner_answer_currentness",
    "typed_blocker_is_stage_owner_answer",
    "typed_blocker_precedes_stage_owner_answer",
    "typed_blocker_required_output_contract",
]
