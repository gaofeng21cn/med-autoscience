from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.opl_execution_boundary import (
    first_trusted_opl_execution_authorization,
    typed_blocker as opl_execution_authorization_typed_blocker,
)

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
        "adapter_kind": "opl_authorized_owner_callable_adapter",
        "target_runtime_owner": "one-person-lab",
        "mas_private_attempt_loop_forbidden": True,
        "mas_dispatch_authority": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "provider_attempt_or_lease_required": False,
        "opl_transition_runtime_required": True,
    }


def _authorized(
    *,
    dispatch: Mapping[str, Any],
    owner_route_basis: str | None,
    current_study: Mapping[str, Any],
) -> bool:
    provider_hosted_authorization = _provider_hosted_stage_attempt_authorization(dispatch=dispatch)
    if provider_hosted_authorization is not None:
        return True
    if owner_route_basis == "live_provider_attempt_dispatch":
        live_attempt = _mapping(current_study.get("opl_provider_attempt")) or current_study
        return first_trusted_opl_execution_authorization(live_attempt) is not None
    if first_trusted_opl_execution_authorization(
        dispatch.get("opl_execution_authorization"),
        dispatch.get("opl_provider_attempt"),
        dispatch.get("stage_attempt"),
        _mapping(dispatch.get("prompt_contract")).get("opl_execution_authorization"),
        _mapping(dispatch.get("prompt_contract")).get("opl_provider_attempt"),
        _mapping(dispatch.get("owner_route")).get("opl_execution_authorization"),
        _mapping(dispatch.get("owner_route")).get("opl_provider_attempt"),
    ) is not None:
        return True
    return _closeout_or_readback_binding_present(dispatch)


def _closeout_or_readback_binding_present(dispatch: Mapping[str, Any]) -> bool:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    binding = _mapping(dispatch.get("closeout_binding")) or _mapping(prompt_contract.get("closeout_binding"))
    if not binding:
        return False
    if _text(binding.get("stage_run_id")) is None and _text(binding.get("stage_run_ref")) is None:
        return False
    if _text(binding.get("stage_manifest_ref")) is None:
        return False
    if _text(binding.get("current_pointer_ref")) is None:
        return False
    if not _text_items(binding.get("closeout_refs")):
        return False
    if _text(binding.get("source_fingerprint")) is None:
        return False
    return _text(binding.get("work_unit_fingerprint")) is not None


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


def provider_hosted_exact_stage_run_current_execution_authority(
    dispatch: Mapping[str, Any],
) -> bool:
    return provider_hosted_stage_attempt_authorizes_dispatch(dispatch)


def provider_hosted_canonical_stage_packet_dispatch(
    *,
    dispatch: Mapping[str, Any],
    workspace_root: Path,
    study_root: Path,
) -> dict[str, Any] | None:
    stage_packet_ref = _env_text("OPL_STAGE_PACKET_REF")
    if stage_packet_ref is None:
        return None
    for path in _candidate_stage_packet_paths(
        stage_packet_ref=stage_packet_ref,
        dispatch=dispatch,
        workspace_root=workspace_root,
        study_root=study_root,
    ):
        packet = _read_json_object(path)
        if packet is None:
            continue
        if not _canonical_stage_packet_matches(
            carrier=dispatch,
            packet=packet,
            stage_packet_ref=stage_packet_ref,
        ):
            continue
        packet_refs = _mapping(packet.get("refs"))
        refs = {
            **packet_refs,
            "stage_packet_path": str(path),
        }
        refs.setdefault("immutable_dispatch_path", str(path))
        if _text(refs.get("dispatch_path")) is None:
            refs["dispatch_path"] = str(path)
        return with_provider_hosted_opl_authorization({**dict(packet), "refs": refs})
    return None


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
    if not _env_work_unit_authorizes_dispatch(
        env_work_unit_id=env_work_unit_id,
        dispatch_work_unit_id=dispatch_work_unit_id,
        stage_packet_ref=stage_packet_ref,
        dispatch=dispatch,
    ):
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
    return any(_refs_match(stage_packet_ref, candidate) for candidate in candidates)


def _env_work_unit_authorizes_dispatch(
    *,
    env_work_unit_id: str | None,
    dispatch_work_unit_id: str | None,
    stage_packet_ref: str,
    dispatch: Mapping[str, Any],
) -> bool:
    if env_work_unit_id is None or dispatch_work_unit_id is None:
        return True
    if env_work_unit_id == dispatch_work_unit_id:
        return True
    stage_packet_scope_ref = _stage_packet_scope_ref(env_work_unit_id)
    if stage_packet_scope_ref is None:
        return False
    if not _refs_match(stage_packet_ref, stage_packet_scope_ref):
        return False
    return _stage_packet_ref_matches_dispatch(
        stage_packet_ref=stage_packet_scope_ref,
        dispatch=dispatch,
    )


def _stage_packet_scope_ref(value: str) -> str | None:
    prefix = "stage-packet:"
    if not value.startswith(prefix):
        return None
    return _text(value.removeprefix(prefix))


def _refs_match(reference: object, candidate: object) -> bool:
    normalized_reference = _normalize_ref(reference)
    normalized_candidate = _normalize_ref(candidate)
    if normalized_reference is None or normalized_candidate is None:
        return False
    return (
        normalized_candidate == normalized_reference
        or normalized_candidate.endswith(f"/{normalized_reference}")
        or normalized_reference.endswith(f"/{normalized_candidate}")
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


def _dispatch_work_unit_fingerprint(dispatch: Mapping[str, Any]) -> str | None:
    owner_route = _mapping(dispatch.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(owner_route.get("currentness_contract")).get("basis")
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action"))
    return (
        _text(dispatch.get("work_unit_fingerprint"))
        or _text(source_action.get("work_unit_fingerprint"))
        or _text(owner_route.get("work_unit_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(currentness_basis.get("work_unit_fingerprint"))
        or _text(prompt_contract.get("work_unit_fingerprint"))
    )


def _candidate_stage_packet_paths(
    *,
    stage_packet_ref: str,
    dispatch: Mapping[str, Any],
    workspace_root: Path,
    study_root: Path,
) -> list[Path]:
    refs = _mapping(dispatch.get("refs"))
    candidates: list[Path] = []
    seen: set[str] = set()
    for item in (
        stage_packet_ref,
        refs.get("stage_packet_path"),
        refs.get("immutable_dispatch_path"),
        refs.get("dispatch_path"),
        dispatch.get("stage_packet_ref"),
    ):
        for path in _resolved_ref_paths(
            item,
            workspace_root=workspace_root,
            study_root=study_root,
        ):
            key = path.as_posix()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(path)
    return candidates


def _resolved_ref_paths(value: object, *, workspace_root: Path, study_root: Path) -> list[Path]:
    text = _normalize_ref(value)
    if text is None or "://" in text:
        return []
    raw = Path(text).expanduser()
    if raw.is_absolute():
        return [raw.resolve()]
    candidates: list[Path] = []
    if text.startswith(("studies/", "runtime/", "ops/")):
        candidates.append((workspace_root / raw).resolve())
    candidates.append((study_root / raw).resolve())
    candidates.append((workspace_root / raw).resolve())
    return candidates


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _canonical_stage_packet_matches(
    *,
    carrier: Mapping[str, Any],
    packet: Mapping[str, Any],
    stage_packet_ref: str,
) -> bool:
    if _text(packet.get("surface")) != "default_executor_dispatch_request":
        return False
    if _text(packet.get("dispatch_status")) != "ready":
        return False
    if _text(packet.get("executor_kind")) != "codex_cli_default":
        return False
    if not _stage_packet_ref_matches_dispatch(stage_packet_ref=stage_packet_ref, dispatch=packet):
        return False
    if _provider_hosted_stage_attempt_authorization(dispatch=packet) is None:
        return False
    for env_key, packet_value in (
        ("OPL_STUDY_ID", packet.get("study_id")),
        ("OPL_ACTION_TYPE", packet.get("action_type")),
    ):
        expected = _env_text(env_key)
        actual = _text(packet_value)
        if expected is not None and actual != expected:
            return False
    packet_work_unit_id = _dispatch_work_unit_id(packet)
    expected_work_unit_id = _env_text("OPL_WORK_UNIT_ID")
    if not _env_work_unit_authorizes_dispatch(
        env_work_unit_id=expected_work_unit_id,
        dispatch_work_unit_id=packet_work_unit_id,
        stage_packet_ref=stage_packet_ref,
        dispatch=packet,
    ):
        return False
    carrier_work_unit_id = _dispatch_work_unit_id(carrier)
    if (
        carrier_work_unit_id is not None
        and packet_work_unit_id is not None
        and carrier_work_unit_id != packet_work_unit_id
    ):
        return False
    carrier_fingerprint = _dispatch_work_unit_fingerprint(carrier)
    packet_fingerprint = _dispatch_work_unit_fingerprint(packet)
    if (
        carrier_fingerprint is not None
        and packet_fingerprint is not None
        and carrier_fingerprint != packet_fingerprint
    ):
        return False
    carrier_study_id = _text(carrier.get("study_id"))
    if carrier_study_id is not None and _text(packet.get("study_id")) != carrier_study_id:
        return False
    carrier_action_type = _text(carrier.get("action_type"))
    if carrier_action_type is not None and _text(packet.get("action_type")) != carrier_action_type:
        return False
    return True


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


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]
