from __future__ import annotations

from collections.abc import Mapping
from typing import Any


CLOSEOUT_REQUIRED_REASON = "closeout_required_before_new_default_executor_task"


def closeout_first_admission(
    *,
    identity: Mapping[str, Any],
    immutable_dispatch_packet: Mapping[str, Any] | None,
    running_attempt: Mapping[str, Any] | None = None,
    owner_receipt: Mapping[str, Any] | None = None,
    stage_closeout: Mapping[str, Any] | None = None,
    stable_typed_blocker: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    packet = _mapping(immutable_dispatch_packet)
    consumed = _consumed_closeout(
        owner_receipt=owner_receipt,
        stage_closeout=stage_closeout,
        stable_typed_blocker=stable_typed_blocker,
    )
    if consumed is not None:
        return {
            "admission_status": "ready",
            "blocked_reason": None,
            "export_new_default_executor_task": True,
            "consumed_closeout": consumed,
            "immutable_dispatch_packet": packet or None,
        }
    if packet and _mapping(running_attempt):
        return {
            "admission_status": "blocked",
            "blocked_reason": CLOSEOUT_REQUIRED_REASON,
            "export_new_default_executor_task": False,
            "immutable_dispatch_packet": packet,
            "running_attempt": dict(running_attempt or {}),
            "typed_blocker": _closeout_required_blocker(identity=identity, packet=packet),
        }
    return {
        "admission_status": "ready",
        "blocked_reason": None,
        "export_new_default_executor_task": True,
        "consumed_closeout": None,
        "immutable_dispatch_packet": packet or None,
    }


def _consumed_closeout(
    *,
    owner_receipt: Mapping[str, Any] | None,
    stage_closeout: Mapping[str, Any] | None,
    stable_typed_blocker: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if _mapping(owner_receipt):
        return {"kind": "owner_receipt", "payload": dict(owner_receipt or {})}
    if _mapping(stage_closeout):
        return {"kind": "stage_closeout", "payload": dict(stage_closeout or {})}
    if _mapping(stable_typed_blocker):
        return {"kind": "stable_typed_blocker", "payload": dict(stable_typed_blocker or {})}
    return None


def _closeout_required_blocker(
    *,
    identity: Mapping[str, Any],
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_domain_typed_blocker",
        "schema_version": 1,
        "blocker_kind": "closeout_first_admission",
        "reason": CLOSEOUT_REQUIRED_REASON,
        "blocked_reason": CLOSEOUT_REQUIRED_REASON,
        "study_id": _text(identity.get("study_id")),
        "quest_id": _text(identity.get("quest_id")),
        "work_unit_id": _text(identity.get("work_unit_id")),
        "stage_attempt_id": _text(identity.get("stage_attempt_id")),
        "effective_eval_id": _text(packet.get("effective_eval_id")),
        "next_owner": "med-autoscience",
        "provider_completion_is_domain_completion": False,
        "export_new_default_executor_task": False,
        "authority_boundary": {
            "opl": "transport_and_attempt_projection_only",
            "mas": "owner_receipt_typed_blocker_and_closeout_authority",
        },
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["CLOSEOUT_REQUIRED_REASON", "closeout_first_admission"]

