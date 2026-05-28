from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile

from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)
from med_autoscience.controllers import study_transition_receipt_consumption
from med_autoscience.runtime_control import owner_route_attempt_protocol


TASK_KIND = "domain_owner/default-executor-dispatch"
DISPATCH_RELATIVE_ROOT = Path("artifacts/supervision/consumer/default_executor_dispatches")
REQUIRED_SURFACE = "default_executor_dispatch_request"
REQUIRED_EXECUTOR_KIND = "codex_cli_default"
DEFAULT_NEXT_OWNER = "write"
ALLOWED_NEXT_OWNERS = frozenset({"write", "ai_reviewer", "write/ai_reviewer"})
OWNER_RECEIPT_CONTRACT = "mas-default-executor-owner-receipt.v1"


def default_executor_dispatch_tasks(
    *,
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> list[dict[str, Any]]:
    dispatch_root = profile.studies_root / study_id / DISPATCH_RELATIVE_ROOT
    if not dispatch_root.is_dir():
        return []
    tasks: list[dict[str, Any]] = []
    for candidate in _current_dispatch_candidates(dispatch_root):
        dispatch_path = candidate["path"]
        dispatch = candidate["dispatch"]
        if not isinstance(dispatch_path, Path) or not isinstance(dispatch, Mapping):
            continue
        action_type = _text(dispatch.get("action_type"))
        if action_type is None:
            continue
        if _dispatch_execution_receipt_consumed(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch,
            action_type=action_type,
        ):
            continue
        redrive_context = _dispatch_execution_redrive_context(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch,
            action_type=action_type,
        )
        dispatch_authority = _text(dispatch.get("dispatch_authority")) or "consumer_default_executor_dispatch"
        dispatch_ref = _workspace_relative(dispatch_path, workspace_root=profile.workspace_root)
        owner_route_attempt_envelope = owner_route_attempt_protocol.default_executor_attempt_envelope(
            dispatch=dispatch
        )
        if owner_route_attempt_envelope.get("dispatchable") is not True:
            continue
        protocol_payload_fields = owner_route_attempt_protocol.payload_fields_for_default_executor_dispatch(
            dispatch=dispatch
        )
        prompt_contract_ref = f"{dispatch_ref}#prompt_contract"
        source_refs = _source_refs(
            dispatch=dispatch,
            dispatch_ref=dispatch_ref,
            prompt_contract_ref=prompt_contract_ref,
            workspace_root=profile.workspace_root,
            redrive_context=redrive_context,
        )
        quest_id = _text(dispatch.get("quest_id")) or study_id
        next_owner = _next_executable_owner(dispatch) or DEFAULT_NEXT_OWNER
        executor_kind = _text(dispatch.get("executor_kind")) or REQUIRED_EXECUTOR_KIND
        source_fingerprint = _source_fingerprint(
            dispatch=dispatch,
            dispatch_path=dispatch_path,
            redrive_context=redrive_context,
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
                    "dispatch_authority": dispatch_authority,
                    "executor_kind": executor_kind,
                    "dispatch_ref": dispatch_ref,
                    "authority_boundary": "mas_default_executor_dispatch_request_only",
                    "next_executable_owner": next_owner,
                    **({"redrive_context": redrive_context} if redrive_context else {}),
                },
                "source_refs": source_refs,
                "owner_route_attempt_envelope": owner_route_attempt_envelope,
                "dispatch_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "queue_owner": "one-person-lab",
                "profile_name": profile.name,
                "domain_dispatch_evidence_record_payload": evidence_record_payload,
            }
        )
    return tasks


def _current_dispatch_candidates(dispatch_root: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for dispatch_path in sorted(dispatch_root.glob("*.json")):
        dispatch = _read_json_object(dispatch_path)
        if not _dispatch_ready_for_opl_attempt(dispatch):
            continue
        candidates.append({"path": dispatch_path, "dispatch": dispatch})
    return [
        candidate
        for candidate in candidates
        if not _dispatch_blocked_by_newer_candidate(candidate, candidates)
    ]


def _dispatch_blocked_by_newer_candidate(
    candidate: Mapping[str, Any],
    candidates: list[Mapping[str, Any]],
) -> bool:
    dispatch = _mapping(candidate.get("dispatch"))
    action_type = _text(dispatch.get("action_type"))
    if action_type is None:
        return False
    owner_route = _dispatch_owner_route(dispatch)
    work_unit_id = _owner_route_work_unit_id(owner_route)
    for other_candidate in candidates:
        if other_candidate is candidate:
            continue
        other = _mapping(other_candidate.get("dispatch"))
        other_route = _dispatch_owner_route(other)
        if action_type not in set(_string_list(other_route.get("blocked_actions"))):
            continue
        other_work_unit_id = _owner_route_work_unit_id(other_route)
        if work_unit_id and other_work_unit_id and work_unit_id != other_work_unit_id:
            continue
        if _dispatch_currentness_key(other) <= _dispatch_currentness_key(dispatch):
            continue
        return True
    return False


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


def _dispatch_currentness_key(dispatch: Mapping[str, Any]) -> tuple[str, str, str]:
    owner_route = _dispatch_owner_route(dispatch)
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return (
        _text(dispatch.get("generated_at")) or "",
        _text(owner_route.get("runtime_health_epoch"))
        or _text(source_refs.get("runtime_health_epoch"))
        or _text(basis.get("runtime_health_epoch"))
        or "",
        _text(owner_route.get("work_unit_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or "",
    )


def _source_refs(
    *,
    dispatch: Mapping[str, Any],
    dispatch_ref: str,
    prompt_contract_ref: str,
    workspace_root: Path,
    redrive_context: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = [
        {
            "role": "default_executor_dispatch_request",
            "ref": dispatch_ref,
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


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for text in (_text(entry) for entry in value) if text is not None]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["TASK_KIND", "default_executor_dispatch_tasks"]
