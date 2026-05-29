from __future__ import annotations

from typing import Any, Mapping, Sequence

from med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export_parts.closeout_io import (
    closeout_authority_boundary,
    default_executor_execution_history_ref,
    default_executor_execution_latest_ref,
    dispatch_packet_refs,
    read_dispatch_packet,
    read_json_object,
    relative_stage_attempt_closeout_ref,
    workspace_relative_ref,
    write_json_object,
)
from med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export_parts.shared import (
    mapping,
    sequence,
    text,
    texts,
    unique,
)


def materialize_blocked_default_executor_closeout(
    *,
    profile: Any,
    study_id: str,
    target_identity: Mapping[str, Any],
    dispatch_identity: Mapping[str, Any],
    action_type: str,
    closeout_path: Any,
) -> dict[str, Any] | None:
    stage_attempt_id = text(target_identity.get("stage_attempt_id"))
    if stage_attempt_id is None:
        return None
    execution = _matching_blocked_default_executor_execution(
        profile=profile,
        study_id=study_id,
        dispatch_identity=dispatch_identity,
        action_type=action_type,
    )
    if execution is None:
        return None
    closeout_ref = relative_stage_attempt_closeout_ref(
        study_id=study_id,
        stage_attempt_id=stage_attempt_id,
    )
    dispatch_ref = text(dispatch_identity.get("dispatch_ref"))
    dispatch_packet = read_dispatch_packet(profile=profile, dispatch_ref=dispatch_ref)
    blocked_reason = text(execution.get("blocked_reason"))
    next_owner = (
        text(mapping(execution.get("current_owner_route")).get("next_owner"))
        or text(execution.get("next_owner"))
        or "med-autoscience"
    )
    generated_at = text(execution.get("generated_at"))
    closeout = {
        "surface_kind": "stage_attempt_closeout_packet",
        "schema_version": 1,
        "stage_attempt_id": stage_attempt_id,
        "stage_id": text(target_identity.get("stage_id")),
        "stage_packet_ref": dispatch_ref,
        "study_id": study_id,
        "quest_id": text(execution.get("quest_id")) or study_id,
        "action_type": action_type,
        "closeout_id": f"stage-attempt-closeout::{stage_attempt_id}::{blocked_reason}",
        "status": "blocked",
        "blocked_reason": blocked_reason,
        "domain_blocker": {
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "blocker_kind": "default_executor_execution_blocked",
            "reason": blocked_reason,
            "next_owner": next_owner,
            "action_type": action_type,
            "study_id": study_id,
            "quest_id": text(execution.get("quest_id")) or study_id,
            "stage_attempt_id": stage_attempt_id,
            "stage_packet_ref": dispatch_ref,
            "blocked_at": generated_at,
            "provider_completion_is_domain_completion": False,
            "authority_boundary": closeout_authority_boundary(),
        },
        "execution_observation": {
            "execution_ref": default_executor_execution_latest_ref(study_id),
            "execution_status": text(execution.get("execution_status")),
            "blocked_reason": blocked_reason,
            "execution_id": text(execution.get("execution_id")),
            "owner_callable_surface": text(execution.get("owner_callable_surface")),
        },
        "domain_execution": {
            "action_type": action_type,
            "execution_status": text(execution.get("execution_status")),
            "blocked_reason": blocked_reason,
            "domain_owner": next_owner,
            "execution_id": text(execution.get("execution_id")),
        },
        "closeout_refs": unique(
            texts(
                [
                    closeout_ref,
                    default_executor_execution_latest_ref(study_id),
                    default_executor_execution_history_ref(study_id),
                    dispatch_ref,
                    *dispatch_packet_refs(
                        dispatch_ref=dispatch_ref,
                        dispatch_packet=dispatch_packet,
                        workspace_root=profile.workspace_root,
                    ),
                ]
            )
        ),
        "typed_blocker_ref": f"{closeout_ref}#domain_blocker",
        "owner_receipt_ref": None,
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "domain_completion_claimed": False,
        "domain_ready_claimed": False,
        "publication_ready_claimed": False,
        "artifact_mutation_authorized": False,
        "current_package_mutation_authorized": False,
        "authority_boundary": closeout_authority_boundary(),
    }
    write_json_object(closeout_path, closeout)
    return closeout


def _matching_blocked_default_executor_execution(
    *,
    profile: Any,
    study_id: str,
    dispatch_identity: Mapping[str, Any],
    action_type: str,
) -> dict[str, Any] | None:
    latest_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )
    latest = read_json_object(latest_path)
    if latest is None:
        return None
    dispatch_ref = text(dispatch_identity.get("dispatch_ref"))
    dispatch_packet = read_dispatch_packet(profile=profile, dispatch_ref=dispatch_ref)
    candidates = [*sequence(latest.get("executions")), *reversed(sequence(latest.get("execution_ledger")))]
    valid_candidates = [
        dict(candidate)
        for candidate in candidates
        if isinstance(candidate, Mapping)
        and text(candidate.get("study_id")) == study_id
        and text(candidate.get("action_type")) == action_type
        and text(candidate.get("execution_status")) == "blocked"
        and text(candidate.get("blocked_reason")) is not None
    ]
    if dispatch_ref is None:
        return None
    for execution in valid_candidates:
        if _execution_dispatch_matches_profile_ref(
            execution=execution,
            dispatch_ref=dispatch_ref,
            workspace_root=profile.workspace_root,
        ):
            return execution
    if not _dispatch_packet_matches_identity(
        dispatch_packet=dispatch_packet,
        study_id=study_id,
        action_type=action_type,
    ):
        return None
    for execution in valid_candidates:
        if _execution_matches_dispatch_packet_binding(
            execution=execution,
            dispatch_ref=dispatch_ref,
            dispatch_packet=dispatch_packet,
            workspace_root=profile.workspace_root,
        ):
            return execution
    return None


def _dispatch_packet_matches_identity(
    *,
    dispatch_packet: Mapping[str, Any] | None,
    study_id: str,
    action_type: str,
) -> bool:
    if dispatch_packet is None:
        return False
    return (
        text(dispatch_packet.get("study_id")) == study_id
        and text(dispatch_packet.get("action_type")) == action_type
    )


def _execution_matches_dispatch_packet_binding(
    *,
    execution: Mapping[str, Any],
    dispatch_ref: str,
    dispatch_packet: Mapping[str, Any] | None,
    workspace_root: Any,
) -> bool:
    if dispatch_packet is None:
        return False
    if _execution_dispatch_matches_any_ref(
        execution=execution,
        dispatch_refs=dispatch_packet_refs(
            dispatch_ref=dispatch_ref,
            dispatch_packet=dispatch_packet,
            workspace_root=workspace_root,
        ),
        workspace_root=workspace_root,
    ):
        return True
    dispatch_idempotency_key = _binding_text(dispatch_packet, "idempotency_key")
    execution_idempotency_key = _binding_text(execution, "idempotency_key")
    if dispatch_idempotency_key is not None and dispatch_idempotency_key == execution_idempotency_key:
        return True
    dispatch_action_fingerprint = _binding_text(dispatch_packet, "action_fingerprint")
    execution_action_fingerprint = _binding_text(execution, "action_fingerprint")
    return dispatch_action_fingerprint is not None and dispatch_action_fingerprint == execution_action_fingerprint


def _binding_text(payload: Mapping[str, Any], key: str) -> str | None:
    return (
        text(payload.get(key))
        or text(mapping(payload.get("prompt_contract")).get(key))
        or text(mapping(payload.get("owner_route")).get(key))
    )


def _execution_dispatch_matches_any_ref(
    *,
    execution: Mapping[str, Any],
    dispatch_refs: Sequence[str],
    workspace_root: Any,
) -> bool:
    return any(
        _execution_dispatch_matches_profile_ref(
            execution=execution,
            dispatch_ref=dispatch_ref,
            workspace_root=workspace_root,
        )
        for dispatch_ref in dispatch_refs
    )


def _execution_dispatch_matches_profile_ref(
    *,
    execution: Mapping[str, Any],
    dispatch_ref: str,
    workspace_root: Any,
) -> bool:
    execution_dispatch_path = text(execution.get("dispatch_path"))
    if execution_dispatch_path is None:
        return False
    if execution_dispatch_path == dispatch_ref:
        return True
    workspace_relative = workspace_relative_ref(execution_dispatch_path, workspace_root=workspace_root)
    return workspace_relative == dispatch_ref
