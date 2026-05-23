from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


SURFACE_KIND = "mas_domain_authority_handoff"
SCHEMA_VERSION = 1


def build_domain_authority_handoff(
    *,
    study_id: str,
    quest_id: str | None,
    study_root: Path,
    owner_route: Mapping[str, Any],
    actions: list[dict[str, Any]],
    blocked_reason: str | None,
    next_owner: str | None,
    generated_at: str,
) -> dict[str, Any]:
    normalized_route = dict(owner_route)
    typed_blocker = _typed_blocker(
        study_id=study_id,
        quest_id=quest_id,
        blocked_reason=blocked_reason,
        next_owner=next_owner,
        owner_route=normalized_route,
        generated_at=generated_at,
    )
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "quest_id": quest_id,
        "study_root": str(Path(study_root).expanduser().resolve()),
        "generated_at": generated_at,
        "status": "typed_blocker" if typed_blocker is not None else "owner_route_ready",
        "owner_route": normalized_route or None,
        "typed_blocker": typed_blocker,
        "opl_control_plane": {
            "runtime_control_owner": "one-person-lab",
            "hydrate_owner_route_refs": True,
            "provider_completion_is_domain_completion": False,
            "queue_succeeded_is_domain_completion": False,
            "stage_attempt_state_owned_by_mas": False,
        },
        "action_refs": [
            {
                "action_id": _text(action.get("action_id")),
                "action_type": _text(action.get("action_type")),
                "next_owner": _text(action.get("next_executable_owner"))
                or _text(action.get("owner"))
                or _text(action.get("request_owner"))
                or _text(action.get("recommended_owner")),
                "owner_route_idempotency_key": _text(_mapping(action.get("owner_route")).get("idempotency_key")),
            }
            for action in actions
            if isinstance(action, Mapping)
        ],
        "authority": {
            "kind": "domain_authority_refs_only_handoff",
            "writes_runtime_attempt_state": False,
            "owns_generic_queue": False,
            "owns_retry_dead_letter": False,
            "quality_ready_authorized": False,
            "publication_ready_authorized": False,
            "submission_ready_authorized": False,
        },
    }


def projection_error_handoff(
    *,
    study_id: str,
    study_root: Path,
    generated_at: str,
    reason: str,
    error: Exception,
) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "study_id": study_id,
        "quest_id": None,
        "study_root": str(Path(study_root).expanduser().resolve()),
        "generated_at": generated_at,
        "status": "typed_blocker",
        "owner_route": None,
        "typed_blocker": {
            "surface_kind": "mas_domain_typed_blocker",
            "blocker_kind": "projection_contract_error",
            "reason": reason,
            "next_owner": "repo_controller_repair",
            "error_type": type(error).__name__,
            "message": str(error),
            "provider_completion_is_domain_completion": False,
        },
        "opl_control_plane": {
            "runtime_control_owner": "one-person-lab",
            "hydrate_owner_route_refs": False,
            "provider_completion_is_domain_completion": False,
            "queue_succeeded_is_domain_completion": False,
            "stage_attempt_state_owned_by_mas": False,
        },
        "action_refs": [],
        "authority": {
            "kind": "domain_authority_refs_only_handoff",
            "writes_runtime_attempt_state": False,
            "owns_generic_queue": False,
            "owns_retry_dead_letter": False,
            "quality_ready_authorized": False,
            "publication_ready_authorized": False,
            "submission_ready_authorized": False,
        },
    }


def _typed_blocker(
    *,
    study_id: str,
    quest_id: str | None,
    blocked_reason: str | None,
    next_owner: str | None,
    owner_route: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any] | None:
    reason = _text(blocked_reason)
    if reason is None:
        return None
    return {
        "surface_kind": "mas_domain_typed_blocker",
        "blocker_kind": "owner_route_blocked",
        "study_id": study_id,
        "quest_id": quest_id,
        "generated_at": generated_at,
        "reason": reason,
        "next_owner": _text(next_owner) or _text(owner_route.get("next_owner")),
        "route_epoch": _text(owner_route.get("route_epoch")),
        "source_fingerprint": _text(owner_route.get("source_fingerprint")),
        "idempotency_key": _text(owner_route.get("idempotency_key")),
        "provider_completion_is_domain_completion": False,
    }


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_domain_authority_handoff",
    "projection_error_handoff",
]
