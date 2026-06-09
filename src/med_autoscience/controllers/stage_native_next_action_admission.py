from __future__ import annotations

from collections.abc import Mapping
from typing import Any


STAGE_NATIVE_WORKSPACE_NEXT_ACTION_AUTHORITY = "stage_native_workspace_next_action"
STAGE_NATIVE_WORKSPACE_NEXT_ACTION_DIAGNOSTIC_AUTHORITY = (
    "stage_native_workspace_next_action_diagnostic_only"
)
STAGE_NATIVE_NEXT_ACTION_ADMISSION_POLICY = (
    "requires_canonical_current_work_unit_or_opl_stage_transition_authority_binding"
)
STAGE_NATIVE_NEXT_ACTION_BLOCKED_REASON = (
    "stage_native_workspace_next_action_requires_authority_binding"
)
STAGE_TRANSITION_AUTHORITIES = frozenset({"one-person-lab", "OPL Stage Transition Authority"})


def next_action_admission(next_action: Mapping[str, Any]) -> dict[str, Any]:
    authority_boundary = _mapping(next_action.get("stage_transition_authority_boundary"))
    current_work_unit_binding = _mapping(next_action.get("current_work_unit_binding"))
    has_stage_authority_binding = (
        _text(authority_boundary.get("stage_transition_authority")) in STAGE_TRANSITION_AUTHORITIES
        and authority_boundary.get("intent_can_write_stage_current_pointer") is False
        and authority_boundary.get("intent_can_write_stage_run_terminal_state") is False
        and authority_boundary.get("intent_can_publish_current_owner_delta") is False
    )
    has_current_work_unit_binding = (
        _text(current_work_unit_binding.get("source")) == "canonical_current_work_unit"
        and _text(current_work_unit_binding.get("work_unit_id")) is not None
        and _text(current_work_unit_binding.get("work_unit_fingerprint")) is not None
    )
    allowed = has_stage_authority_binding and has_current_work_unit_binding
    return {
        "policy": STAGE_NATIVE_NEXT_ACTION_ADMISSION_POLICY,
        "default_dispatch_allowed": allowed,
        "blocked_reason": None if allowed else STAGE_NATIVE_NEXT_ACTION_BLOCKED_REASON,
        "has_stage_transition_authority_boundary": has_stage_authority_binding,
        "has_current_work_unit_binding": has_current_work_unit_binding,
        "stage_run_current_authority": _text(next_action.get("stage_run_current_authority")),
        "source_surface": _text(next_action.get("source_surface")) or "control/next_action.json",
    }


def stage_transition_authority_boundary() -> dict[str, Any]:
    return {
        "producer_kind": "runtime_provider",
        "intent_kind": "provider_observation",
        "stage_transition_authority": "one-person-lab",
        "intent_can_write_stage_current_pointer": False,
        "intent_can_write_stage_run_terminal_state": False,
        "intent_can_publish_current_owner_delta": False,
        "intent_can_write_domain_truth": False,
        "intent_can_create_owner_receipt": False,
        "intent_can_create_typed_blocker": False,
        "provider_completion_counts_as_stage_transition": False,
        "read_model_update_counts_as_stage_transition": False,
        "worklist_update_counts_as_stage_transition": False,
        "evidence_event_counts_as_stage_transition": False,
        "agent_lab_output_counts_as_stage_transition": False,
    }


def build_current_work_unit_binding(
    *,
    action_type: str,
    current_stage_id: str,
    source_surface: str,
) -> dict[str, str]:
    return {
        "source": "canonical_current_work_unit",
        "work_unit_id": action_type,
        "work_unit_fingerprint": stage_native_fingerprint(
            action_type=action_type,
            current_stage_id=current_stage_id,
            source_surface=source_surface,
        ),
    }


def stage_native_fingerprint(
    *,
    action_type: str,
    current_stage_id: str,
    source_surface: str,
) -> str:
    return f"stage-native-next-action::{current_stage_id}::{action_type}::{source_surface}"


def default_dispatch_allowed(next_action: Mapping[str, Any]) -> bool:
    return next_action_admission(next_action)["default_dispatch_allowed"] is True


def action_default_dispatch_allowed(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("authority")) == STAGE_NATIVE_WORKSPACE_NEXT_ACTION_AUTHORITY
        and action.get("default_dispatch_allowed") is True
    )


def current_work_unit_binding(next_action: Mapping[str, Any]) -> dict[str, Any]:
    binding = _mapping(next_action.get("current_work_unit_binding"))
    return binding if _text(binding.get("source")) == "canonical_current_work_unit" else {}


def work_unit_id(next_action: Mapping[str, Any], *, fallback: str) -> str:
    return _text(current_work_unit_binding(next_action).get("work_unit_id")) or fallback


def work_unit_fingerprint(next_action: Mapping[str, Any], *, fallback: str) -> str:
    return _text(current_work_unit_binding(next_action).get("work_unit_fingerprint")) or fallback


def dispatch_uses_stage_native_next_action(dispatch: Mapping[str, Any]) -> bool:
    source_action = _mapping(dispatch.get("source_action"))
    return _text(source_action.get("authority")) == STAGE_NATIVE_WORKSPACE_NEXT_ACTION_AUTHORITY


def ignored_reason(action: Mapping[str, Any]) -> str:
    return _text(action.get("default_dispatch_blocked_reason")) or STAGE_NATIVE_NEXT_ACTION_BLOCKED_REASON


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "STAGE_NATIVE_NEXT_ACTION_BLOCKED_REASON",
    "STAGE_NATIVE_NEXT_ACTION_ADMISSION_POLICY",
    "STAGE_NATIVE_WORKSPACE_NEXT_ACTION_AUTHORITY",
    "STAGE_NATIVE_WORKSPACE_NEXT_ACTION_DIAGNOSTIC_AUTHORITY",
    "action_default_dispatch_allowed",
    "build_current_work_unit_binding",
    "current_work_unit_binding",
    "default_dispatch_allowed",
    "dispatch_uses_stage_native_next_action",
    "ignored_reason",
    "next_action_admission",
    "stage_native_fingerprint",
    "stage_transition_authority_boundary",
    "work_unit_fingerprint",
    "work_unit_id",
]
