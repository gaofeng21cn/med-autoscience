from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.opl_execution_boundary import (
    first_trusted_opl_execution_authorization,
    typed_blocker as opl_execution_authorization_typed_blocker,
)
from . import current_writer_handoff

_CLEAN_ROOM_PUBLICATION_SURFACE_ACTION = "run_medical_publication_surface_from_clean_room"
_CLEAN_ROOM_DESCRIPTOR_SURFACE = "artifacts/supervision/paper_clean_room_rebuild/latest.json"
_QUALITY_REPAIR_ACTION = "run_quality_repair_batch"
_PUBLICATION_SURFACE_DESCRIPTOR = "artifacts/reports/medical_publication_surface/latest.json"
_PUBLICATION_HANDOFF_STAGE_ID = "08-publication_package_handoff"
_ACCEPTED_OWNER_GATE_DECISION_AUTHORITY = "paper_recovery_state.accepted_owner_gate_decision"


def block_if_missing_authorization(
    *,
    dispatch: Mapping[str, Any],
    owner_route_basis: str | None,
    current_study: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _authorized(
        dispatch=dispatch,
        owner_route_basis=owner_route_basis,
        current_study=current_study,
    ):
        return None
    if _text(dispatch.get("action_type")) == "complete_medical_paper_readiness_surface":
        return {
            "execution_status": "handoff_ready",
            "blocked_reason": None,
            "owner_callable_surface": "opl_default_executor.stage_attempt",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "authority_boundary": {
                "opl": "provider_attempt_admission_and_execution_authorization",
                "domain": "truth_quality_artifact_gate_owner",
                "can_write_domain_truth": False,
                "can_authorize_quality_verdict": False,
                "provider_completion_is_domain_ready": False,
            },
        }
    return {
        "execution_status": "blocked",
        "blocked_reason": "opl_execution_authorization_required",
        "typed_blocker": opl_execution_authorization_typed_blocker(),
        "owner_callable_surface": None,
        "mas_private_attempt_loop_forbidden": True,
        "provider_attempt_or_lease_required": True,
    }


def _authorized(
    *,
    dispatch: Mapping[str, Any],
    owner_route_basis: str | None,
    current_study: Mapping[str, Any],
) -> bool:
    if _stage_native_clean_room_publication_surface_authorized(
        dispatch=dispatch,
        owner_route_basis=owner_route_basis,
    ):
        return True
    if _stage_native_quality_repair_owner_action_authorized(
        dispatch=dispatch,
        owner_route_basis=owner_route_basis,
    ):
        return True
    if _accepted_owner_gate_materialization_authorized(
        dispatch=dispatch,
        owner_route_basis=owner_route_basis,
    ):
        return True
    if owner_route_basis in {"bridged_writer_handoff", "current_writer_handoff"} and (
        current_writer_handoff.self_authorized_quality_repair_writer_handoff(
            study_id=_text(dispatch.get("study_id")) or "",
            action_type=_text(dispatch.get("action_type")) or "",
            dispatch=dispatch,
        )
    ):
        return True
    provider_hosted_authorization = _provider_hosted_stage_attempt_authorization(dispatch=dispatch)
    if provider_hosted_authorization is not None:
        return True
    if owner_route_basis == "live_provider_attempt_dispatch":
        live_attempt = _mapping(current_study.get("opl_provider_attempt")) or current_study
        return first_trusted_opl_execution_authorization(live_attempt) is not None
    return first_trusted_opl_execution_authorization(
        dispatch.get("opl_execution_authorization"),
        dispatch.get("opl_provider_attempt"),
        dispatch.get("stage_attempt"),
        _mapping(dispatch.get("prompt_contract")).get("opl_execution_authorization"),
        _mapping(dispatch.get("prompt_contract")).get("opl_provider_attempt"),
        _mapping(dispatch.get("owner_route")).get("opl_execution_authorization"),
        _mapping(dispatch.get("owner_route")).get("opl_provider_attempt"),
    ) is not None


def _stage_native_clean_room_publication_surface_authorized(
    *,
    dispatch: Mapping[str, Any],
    owner_route_basis: str | None,
) -> bool:
    if owner_route_basis != "stage_native_workspace_next_action":
        return False
    if _text(dispatch.get("action_type")) != _CLEAN_ROOM_PUBLICATION_SURFACE_ACTION:
        return False
    source_action = _mapping(dispatch.get("source_action"))
    owner_route = _mapping(dispatch.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    source_surface = (
        _text(source_action.get("source_surface"))
        or _text(source_refs.get("source_surface"))
        or _text(_mapping(dispatch.get("prompt_contract")).get("source_surface"))
    )
    return source_surface == _CLEAN_ROOM_DESCRIPTOR_SURFACE


def _stage_native_quality_repair_owner_action_authorized(
    *,
    dispatch: Mapping[str, Any],
    owner_route_basis: str | None,
) -> bool:
    if owner_route_basis != "stage_native_workspace_next_action":
        return False
    if _text(dispatch.get("action_type")) != _QUALITY_REPAIR_ACTION:
        return False
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    if (_text(dispatch.get("next_executable_owner")) or _text(owner_route.get("next_owner"))) != "write":
        return False
    source_action = _mapping(dispatch.get("source_action"))
    if _text(source_action.get("authority")) != "stage_native_workspace_next_action":
        return False
    source_refs = _mapping(owner_route.get("source_refs"))
    source_surface = (
        _text(source_action.get("source_surface"))
        or _text(source_refs.get("source_surface"))
        or _text(_mapping(dispatch.get("prompt_contract")).get("source_surface"))
    )
    if source_surface != _PUBLICATION_SURFACE_DESCRIPTOR:
        return False
    current_stage_id = _text(source_action.get("current_stage_id")) or _text(
        source_refs.get("current_stage_id")
    )
    if current_stage_id != _PUBLICATION_HANDOFF_STAGE_ID:
        return False
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(owner_route.get("currentness_contract")).get("basis")
    )
    binding = _mapping(source_refs.get("current_work_unit_binding"))
    return (
        _work_unit_id(currentness_basis.get("work_unit_id")) == _QUALITY_REPAIR_ACTION
        and _text(binding.get("source")) == "canonical_current_work_unit"
        and _text(binding.get("work_unit_id")) == _QUALITY_REPAIR_ACTION
        and _text(binding.get("work_unit_fingerprint")) is not None
    )


def _accepted_owner_gate_materialization_authorized(
    *,
    dispatch: Mapping[str, Any],
    owner_route_basis: str | None,
) -> bool:
    if owner_route_basis != "accepted_owner_gate_decision":
        return False
    if _text(dispatch.get("action_type")) != _QUALITY_REPAIR_ACTION:
        return False
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    if (_text(dispatch.get("next_executable_owner")) or _text(owner_route.get("next_owner"))) != "write":
        return False
    source_action = _mapping(dispatch.get("source_action"))
    source_refs = _mapping(owner_route.get("source_refs"))
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    if _ACCEPTED_OWNER_GATE_DECISION_AUTHORITY not in {
        _text(source_action.get("authority")),
        _text(source_action.get("source_surface")),
        _text(source_refs.get("source_surface")),
        _text(prompt_contract.get("source_surface")),
    }:
        return False
    stall = _mapping(dispatch.get("paper_progress_stall")) or _mapping(
        prompt_contract.get("paper_progress_stall")
    )
    if _text(stall.get("kind")) != "owner_gate_route_back":
        return False
    if stall.get("provider_admission_allowed") is not False:
        return False
    route_back_ref = _text(stall.get("route_back_evidence_ref"))
    if route_back_ref is None:
        return False
    if route_back_ref not in {
        _text(source_action.get("source_ref")),
        _text(source_refs.get("source_ref")),
        _text(prompt_contract.get("source_ref")),
    }:
        return False
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(owner_route.get("currentness_contract")).get("basis")
    )
    work_unit_id = (
        _work_unit_id(source_action.get("work_unit_id"))
        or _work_unit_id(source_refs.get("work_unit_id"))
        or _work_unit_id(currentness_basis.get("work_unit_id"))
    )
    fingerprint = (
        _text(source_action.get("work_unit_fingerprint"))
        or _text(dispatch.get("work_unit_fingerprint"))
        or _text(dispatch.get("action_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(currentness_basis.get("work_unit_fingerprint"))
    )
    return work_unit_id is not None and fingerprint is not None


def with_provider_hosted_opl_authorization(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(dispatch)
    authorization = _provider_hosted_stage_attempt_authorization(dispatch=result)
    if authorization is None:
        return result
    result["opl_execution_authorization"] = dict(authorization)
    prompt_contract = _mapping(result.get("prompt_contract"))
    if prompt_contract:
        result["prompt_contract"] = {
            **prompt_contract,
            "opl_execution_authorization": dict(authorization),
        }
    return result


def provider_hosted_stage_attempt_authorizes_dispatch(dispatch: Mapping[str, Any]) -> bool:
    return _provider_hosted_stage_attempt_authorization(dispatch=dispatch) is not None


def _provider_hosted_stage_attempt_authorization(*, dispatch: Mapping[str, Any]) -> dict[str, Any] | None:
    stage_attempt_id = _env_text("OPL_STAGE_ATTEMPT_ID")
    stage_packet_ref = _env_text("OPL_STAGE_PACKET_REF")
    stage_id = _env_text("OPL_STAGE_ID")
    if stage_attempt_id is None or stage_packet_ref is None:
        return None
    if stage_id is not None and stage_id != "domain_owner/default-executor-dispatch":
        return None
    if not _stage_packet_ref_matches_dispatch(stage_packet_ref=stage_packet_ref, dispatch=dispatch):
        return None
    env_study_id = _env_text("OPL_STUDY_ID")
    dispatch_study_id = _text(dispatch.get("study_id"))
    if env_study_id is not None and dispatch_study_id is not None and env_study_id != dispatch_study_id:
        return None
    env_action_type = _env_text("OPL_ACTION_TYPE")
    dispatch_action_type = _text(dispatch.get("action_type"))
    if env_action_type is not None and dispatch_action_type is not None and env_action_type != dispatch_action_type:
        return None
    env_work_unit_id = _env_text("OPL_WORK_UNIT_ID")
    dispatch_work_unit_id = _dispatch_work_unit_id(dispatch)
    if env_work_unit_id is not None and dispatch_work_unit_id is not None and env_work_unit_id != dispatch_work_unit_id:
        return None
    return first_trusted_opl_execution_authorization(
        {
            "owner": "one-person-lab",
            "executor_kind": "codex_cli",
            "provider_attempt_ref": _env_text("OPL_PROVIDER_ATTEMPT_REF"),
            "stage_attempt_id": stage_attempt_id,
            "attempt_lease_ref": _env_text("OPL_ATTEMPT_LEASE_REF"),
            "attempt_lease_status": _env_text("OPL_ATTEMPT_LEASE_STATUS"),
            "execution_authorization_decision_ref": _env_text("OPL_EXECUTION_AUTHORIZATION_DECISION_REF"),
            "source_fingerprint": _env_text("OPL_SOURCE_FINGERPRINT"),
            "idempotency_key": _env_text("OPL_IDEMPOTENCY_KEY"),
            "stage_run_id": _env_text("OPL_STAGE_RUN_ID"),
            "stage_manifest_ref": _env_text("OPL_STAGE_MANIFEST_REF"),
            "current_pointer_ref": _env_text("OPL_CURRENT_POINTER_REF"),
            "stage_packet_ref": stage_packet_ref,
            "workflow_id": _env_text("OPL_WORKFLOW_ID"),
            "task_id": _env_text("OPL_TASK_ID"),
            "runtime_owner": "one-person-lab",
        }
    )


def _stage_packet_ref_matches_dispatch(*, stage_packet_ref: str, dispatch: Mapping[str, Any]) -> bool:
    candidates = [
        _text(dispatch.get("stage_packet_ref")),
        _text(_mapping(dispatch.get("refs")).get("stage_packet_path")),
        _text(_mapping(dispatch.get("refs")).get("immutable_dispatch_path")),
        _text(_mapping(dispatch.get("refs")).get("dispatch_path")),
    ]
    normalized_ref = _normalize_ref(stage_packet_ref)
    return any(
        normalized_candidate == normalized_ref or normalized_candidate.endswith(f"/{normalized_ref}")
        for candidate in candidates
        if (normalized_candidate := _normalize_ref(candidate)) is not None
    )


def _dispatch_work_unit_id(dispatch: Mapping[str, Any]) -> str | None:
    owner_route = _mapping(dispatch.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(owner_route.get("currentness_contract")).get("basis")
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action"))
    return (
        _work_unit_id(source_refs.get("work_unit_id"))
        or _work_unit_id(currentness_basis.get("work_unit_id"))
        or _work_unit_id(prompt_contract.get("next_work_unit"))
        or _work_unit_id(dispatch.get("next_work_unit"))
        or _work_unit_id(source_action.get("next_work_unit"))
    )


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _normalize_ref(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    return Path(text).as_posix()


def _env_text(key: str) -> str | None:
    return _text(os.environ.get(key))


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None
