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
