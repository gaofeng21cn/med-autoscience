from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile

from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)
from med_autoscience.controllers import study_transition_receipt_consumption
from med_autoscience.controllers import default_executor_dispatch_packets
from med_autoscience.controllers.default_executor_action_policy import REQUEST_OWNER_BY_ACTION_TYPE
from med_autoscience.controllers.domain_health_diagnostic_parts import provider_admission
from med_autoscience.controllers.study_transition_receipt_consumption_parts import (
    nonconsumable_redrive_budget,
)
from med_autoscience.runtime_control import owner_route_attempt_protocol


TASK_KIND = "domain_owner/default-executor-dispatch"
DISPATCH_RELATIVE_ROOT = Path("artifacts/supervision/consumer/default_executor_dispatches")
REQUIRED_SURFACE = "default_executor_dispatch_request"
REQUIRED_EXECUTOR_KIND = "codex_cli_default"
READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"
DEFAULT_NEXT_OWNER = "write"
ALLOWED_NEXT_OWNERS = frozenset({*REQUEST_OWNER_BY_ACTION_TYPE.values(), "write/ai_reviewer"})
OWNER_RECEIPT_CONTRACT = "mas-default-executor-owner-receipt.v1"


def default_executor_dispatch_tasks(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
    current_owner_action: Mapping[str, Any] | None = None,
    current_work_unit: Mapping[str, Any] | None = None,
    current_execution_envelope: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    dispatch_root = profile.studies_root / study_id / DISPATCH_RELATIVE_ROOT
    if not dispatch_root.is_dir():
        return []
    canonical_identity = _canonical_current_dispatch_identity(
        current_owner_action=_mapping(current_owner_action),
        current_work_unit=_mapping(current_work_unit),
        current_execution_envelope=_mapping(current_execution_envelope),
    )
    if canonical_identity.get("blocked") is True:
        return []
    tasks: list[dict[str, Any]] = []
    provider_admission_candidates = provider_admission.persisted_provider_admission_candidates(
        study_root=profile.studies_root / study_id,
        status_payload=_provider_admission_status_payload(
            study_id=study_id,
            current_owner_action=_mapping(current_owner_action),
            current_work_unit=_mapping(current_work_unit),
            current_execution_envelope=_mapping(current_execution_envelope),
        ),
    )
    candidates = _current_dispatch_candidates(
        dispatch_root,
        profile=profile,
        study_id=study_id,
        current_owner_action=current_owner_action,
        canonical_identity=canonical_identity,
        provider_admission_candidates=provider_admission_candidates,
    )
    for candidate in candidates:
        dispatch_path = candidate["path"]
        dispatch = candidate["dispatch"]
        if not isinstance(dispatch_path, Path) or not isinstance(dispatch, Mapping):
            continue
        if candidate.get("persist_current_owner_action_identity") is True:
            dispatch = _persist_dispatch_packet_identity(
                dispatch_path=dispatch_path,
                dispatch=dispatch,
            )
        action_type = _text(dispatch.get("action_type"))
        if action_type is None:
            continue
        redrive_context = _dispatch_execution_redrive_context(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch,
            action_type=action_type,
        )
        dispatch_authority = _text(dispatch.get("dispatch_authority")) or "consumer_default_executor_dispatch"
        stage_packet_path = default_executor_dispatch_packets.dispatch_stage_packet_path(
            dispatch,
            fallback_dispatch_path=dispatch_path,
        )
        if not stage_packet_path.is_file():
            continue
        dispatch_ref = _workspace_relative(stage_packet_path, workspace_root=profile.workspace_root)
        latest_dispatch_ref = _workspace_relative(dispatch_path, workspace_root=profile.workspace_root)
        owner_route_attempt_envelope = owner_route_attempt_protocol.default_executor_attempt_envelope(
            dispatch=dispatch
        )
        if owner_route_attempt_envelope.get("dispatchable") is not True:
            continue
        protocol_payload_fields = owner_route_attempt_protocol.payload_fields_for_default_executor_dispatch(
            dispatch=dispatch
        )
        readiness_surface_identity = _readiness_surface_identity(
            action_type=action_type,
            current_owner_action=_mapping(current_owner_action),
        )
        dispatch_for_task = _dispatch_with_readiness_surface_identity(
            dispatch=dispatch,
            readiness_surface_identity=readiness_surface_identity,
        )
        if dispatch_for_task is not dispatch:
            dispatch = dispatch_for_task
            _persist_dispatch_identity(
                profile=profile,
                study_id=study_id,
                dispatch_path=dispatch_path,
                stage_packet_path=stage_packet_path,
                dispatch=dispatch,
            )
        prompt_contract_ref = f"{dispatch_ref}#prompt_contract"
        source_refs = _source_refs(
            dispatch=dispatch,
            dispatch_ref=dispatch_ref,
            latest_dispatch_ref=latest_dispatch_ref,
            prompt_contract_ref=prompt_contract_ref,
            workspace_root=profile.workspace_root,
            redrive_context=redrive_context,
        )
        quest_id = _text(dispatch.get("quest_id")) or study_id
        next_owner = _next_executable_owner(dispatch) or DEFAULT_NEXT_OWNER
        executor_kind = _text(dispatch.get("executor_kind")) or REQUIRED_EXECUTOR_KIND
        owner_route_basis = _mapping(protocol_payload_fields.get("owner_route_currentness_basis"))
        work_unit_id = _text(protocol_payload_fields.get("work_unit_id")) or _text(owner_route_basis.get("work_unit_id"))
        work_unit_fingerprint = _text(owner_route_basis.get("work_unit_fingerprint"))
        provider_admission_identity = _matching_provider_admission_identity(
            candidates=provider_admission_candidates,
            action_type=action_type,
            work_unit_id=work_unit_id,
            dispatch_path=dispatch_path,
            stage_packet_path=stage_packet_path,
            workspace_root=profile.workspace_root,
        )
        provider_payload_fields = _provider_admission_payload_fields(
            provider_admission_identity=provider_admission_identity,
            owner_route_basis=owner_route_basis,
        )
        work_unit_id = _text(provider_payload_fields.get("work_unit_id")) or work_unit_id
        work_unit_fingerprint = (
            _text(provider_payload_fields.get("work_unit_fingerprint"))
            or work_unit_fingerprint
        )
        source_fingerprint = (
            _text(provider_payload_fields.get("source_fingerprint"))
            or _source_fingerprint(
                dispatch=dispatch,
                dispatch_path=stage_packet_path,
                redrive_context=redrive_context,
                readiness_surface_identity=readiness_surface_identity,
            )
        )
        evidence_record_payload = build_domain_dispatch_evidence_record_payload(
            task_kind=TASK_KIND,
            study_id=study_id,
            reason="default_executor_owner_receipt_or_typed_closeout_pending",
            evidence_refs=source_refs,
            source_fingerprint=source_fingerprint,
            profile_name=profile.name,
        )
        tasks.append(
            {
                "domain_id": "medautoscience",
                "task_kind": TASK_KIND,
                "study_id": study_id,
                "quest_id": quest_id,
                "action_type": action_type,
                "domain_owner": next_owner,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "priority": 65,
                "source": "mas-domain-handler-export",
                "requires_approval": False,
                "dedupe_key": (
                    f"mas:{profile.name}:{study_id}:default-executor:"
                    f"{action_type}:{dispatch_authority}:{source_fingerprint}"
                ),
                "source_fingerprint": source_fingerprint,
                "payload": {
                    "profile": str(profile_ref),
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "action_type": action_type,
                    **protocol_payload_fields,
                    **provider_payload_fields,
                    **(
                        {"work_unit_fingerprint": work_unit_fingerprint}
                        if work_unit_fingerprint is not None
                        else {}
                    ),
                    "dispatch_authority": dispatch_authority,
                    "executor_kind": executor_kind,
                    "dispatch_ref": dispatch_ref,
                    "authority_boundary": "mas_default_executor_dispatch_request_only",
                    "next_executable_owner": next_owner,
                    **(
                        {"readiness_surface_identity": readiness_surface_identity}
                        if readiness_surface_identity
                        else {}
                    ),
                    **(
                        {"provider_admission_identity": provider_admission_identity}
                        if provider_admission_identity
                        else {}
                    ),
                    **({"redrive_context": redrive_context} if redrive_context else {}),
                },
                "source_refs": source_refs,
                "owner_route_attempt_envelope": owner_route_attempt_envelope,
                "dispatch_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "queue_owner": "one-person-lab",
                "profile_name": profile.name,
                **(
                    {"provider_admission_identity": provider_admission_identity}
                    if provider_admission_identity
                    else {}
                ),
                "domain_dispatch_evidence_record_payload": evidence_record_payload,
            }
        )
    return tasks


def _provider_admission_status_payload(
    *,
    study_id: str,
    current_owner_action: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_execution_envelope: Mapping[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {"study_id": study_id}
    if current_work_unit:
        payload["current_work_unit"] = dict(current_work_unit)
    if current_execution_envelope:
        payload["current_execution_envelope"] = dict(current_execution_envelope)
    if current_owner_action:
        payload["current_executable_owner_action"] = dict(current_owner_action)
    return payload


def _canonical_current_dispatch_identity(
    *,
    current_owner_action: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_execution_envelope: Mapping[str, Any],
) -> dict[str, Any]:
    work_unit_status = _text(current_work_unit.get("status"))
    envelope_state = _text(current_execution_envelope.get("state_kind")) or _text(
        current_execution_envelope.get("execution_state_kind")
    )
    if work_unit_status in {
        "typed_blocker",
        "running_provider_attempt",
        "blocked_current_work_unit",
        "blocked_typed_owner",
        "parked",
    }:
        return {"blocked": True, "source": "current_work_unit", "state_kind": work_unit_status}
    if envelope_state in {
        "typed_blocker",
        "running_provider_attempt",
        "blocked_current_work_unit",
        "blocked_typed_owner",
        "parked",
    }:
        return {"blocked": True, "source": "current_execution_envelope", "state_kind": envelope_state}
    if work_unit_status == "executable_owner_action":
        identity = _current_work_unit_dispatch_identity(current_work_unit)
        if identity:
            return identity
        return {"blocked": True, "source": "current_work_unit", "state_kind": work_unit_status}
    if envelope_state == "executable_owner_action" and current_owner_action:
        identity = _current_owner_action_dispatch_identity(current_owner_action)
        if identity:
            identity["source"] = "current_execution_envelope"
            return identity
        return {"blocked": True, "source": "current_execution_envelope", "state_kind": envelope_state}
    if current_owner_action:
        identity = _current_owner_action_dispatch_identity(current_owner_action)
        if identity:
            return identity
    return {}


def _current_work_unit_dispatch_identity(current_work_unit: Mapping[str, Any]) -> dict[str, Any]:
    action_type = _text(current_work_unit.get("action_type"))
    work_unit_id = _text(current_work_unit.get("work_unit_id"))
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    fingerprint = (
        _text(current_work_unit.get("work_unit_fingerprint"))
        or _text(current_work_unit.get("action_fingerprint"))
        or _text(currentness_basis.get("work_unit_fingerprint"))
        or _text(currentness_basis.get("source_fingerprint"))
    )
    action_ids = [item for item in (action_type, work_unit_id) if item is not None]
    if action_type is None or work_unit_id is None:
        return {}
    return {
        "source": "current_work_unit",
        "action_type": action_type,
        "action_ids": action_ids,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }


def _current_owner_action_dispatch_identity(current_owner_action: Mapping[str, Any]) -> dict[str, Any]:
    action_type = _text(current_owner_action.get("action_type"))
    next_action = _mapping(current_owner_action.get("next_action"))
    work_unit_id = _text(current_owner_action.get("work_unit_id")) or _text(next_action.get("action_id"))
    basis = _mapping(current_owner_action.get("owner_route_currentness_basis"))
    fingerprint = (
        _text(current_owner_action.get("work_unit_fingerprint"))
        or _text(current_owner_action.get("action_fingerprint"))
        or _text(current_owner_action.get("source_fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(basis.get("source_fingerprint"))
    )
    action_ids = list(
        dict.fromkeys(
            [
                item
                for item in (
                    *_string_list(current_owner_action.get("allowed_actions")),
                    action_type,
                    work_unit_id,
                    _text(next_action.get("action_id")),
                )
                if item is not None
            ]
        )
    )
    if action_type is None or work_unit_id is None:
        return {}
    return {
        "source": _text(current_owner_action.get("source")) or "current_executable_owner_action",
        "action_type": action_type,
        "action_ids": action_ids,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }


def _matching_provider_admission_identity(
    *,
    candidates: list[Mapping[str, Any]],
    action_type: str,
    work_unit_id: str | None,
    dispatch_path: Path,
    stage_packet_path: Path,
    workspace_root: Path,
) -> dict[str, Any] | None:
    for candidate in candidates:
        if _text(candidate.get("action_type")) != action_type:
            continue
        candidate_work_unit = _text(candidate.get("work_unit_id"))
        if work_unit_id is not None and candidate_work_unit != work_unit_id:
            continue
        if not _candidate_dispatch_path_matches(
            candidate_dispatch_path=_text(candidate.get("dispatch_path")),
            dispatch_path=dispatch_path,
            stage_packet_path=stage_packet_path,
            workspace_root=workspace_root,
        ):
            continue
        return dict(candidate)
    return None


def _candidate_dispatch_path_matches(
    *,
    candidate_dispatch_path: str | None,
    dispatch_path: Path,
    stage_packet_path: Path,
    workspace_root: Path,
) -> bool:
    candidate = _normalized_path_text(candidate_dispatch_path)
    if candidate is None:
        return False
    expected_paths = {
        _normalized_path_text(str(dispatch_path)),
        _normalized_path_text(str(stage_packet_path)),
        _normalized_path_text(_workspace_relative(dispatch_path, workspace_root=workspace_root)),
        _normalized_path_text(_workspace_relative(stage_packet_path, workspace_root=workspace_root)),
    }
    expected = {path for path in expected_paths if path is not None}
    for path in expected:
        if candidate == path or candidate.endswith(f"/{path}") or path.endswith(f"/{candidate}"):
            return True
    return False


def _provider_admission_payload_fields(
    *,
    provider_admission_identity: Mapping[str, Any] | None,
    owner_route_basis: Mapping[str, Any],
) -> dict[str, Any]:
    identity = _mapping(provider_admission_identity)
    if not identity:
        return {}
    work_unit_id = _text(identity.get("work_unit_id"))
    work_unit_fingerprint = _text(identity.get("work_unit_fingerprint"))
    action_fingerprint = _text(identity.get("action_fingerprint")) or work_unit_fingerprint
    currentness_basis = dict(owner_route_basis)
    if work_unit_id is not None:
        currentness_basis["work_unit_id"] = work_unit_id
    if work_unit_fingerprint is not None:
        currentness_basis["work_unit_fingerprint"] = work_unit_fingerprint
    fields: dict[str, Any] = {
        "provider_admission_identity": dict(identity),
        "provider_admission_status": _text(identity.get("status")),
        "provider_admission_source": _text(identity.get("source")),
        "provider_admission_execution_ref": _text(identity.get("execution_ref")),
        "provider_attempt_or_lease_required": identity.get("provider_attempt_or_lease_required") is True,
        "owner_callable_surface": _text(identity.get("owner_callable_surface")),
    }
    if work_unit_id is not None:
        fields["work_unit_id"] = work_unit_id
    if work_unit_fingerprint is not None:
        fields["work_unit_fingerprint"] = work_unit_fingerprint
    if action_fingerprint is not None:
        fields["action_fingerprint"] = action_fingerprint
        fields["source_fingerprint"] = action_fingerprint
    if currentness_basis:
        fields["owner_route_currentness_basis"] = currentness_basis
    return {key: value for key, value in fields.items() if value is not None}


def _current_dispatch_candidates(
    dispatch_root: Path,
    *,
    profile: WorkspaceProfile,
    study_id: str,
    current_owner_action: Mapping[str, Any] | None = None,
    canonical_identity: Mapping[str, Any] | None = None,
    provider_admission_candidates: list[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    current_action = _mapping(current_owner_action)
    canonical = _mapping(canonical_identity)
    for dispatch_path in sorted(dispatch_root.glob("*.json")):
        dispatch = _read_json_object(dispatch_path)
        if not _dispatch_ready_for_opl_attempt(dispatch):
            continue
        action_type = _text(dispatch.get("action_type"))
        if action_type is None:
            continue
        persist_current_identity = False
        if current_action:
            dispatch_for_current_action = _dispatch_with_current_owner_action_identity(
                dispatch=dispatch,
                current_owner_action=current_action,
            )
            persist_current_identity = dispatch_for_current_action is not dispatch
            dispatch = dispatch_for_current_action
            if not _dispatch_matches_current_owner_action(dispatch, current_action):
                continue
        if canonical and not _dispatch_matches_canonical_current_identity(
            dispatch,
            canonical,
            dispatch_path=dispatch_path,
            provider_admission_candidates=provider_admission_candidates or [],
            workspace_root=profile.workspace_root,
        ):
            continue
        if _dispatch_execution_receipt_consumed(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch,
            action_type=action_type,
        ):
            continue
        candidates.append(
            {
                "path": dispatch_path,
                "dispatch": dispatch,
                "mtime_key": _dispatch_mtime_key(dispatch_path),
                "persist_current_owner_action_identity": persist_current_identity,
            }
        )
    if current_action or canonical:
        return candidates
    unresolved = [
        candidate
        for candidate in candidates
        if not _dispatch_blocked_by_newer_candidate(candidate, candidates)
    ]
    if len(unresolved) <= 1:
        return unresolved
    return [_newest_candidate(unresolved)]


def _dispatch_matches_canonical_current_identity(
    dispatch: Mapping[str, Any],
    canonical_identity: Mapping[str, Any],
    *,
    dispatch_path: Path,
    provider_admission_candidates: list[Mapping[str, Any]],
    workspace_root: Path,
) -> bool:
    if canonical_identity.get("blocked") is True:
        return False
    expected_action_type = _text(canonical_identity.get("action_type"))
    dispatch_action_type = _text(dispatch.get("action_type"))
    if expected_action_type is None or dispatch_action_type != expected_action_type:
        return False
    action_ids = set(_string_list(canonical_identity.get("action_ids")))
    if action_ids and dispatch_action_type not in action_ids:
        return False
    expected_work_unit_id = _text(canonical_identity.get("work_unit_id"))
    if expected_work_unit_id is None:
        return False
    owner_route = _dispatch_owner_route(dispatch)
    dispatch_work_unit_id = _owner_route_work_unit_id(owner_route)
    if dispatch_work_unit_id != expected_work_unit_id:
        return False
    allowed_actions = set(_string_list(owner_route.get("allowed_actions")))
    if allowed_actions and dispatch_action_type not in allowed_actions:
        return False
    expected_fingerprint = _text(canonical_identity.get("work_unit_fingerprint"))
    if expected_fingerprint is None:
        return True
    if _dispatch_work_unit_fingerprint(dispatch) == expected_fingerprint:
        return True
    stage_packet_path = default_executor_dispatch_packets.dispatch_stage_packet_path(
        dispatch,
        fallback_dispatch_path=dispatch_path,
    )
    provider_identity = _matching_provider_admission_identity(
        candidates=provider_admission_candidates,
        action_type=dispatch_action_type,
        work_unit_id=expected_work_unit_id,
        dispatch_path=dispatch_path,
        stage_packet_path=stage_packet_path,
        workspace_root=workspace_root,
    )
    if not provider_identity:
        return False
    provider_fingerprints = {
        text
        for value in (
            provider_identity.get("work_unit_fingerprint"),
            provider_identity.get("action_fingerprint"),
            provider_identity.get("source_fingerprint"),
        )
        if (text := _text(value)) is not None
    }
    return expected_fingerprint in provider_fingerprints


def _dispatch_matches_current_owner_action(
    dispatch: Mapping[str, Any],
    current_owner_action: Mapping[str, Any],
) -> bool:
    action_type = _text(dispatch.get("action_type"))
    current_action_type = _text(current_owner_action.get("action_type"))
    if action_type is None or current_action_type is None or action_type != current_action_type:
        return False
    current_work_unit_id = _text(current_owner_action.get("work_unit_id"))
    if current_work_unit_id is None:
        current_basis = _mapping(current_owner_action.get("owner_route_currentness_basis"))
        current_work_unit_id = _text(current_basis.get("work_unit_id"))
    if current_work_unit_id is None:
        return False
    dispatch_work_unit_id = _owner_route_work_unit_id(_dispatch_owner_route(dispatch))
    if dispatch_work_unit_id != current_work_unit_id:
        return False
    owner_route = _dispatch_owner_route(dispatch)
    allowed_actions = set(_string_list(owner_route.get("allowed_actions")))
    if allowed_actions and action_type not in allowed_actions:
        return False
    current_owner_route = _mapping(current_owner_action.get("owner_route"))
    current_allowed_actions = set(_string_list(current_owner_route.get("allowed_actions")))
    if current_allowed_actions and action_type not in current_allowed_actions:
        return False
    return True


def _dispatch_with_current_owner_action_identity(
    *,
    dispatch: Mapping[str, Any],
    current_owner_action: Mapping[str, Any],
) -> Mapping[str, Any]:
    action_type = _text(dispatch.get("action_type"))
    current_action_type = _text(current_owner_action.get("action_type"))
    if action_type is None or current_action_type is None or action_type != current_action_type:
        return dispatch
    if _dispatch_matches_current_owner_action(dispatch, current_owner_action):
        return dispatch
    current_owner_route = _mapping(current_owner_action.get("owner_route"))
    if not current_owner_route:
        return dispatch
    allowed_actions = set(_string_list(current_owner_route.get("allowed_actions")))
    if allowed_actions and action_type not in allowed_actions:
        return dispatch

    updated = dict(dispatch)
    updated["owner_route"] = dict(current_owner_route)
    if next_owner := (_text(current_owner_action.get("next_owner")) or _text(current_owner_route.get("next_owner"))):
        updated["next_executable_owner"] = next_owner
    if source := _text(current_owner_action.get("source")):
        updated["dispatch_authority"] = source
    source_fingerprint = _text(current_owner_route.get("source_fingerprint")) or _text(
        current_owner_route.get("work_unit_fingerprint")
    )
    if source_fingerprint is not None:
        updated["source_fingerprint"] = source_fingerprint
        updated["action_fingerprint"] = source_fingerprint

    prompt_contract = dict(_mapping(updated.get("prompt_contract")))
    prompt_contract["owner_route"] = dict(current_owner_route)
    prompt_contract["action_type"] = action_type
    if next_owner := _text(updated.get("next_executable_owner")):
        prompt_contract["next_executable_owner"] = next_owner
    if source_fingerprint is not None:
        prompt_contract["source_fingerprint"] = source_fingerprint
    updated["prompt_contract"] = prompt_contract
    return updated if updated != dict(dispatch) else dispatch


def _readiness_surface_identity(
    *,
    action_type: str,
    current_owner_action: Mapping[str, Any],
) -> dict[str, str] | None:
    if action_type != READINESS_ACTION_TYPE:
        return None
    if _text(current_owner_action.get("action_type")) != READINESS_ACTION_TYPE:
        return None
    target_surface = _mapping(current_owner_action.get("target_surface"))
    next_action = _mapping(current_owner_action.get("next_action"))
    surface_key = (
        _text(current_owner_action.get("surface_key"))
        or _text(target_surface.get("surface_key"))
        or _text(next_action.get("surface_key"))
    )
    if surface_key is None:
        return None
    return {
        "action_type": READINESS_ACTION_TYPE,
        "surface_key": surface_key,
        "source": _text(current_owner_action.get("source")) or "current_owner_action",
    }


def _dispatch_with_readiness_surface_identity(
    *,
    dispatch: Mapping[str, Any],
    readiness_surface_identity: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    identity = _mapping(readiness_surface_identity)
    surface_key = _text(identity.get("surface_key"))
    if surface_key is None:
        return dispatch
    previous_surface_key = _declared_surface_key(dispatch)
    updated = dict(dispatch)
    updated["readiness_surface_identity"] = {
        "action_type": _text(identity.get("action_type")) or READINESS_ACTION_TYPE,
        "surface_key": surface_key,
        "source": _text(identity.get("source")) or "current_owner_action",
    }
    updated["surface_key"] = surface_key
    prompt_contract = dict(_mapping(updated.get("prompt_contract")))
    prompt_contract["readiness_surface_identity"] = dict(updated["readiness_surface_identity"])
    prompt_contract["surface_key"] = surface_key
    updated["prompt_contract"] = prompt_contract
    if previous_surface_key is not None and previous_surface_key != surface_key:
        updated = _drop_stale_readiness_payloads(dispatch=updated, surface_key=surface_key)
    target = dict(_mapping(updated.get("payload_authoring_target")))
    if target:
        target["readiness_surface_identity"] = dict(updated["readiness_surface_identity"])
        target["surface_key"] = surface_key
        contract = dict(_mapping(target.get("operator_payload_contract")))
        if contract:
            contract["surface_key"] = surface_key
            target["operator_payload_contract"] = contract
        payload = dict(_mapping(target.get("operator_payload")))
        if payload:
            payload["surface_key"] = surface_key
            target["operator_payload"] = payload
        updated["payload_authoring_target"] = target
    if updated == dict(dispatch):
        return dispatch
    return updated


def _drop_stale_readiness_payloads(*, dispatch: dict[str, Any], surface_key: str) -> dict[str, Any]:
    prompt_contract = dict(_mapping(dispatch.get("prompt_contract")))
    for container in (dispatch, prompt_contract):
        for key in ("operator_payload", "medical_paper_readiness_payload"):
            payload = _mapping(container.get(key))
            if payload and not _payload_matches_surface(payload=payload, surface_key=surface_key):
                container.pop(key, None)
        container["operator_payload_present"] = bool(
            _mapping(container.get("operator_payload")) or _mapping(container.get("medical_paper_readiness_payload"))
        )
        target = dict(_mapping(container.get("payload_authoring_target")))
        if target:
            target["surface_key"] = surface_key
            target["readiness_surface_identity"] = dict(dispatch["readiness_surface_identity"])
            contract = dict(_mapping(target.get("operator_payload_contract")))
            if contract:
                contract["surface_key"] = surface_key
                target["operator_payload_contract"] = contract
            payload = _mapping(target.get("operator_payload"))
            if payload and not _payload_matches_surface(payload=payload, surface_key=surface_key):
                target.pop("operator_payload", None)
            container["payload_authoring_target"] = target
    dispatch["prompt_contract"] = prompt_contract
    return dispatch


def _payload_matches_surface(*, payload: Mapping[str, Any], surface_key: str) -> bool:
    payload_surface_key = _payload_surface_key(payload)
    return payload_surface_key == surface_key


def _payload_surface_key(payload: Mapping[str, Any]) -> str | None:
    if text := _text(payload.get("surface_key")):
        return text
    surface = _text(payload.get("surface"))
    aliases = {
        "literature_intelligence_os": "literature_scout",
        "study_line_decision": "study_line_selection",
        "study_line_selection_scorecard": "study_line_selection",
        "archetype_specific_analysis_contract": "archetype_analysis_contract",
        "route_control_stoploss": "stop_loss_memo",
        "target_journal_writing_layer": "target_journal_writing_layer",
    }
    if surface in aliases:
        return aliases[surface]
    return surface


def _declared_surface_key(dispatch: Mapping[str, Any]) -> str | None:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    for payload in (dispatch, prompt_contract):
        identity = _mapping(payload.get("readiness_surface_identity"))
        if text := _text(identity.get("surface_key")):
            return text
        if text := _text(payload.get("surface_key")):
            return text
    return None


def _dispatch_blocked_by_newer_candidate(
    candidate: Mapping[str, Any],
    candidates: list[Mapping[str, Any]],
) -> bool:
    dispatch = _mapping(candidate.get("dispatch"))
    action_type = _text(dispatch.get("action_type"))
    if action_type is None:
        return False
    owner_route = _dispatch_owner_route(dispatch)
    for other_candidate in candidates:
        if other_candidate is candidate:
            continue
        other = _mapping(other_candidate.get("dispatch"))
        other_route = _dispatch_owner_route(other)
        if action_type not in set(_string_list(other_route.get("blocked_actions"))):
            continue
        if not _candidate_newer_than(other_candidate, candidate):
            continue
        return True
    return False


def _newest_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    selected = candidates[0]
    for candidate in candidates[1:]:
        if _candidate_newer_than(candidate, selected):
            selected = candidate
    return selected


def _candidate_newer_than(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_dispatch = _mapping(left.get("dispatch"))
    right_dispatch = _mapping(right.get("dispatch"))
    left_time = _dispatch_generated_time_key(left_dispatch)
    right_time = _dispatch_generated_time_key(right_dispatch)
    if left_time is not None and right_time is not None:
        return _dispatch_currentness_key(left_dispatch, time_key=left_time) > _dispatch_currentness_key(
            right_dispatch,
            time_key=right_time,
        )
    left_route_key = _dispatch_route_currentness_key(
        left_dispatch,
        mtime_key=_text(left.get("mtime_key")) or "",
    )
    right_route_key = _dispatch_route_currentness_key(
        right_dispatch,
        mtime_key=_text(right.get("mtime_key")) or "",
    )
    return left_route_key > right_route_key


def _dispatch_ready_for_opl_attempt(dispatch: Mapping[str, Any] | None) -> bool:
    if dispatch is None:
        return False
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    refs = _mapping(dispatch.get("refs"))
    if not (
        _text(dispatch.get("surface")) == REQUIRED_SURFACE
        and _text(dispatch.get("dispatch_status")) == "ready"
        and _text(dispatch.get("executor_kind")) == REQUIRED_EXECUTOR_KIND
        and _next_executable_owner(dispatch) in ALLOWED_NEXT_OWNERS
        and bool(owner_route)
        and _text(refs.get("dispatch_path")) is not None
    ):
        return False
    envelope = owner_route_attempt_protocol.default_executor_attempt_envelope(dispatch=dispatch)
    return envelope.get("dispatchable") is True


def _dispatch_execution_receipt_consumed(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
    action_type: str,
) -> bool:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    if not owner_route:
        return False
    receipt = study_transition_receipt_consumption.default_executor_execution_receipt_consumption(
        study_root=profile.studies_root / study_id,
        owner_route=owner_route,
        actions=[{"action_type": action_type}],
    )
    if _receipt_is_synthetic_nonconsumable_budget(receipt) and _stage_native_owner_route(owner_route):
        return False
    return bool(receipt)


def _dispatch_execution_redrive_context(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
    action_type: str,
) -> dict[str, Any]:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    if not owner_route:
        return {}
    return study_transition_receipt_consumption.default_executor_execution_nonconsumable_closeout(
        study_root=profile.studies_root / study_id,
        owner_route=owner_route,
        actions=[{"action_type": action_type}],
    )


def _next_executable_owner(dispatch: Mapping[str, Any]) -> str | None:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    return (
        _text(dispatch.get("next_executable_owner"))
        or _text(prompt_contract.get("next_executable_owner"))
        or _text(owner_route.get("next_owner"))
    )


def _dispatch_owner_route(dispatch: Mapping[str, Any]) -> Mapping[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    return _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))


def _owner_route_work_unit_id(owner_route: Mapping[str, Any]) -> str | None:
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return (
        _text(source_refs.get("work_unit_id"))
        or _text(owner_route.get("work_unit_id"))
        or _text(basis.get("work_unit_id"))
    )


def _dispatch_work_unit_fingerprint(dispatch: Mapping[str, Any]) -> str | None:
    owner_route = _dispatch_owner_route(dispatch)
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return (
        _text(dispatch.get("work_unit_fingerprint"))
        or _text(dispatch.get("action_fingerprint"))
        or _text(dispatch.get("source_fingerprint"))
        or _text(owner_route.get("work_unit_fingerprint"))
        or _text(owner_route.get("source_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(source_refs.get("source_fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(basis.get("source_fingerprint"))
    )


def _dispatch_currentness_key(dispatch: Mapping[str, Any], *, time_key: str) -> tuple[str, str, str]:
    owner_route = _dispatch_owner_route(dispatch)
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return (
        time_key,
        _text(owner_route.get("runtime_health_epoch"))
        or _text(source_refs.get("runtime_health_epoch"))
        or _text(basis.get("runtime_health_epoch"))
        or "",
        _text(owner_route.get("work_unit_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or "",
    )


def _dispatch_route_currentness_key(dispatch: Mapping[str, Any], *, mtime_key: str) -> tuple[str, str, str]:
    owner_route = _dispatch_owner_route(dispatch)
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return (
        _text(owner_route.get("runtime_health_epoch"))
        or _text(source_refs.get("runtime_health_epoch"))
        or _text(basis.get("runtime_health_epoch"))
        or "",
        _text(owner_route.get("work_unit_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or "",
        _dispatch_generated_time_key(dispatch) or mtime_key,
    )


def _dispatch_generated_time_key(dispatch: Mapping[str, Any]) -> str | None:
    generated_at = _text(dispatch.get("generated_at"))
    if generated_at is None:
        return None
    normalized = generated_at.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return generated_at
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return f"{int(parsed.timestamp() * 1_000_000_000):020d}"


def _dispatch_mtime_key(path: Path) -> str:
    try:
        return f"{path.stat().st_mtime_ns:020d}"
    except OSError:
        return ""


def _source_refs(
    *,
    dispatch: Mapping[str, Any],
    dispatch_ref: str,
    latest_dispatch_ref: str,
    prompt_contract_ref: str,
    workspace_root: Path,
    redrive_context: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = [
        {
            "role": "default_executor_stage_packet",
            "ref": dispatch_ref,
            "exists": True,
            "body_included": False,
        },
        {
            "role": "default_executor_dispatch_request",
            "ref": dispatch_ref,
            "exists": True,
            "body_included": False,
        },
        {
            "role": "default_executor_latest_dispatch_request",
            "ref": latest_dispatch_ref,
            "exists": True,
            "body_included": False,
        },
        {
            "role": "default_executor_prompt_contract",
            "ref": prompt_contract_ref,
            "exists": True,
            "body_included": False,
        },
        {
            "role": "mas_default_executor_owner_receipt_contract",
            "ref": OWNER_RECEIPT_CONTRACT,
            "exists": True,
            "body_included": False,
        },
        {
            "role": "owner_route_currentness_basis",
            "ref": f"{dispatch_ref}#owner_route",
            "exists": True,
            "body_included": False,
        },
    ]
    refs.extend(
        _project_dispatch_refs(
            refs=_mapping(dispatch.get("refs")),
            workspace_root=workspace_root,
        )
    )
    refs.extend(
        _project_owner_route_refs(
            owner_route=_mapping(dispatch.get("owner_route"))
            or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route")),
            workspace_root=workspace_root,
        )
    )
    redrive = _mapping(redrive_context)
    if redrive:
        if receipt_ref := _text(redrive.get("receipt_ref")):
            refs.append(
                {
                    "role": "nonconsumable_default_executor_closeout",
                    "ref": receipt_ref,
                    "exists": True,
                    "body_included": False,
                }
            )
        if execution_id := _text(redrive.get("execution_id")):
            refs.append(
                {
                    "role": "nonconsumable_default_executor_execution_id",
                    "ref": execution_id,
                    "exists": True,
                    "body_included": False,
                }
            )
    return refs


def _project_dispatch_refs(*, refs: Mapping[str, Any], workspace_root: Path) -> list[dict[str, Any]]:
    role_by_key = {
        "dispatch_path": "default_executor_dispatch_path",
        "immutable_dispatch_path": "default_executor_immutable_dispatch_path",
        "stage_packet_path": "default_executor_stage_packet_path",
        "source_eval_path": "source_publication_eval_currentness",
        "source_summary_path": "quality_repair_source_summary",
        "repair_execution_evidence_path": "repair_execution_evidence_currentness",
        "scan_latest": "opl_current_control_state_scan_currentness",
    }
    projected: list[dict[str, Any]] = []
    for key, role in role_by_key.items():
        ref = _ref_text(refs.get(key), workspace_root=workspace_root)
        if ref is None:
            continue
        projected.append(
            {
                "role": role,
                "ref": ref,
                "exists": True,
                "body_included": False,
            }
        )
    return projected


def _project_owner_route_refs(
    *,
    owner_route: Mapping[str, Any],
    workspace_root: Path,
) -> list[dict[str, Any]]:
    route_role_by_key = {
        "truth_epoch": "owner_route_truth_epoch",
        "runtime_health_epoch": "owner_route_runtime_health_epoch",
        "route_epoch": "owner_route_route_epoch",
        "work_unit_fingerprint": "owner_route_work_unit_fingerprint",
        "source_fingerprint": "owner_route_source_fingerprint",
    }
    source_refs = _mapping(owner_route.get("source_refs"))
    source_role_by_key = {
        "source_eval_id": "owner_route_source_eval_id",
        "publication_eval_path": "owner_route_publication_eval_path",
        "runtime_health_epoch": "owner_route_runtime_health_epoch",
        "study_truth_epoch": "owner_route_study_truth_epoch",
        "work_unit_id": "owner_route_work_unit_id",
        "blocked_reason": "owner_route_blocked_reason",
    }
    projected: list[dict[str, Any]] = []
    for key, role in route_role_by_key.items():
        ref = _ref_text(owner_route.get(key), workspace_root=workspace_root)
        if ref is None:
            continue
        projected.append(
            {
                "role": role,
                "ref": ref,
                "exists": True,
                "body_included": False,
            }
        )
    for key, role in source_role_by_key.items():
        ref = _ref_text(source_refs.get(key), workspace_root=workspace_root)
        if ref is None:
            continue
        projected.append(
            {
                "role": role,
                "ref": ref,
                "exists": True,
                "body_included": False,
            }
        )
    return projected


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def _persist_dispatch_identity(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch_path: Path,
    stage_packet_path: Path,
    dispatch: Mapping[str, Any],
) -> None:
    if not _mapping(dispatch.get("readiness_surface_identity")):
        return
    targets = {dispatch_path, stage_packet_path}
    for target in targets:
        if not target.is_file():
            continue
        target.write_text(
            json.dumps(dict(dispatch), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    _persist_readiness_request_packet(profile=profile, study_id=study_id, dispatch=dispatch)


def _persist_dispatch_packet_identity(
    *,
    dispatch_path: Path,
    dispatch: Mapping[str, Any],
) -> dict[str, Any]:
    packet = default_executor_dispatch_packets.dispatch_with_immutable_packet_ref(
        dispatch=dispatch,
        dispatch_path=dispatch_path,
    )
    stage_packet_path = default_executor_dispatch_packets.dispatch_stage_packet_path(
        packet,
        fallback_dispatch_path=dispatch_path,
    )
    for target in {dispatch_path, stage_packet_path}:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(dict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return packet


def _persist_readiness_request_packet(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> None:
    if _text(dispatch.get("action_type")) != READINESS_ACTION_TYPE:
        return
    packet = _readiness_request_packet_from_dispatch(study_id=study_id, dispatch=dispatch)
    if not packet:
        return
    path = profile.studies_root / study_id / "artifacts" / "supervision" / "requests" / "medical_paper_readiness" / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _readiness_request_packet_from_dispatch(
    *,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    identity = _mapping(dispatch.get("readiness_surface_identity")) or _mapping(
        prompt_contract.get("readiness_surface_identity")
    )
    surface_key = _text(identity.get("surface_key")) or _text(dispatch.get("surface_key")) or _text(
        prompt_contract.get("surface_key")
    )
    if surface_key is None:
        return {}
    request_ref = "artifacts/supervision/requests/medical_paper_readiness/latest.json"
    operator_payload = _mapping(dispatch.get("operator_payload")) or _mapping(
        dispatch.get("medical_paper_readiness_payload")
    )
    if operator_payload and not _payload_matches_surface(payload=operator_payload, surface_key=surface_key):
        operator_payload = {}
    target = dict(
        _mapping(dispatch.get("payload_authoring_target")) or _mapping(prompt_contract.get("payload_authoring_target"))
    )
    if not target:
        target = {
            "surface": "medical_paper_readiness_operator_payload_authoring_target",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": _text(dispatch.get("quest_id")) or _text(prompt_contract.get("quest_id")) or study_id,
            "action_type": READINESS_ACTION_TYPE,
            "operator_payload_contract": {
                "required": ["operator_payload"],
                "payload_owner": "MedAutoScience",
                "payload_must_be_domain_authored": True,
                "empty_payload_is_not_success_evidence": True,
            },
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        }
    if target:
        target["surface_key"] = surface_key
        target["readiness_surface_identity"] = dict(identity)
        contract = dict(_mapping(target.get("operator_payload_contract")))
        if contract:
            contract["surface_key"] = surface_key
            target["operator_payload_contract"] = contract
        payload = _mapping(target.get("operator_payload"))
        if payload and not _payload_matches_surface(payload=payload, surface_key=surface_key):
            target.pop("operator_payload", None)
    return {
        "surface": "supervisor_request_handoff_packet",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")) or _text(prompt_contract.get("quest_id")) or study_id,
        "request_kind": READINESS_ACTION_TYPE,
        "action_type": READINESS_ACTION_TYPE,
        "authority": _text(dispatch.get("authority")) or _text(prompt_contract.get("authority")) or "mas_owner_surface",
        "request_owner": _text(dispatch.get("request_owner")) or _text(prompt_contract.get("request_owner")) or "MedAutoScience",
        "expected_owner": _text(dispatch.get("expected_owner")) or _text(prompt_contract.get("expected_owner")) or "MedAutoScience",
        "next_executable_owner": _text(dispatch.get("next_executable_owner"))
        or _text(prompt_contract.get("next_executable_owner"))
        or "MedAutoScience",
        "required_output_surface": _text(dispatch.get("required_output_surface"))
        or _text(prompt_contract.get("required_output_surface"))
        or READINESS_ACTION_TYPE,
        "owner_route": _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route")) or None,
        "idempotency_key": _text(dispatch.get("idempotency_key")) or _text(prompt_contract.get("idempotency_key")),
        "request_packet_ref": request_ref,
        "readiness_surface_identity": dict(identity),
        "surface_key": surface_key,
        "operator_payload_ref": request_ref,
        "medical_paper_readiness_payload_ref": request_ref,
        "operator_payload_present": bool(operator_payload),
        **({"operator_payload": operator_payload, "medical_paper_readiness_payload": operator_payload} if operator_payload else {}),
        **({"payload_authoring_target": target} if target else {}),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "supervisor_authority_boundary": "request_only",
    }


def _workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _ref_text(value: object, *, workspace_root: Path) -> str | None:
    text = _text(value)
    if text is None:
        return None
    path = Path(text)
    if path.is_absolute():
        return _workspace_relative(path, workspace_root=workspace_root)
    return text


def _source_fingerprint(
    *,
    dispatch: Mapping[str, Any],
    dispatch_path: Path,
    redrive_context: Mapping[str, Any] | None = None,
    readiness_surface_identity: Mapping[str, Any] | None = None,
) -> str:
    digest_payload = {
        "path": str(dispatch_path),
        "idempotency_key": _text(dispatch.get("idempotency_key")),
        "action_type": _text(dispatch.get("action_type")),
        "dispatch_authority": _text(dispatch.get("dispatch_authority")),
        "owner_route_fingerprint": _text(_mapping(dispatch.get("owner_route")).get("work_unit_fingerprint")),
        "file_digest": hashlib.sha256(dispatch_path.read_bytes()).hexdigest(),
    }
    redrive_fingerprint = _source_fingerprint_redrive_context(redrive_context)
    if redrive_fingerprint is not None:
        digest_payload["redrive_context"] = redrive_fingerprint
    readiness_identity = _mapping(readiness_surface_identity)
    if readiness_identity:
        digest_payload["readiness_surface_identity"] = {
            "action_type": _text(readiness_identity.get("action_type")),
            "surface_key": _text(readiness_identity.get("surface_key")),
            "source": _text(readiness_identity.get("source")),
        }
    rendered = json.dumps(digest_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


def _source_fingerprint_redrive_context(redrive_context: Mapping[str, Any] | None) -> dict[str, Any] | None:
    redrive = _mapping(redrive_context)
    if not redrive:
        return None
    return {
        "status": _text(redrive.get("status")),
        "execution_id": _text(redrive.get("execution_id")),
        "action_type": _text(redrive.get("action_type")),
        "reason": _text(redrive.get("reason")),
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _receipt_is_synthetic_nonconsumable_budget(receipt: Mapping[str, Any] | None) -> bool:
    payload = _mapping(receipt)
    if not payload:
        return False
    if _text(payload.get("blocked_reason")) != nonconsumable_redrive_budget.REDRIVE_BUDGET_EXHAUSTED_REASON:
        return False
    blocker = _mapping(payload.get("typed_blocker"))
    return (
        _text(blocker.get("blocker_family")) == nonconsumable_redrive_budget.REDRIVE_BUDGET_EXHAUSTED_REASON
        and _text(payload.get("next_action")) == "honor_typed_blocker_without_redrive"
    )


def _stage_native_owner_route(owner_route: Mapping[str, Any]) -> bool:
    route_epoch = _text(owner_route.get("route_epoch")) or ""
    source_fingerprint = _text(owner_route.get("source_fingerprint")) or ""
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return any(
        str(value).startswith("stage-native-next-action::")
        for value in (
            route_epoch,
            source_fingerprint,
            _text(source_refs.get("study_truth_epoch")) or "",
            _text(source_refs.get("runtime_health_epoch")) or "",
            _text(source_refs.get("work_unit_fingerprint")) or "",
            _text(basis.get("truth_epoch")) or "",
            _text(basis.get("runtime_health_epoch")) or "",
            _text(basis.get("work_unit_fingerprint")) or "",
        )
    )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for text in (_text(entry) for entry in value) if text is not None]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalized_path_text(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    return text.replace("\\", "/")


__all__ = ["TASK_KIND", "default_executor_dispatch_tasks"]
