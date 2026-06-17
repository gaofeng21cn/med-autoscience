from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_action_request_materializer
from med_autoscience.controllers.domain_action_request_materializer_parts import currentness_identity
from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_boundaries import (
    domain_progress_transition_request_transport_fields,
)
from med_autoscience.controllers.owner_callable_adapter_projection import owner_callable_adapters
from med_autoscience.controllers.paper_progress_policy_adapter import build_transition_request
from med_autoscience.profiles import WorkspaceProfile

from .default_executor_dispatch_tasks import TASK_KIND as DEFAULT_EXECUTOR_DISPATCH_TASK_KIND


def paper_recovery_default_executor_dispatch_tasks(
    *,
    current_progress: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> list[dict[str, Any]]:
    if not _paper_recovery_requests_default_executor_dispatch(current_progress):
        return []
    preview = domain_action_request_materializer.current_owner_callable_adapters(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=False,
        dispatch_ready_for_execution=True,
    )
    tasks: list[dict[str, Any]] = []
    for dispatch in owner_callable_adapters(preview):
        if not isinstance(dispatch, Mapping):
            continue
        if _text(dispatch.get("study_id")) != study_id:
            continue
        if _text(dispatch.get("dispatch_status")) != "ready":
            continue
        task = _materialized_default_executor_dispatch_task(
            dispatch=dispatch,
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
        )
        if task is not None:
            tasks.append(task)
    if tasks:
        return tasks
    dispatch = _successor_owner_action_dispatch(
        current_progress=current_progress,
        profile=profile,
        study_id=study_id,
    )
    if dispatch is None:
        return []
    task = _materialized_default_executor_dispatch_task(
        dispatch=dispatch,
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
    )
    if task is not None:
        tasks.append(task)
    return tasks


def _paper_recovery_requests_default_executor_dispatch(current_progress: Mapping[str, Any]) -> bool:
    recovery = _mapping(current_progress.get("paper_recovery_state"))
    if _text(recovery.get("phase")) != "owner_action_ready":
        return False
    supervisor_decision = _mapping(recovery.get("supervisor_decision"))
    if _text(supervisor_decision.get("decision")) != "materialize_recovery_action":
        return False
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    return _text(next_safe_action.get("kind")) in {
        "run_mas_owner_callable",
        "materialize_successor_owner_action",
        "materialize_mas_transition_request_or_owner_callable",
    }


def _materialized_default_executor_dispatch_task(
    *,
    dispatch: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> dict[str, Any] | None:
    action_type = _text(dispatch.get("action_type"))
    if action_type is None:
        return None
    owner_route = _mapping(dispatch.get("owner_route"))
    source_refs = _materialized_dispatch_source_refs(dispatch=dispatch, profile=profile)
    source_fingerprint = (
        _text(dispatch.get("source_fingerprint"))
        or _text(dispatch.get("action_fingerprint"))
        or _text(dispatch.get("work_unit_fingerprint"))
        or _fingerprint(
            {
                "profile": profile.name,
                "study_id": study_id,
                "action_type": action_type,
                "owner_route": dict(owner_route),
            }
        )
    )
    reason = "paper_autonomy_supervisor_materialized_default_executor_dispatch"
    evidence_record_payload = build_domain_dispatch_evidence_record_payload(
        task_kind=DEFAULT_EXECUTOR_DISPATCH_TASK_KIND,
        study_id=study_id,
        reason=reason,
        evidence_refs=source_refs,
        source_fingerprint=source_fingerprint,
        profile_name=profile.name,
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    owner_route_source_refs = _mapping(owner_route.get("source_refs"))
    owner_route_currentness_basis = _mapping(
        owner_route_source_refs.get("owner_route_currentness_basis")
    )
    work_unit_id = (
        _text(dispatch.get("work_unit_id"))
        or _text(prompt_contract.get("work_unit_id"))
        or _text(owner_route_source_refs.get("work_unit_id"))
    )
    work_unit_fingerprint = (
        _text(dispatch.get("work_unit_fingerprint"))
        or _text(dispatch.get("action_fingerprint"))
        or _text(prompt_contract.get("work_unit_fingerprint"))
        or _text(owner_route.get("work_unit_fingerprint"))
        or _text(owner_route_source_refs.get("work_unit_fingerprint"))
    )
    next_owner = (
        _text(dispatch.get("next_executable_owner"))
        or _text(owner_route.get("next_owner"))
        or "write"
    )
    dispatch_ref = _text(_mapping(dispatch.get("refs")).get("dispatch_path"))
    source_generation = work_unit_fingerprint or source_fingerprint
    transition_request = build_transition_request(
        study_id=study_id,
        quest_id=_text(dispatch.get("quest_id")) or study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        source_generation=source_generation,
        expected_version=source_generation,
        dispatch_ref=dispatch_ref,
        dispatch_authority=_text(dispatch.get("dispatch_authority")),
        next_owner=next_owner,
        currentness_basis=owner_route_currentness_basis,
        idempotency_context={
            "kind": "paper-recovery-transition-request",
            "source_fingerprint": source_fingerprint,
            "dispatch_ref": dispatch_ref,
        },
    )
    transition_authority_fields = domain_progress_transition_request_transport_fields()
    payload = {
        "profile": str(profile_ref),
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")) or study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_fingerprint": source_fingerprint,
        "dispatch_ref": dispatch_ref,
        "authority_boundary": "mas_default_executor_dispatch_request_only",
        "next_executable_owner": next_owner,
        **transition_authority_fields,
        "opl_domain_progress_transition_request": transition_request,
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "owner_route_currentness_basis": owner_route_currentness_basis or None,
        "paper_autonomy_supervisor_decision": _mapping(
            _mapping(dispatch.get("source_action")).get("supervisor_decision")
        )
        or None,
        "paper_recovery_source_action": _mapping(dispatch.get("source_action")) or None,
        "default_executor_dispatch_request": dict(dispatch),
    }
    return {
        "domain_id": "medautoscience",
        "task_kind": DEFAULT_EXECUTOR_DISPATCH_TASK_KIND,
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")) or study_id,
        "action_type": action_type,
        "domain_owner": next_owner,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "priority": 70,
        "source": "mas-domain-handler-export",
        "requires_approval": False,
        "dedupe_key": (
            f"mas:{profile.name}:{study_id}:paper-recovery-default-executor:"
            f"{action_type}:{source_fingerprint}"
        ),
        "source_fingerprint": source_fingerprint,
        "reason": reason,
        "payload": {key: value for key, value in payload.items() if value not in (None, "", [], {})},
        "source_refs": source_refs,
        "owner_route_attempt_envelope": _mapping(dispatch.get("owner_route_attempt_envelope")) or None,
        "dispatch_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "profile_name": profile.name,
        **transition_authority_fields,
        "opl_domain_progress_transition_request": transition_request,
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "domain_dispatch_evidence_record_payload": evidence_record_payload,
    }


def _successor_owner_action_dispatch(
    *,
    current_progress: Mapping[str, Any],
    profile: WorkspaceProfile,
    study_id: str,
) -> dict[str, Any] | None:
    recovery = _mapping(current_progress.get("paper_recovery_state"))
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if _text(next_safe_action.get("kind")) != "materialize_successor_owner_action":
        return None
    successor = _mapping(next_safe_action.get("successor_owner_action"))
    action_type = _text(successor.get("action_type"))
    if action_type is None:
        return None
    current_work_unit = _mapping(current_progress.get("current_work_unit"))
    current_authority = _mapping(recovery.get("current_authority"))
    obligation = _mapping(current_authority.get("obligation"))
    supervisor_decision = _mapping(recovery.get("supervisor_decision"))
    work_unit_id = (
        _text(successor.get("work_unit_id"))
        or _text(next_safe_action.get("work_unit_id"))
        or _text(current_work_unit.get("work_unit_id"))
    )
    work_unit_fingerprint = (
        _text(successor.get("work_unit_fingerprint"))
        or _text(next_safe_action.get("work_unit_fingerprint"))
        or _text(current_work_unit.get("work_unit_fingerprint"))
        or _text(current_work_unit.get("action_fingerprint"))
    )
    next_owner = (
        _text(successor.get("owner"))
        or _text(next_safe_action.get("owner"))
        or _text(supervisor_decision.get("next_owner"))
        or "write"
    )
    source_ref = (
        _text(successor.get("source_ref"))
        or _text(next_safe_action.get("source_ref"))
        or "paper_recovery_state.next_safe_action.successor_owner_action"
    )
    source_fingerprint = (
        work_unit_fingerprint
        or _fingerprint(
            {
                "profile": profile.name,
                "study_id": study_id,
                "action_type": action_type,
                "successor_owner_action": successor,
            }
        )
    )
    basis = currentness_identity.currentness_basis(
        {
            "source_eval_id": successor.get("source_eval_id")
            or next_safe_action.get("source_eval_id")
            or recovery.get("source_eval_id"),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "truth_epoch": successor.get("truth_epoch") or next_safe_action.get("truth_epoch"),
            "runtime_health_epoch": successor.get("runtime_health_epoch")
            or next_safe_action.get("runtime_health_epoch"),
        },
        successor.get("owner_route_currentness_basis"),
        next_safe_action.get("owner_route_currentness_basis"),
    )
    source_refs = {
        "source_ref": source_ref,
        "supervisor_decision_ref": _text(supervisor_decision.get("decision_id")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "owner_route_currentness_basis": basis or None,
    }
    owner_route = {
        "next_owner": next_owner,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_refs": {key: value for key, value in source_refs.items() if value not in (None, "", [], {})},
        "currentness_contract": {"basis": basis} if basis else None,
    }
    source_action = {
        "authority": "paper_recovery_state",
        "reason": _text(obligation.get("blocker_type")) or _text(current_work_unit.get("status")),
        "supervisor_decision": supervisor_decision or None,
        "next_safe_action": next_safe_action,
        "successor_owner_action": successor,
    }
    return {
        "study_id": study_id,
        "quest_id": _text(current_progress.get("quest_id")) or study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "source_fingerprint": source_fingerprint,
        "dispatch_status": "ready",
        "dispatch_authority": "paper_autonomy_supervisor_materialized_default_executor_dispatch",
        "next_executable_owner": next_owner,
        "refs": {"dispatch_path": source_ref},
        "prompt_contract": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "owner_route_currentness_basis": basis or None,
        },
        "owner_route": {key: value for key, value in owner_route.items() if value not in (None, "", [], {})},
        "source_action": {key: value for key, value in source_action.items() if value not in (None, "", [], {})},
    }


def _materialized_dispatch_source_refs(
    *,
    dispatch: Mapping[str, Any],
    profile: WorkspaceProfile,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    dispatch_ref = _text(_mapping(dispatch.get("refs")).get("dispatch_path"))
    if dispatch_ref is not None:
        dispatch_path = Path(dispatch_ref).expanduser()
        refs.append(
            {
                "role": "default_executor_dispatch_request",
                "ref": dispatch_ref,
                "exists": dispatch_path.exists(),
            }
        )
    source_action = _mapping(dispatch.get("source_action"))
    supervisor_decision = _mapping(source_action.get("supervisor_decision"))
    if supervisor_decision:
        refs.append(
            {
                "role": "paper_autonomy_supervisor_decision",
                "ref": _text(source_action.get("supervisor_decision_ref"))
                or _text(supervisor_decision.get("decision_id"))
                or "default_executor_dispatch_request.source_action.supervisor_decision",
                "exists": True,
                "decision": _text(supervisor_decision.get("decision")),
            }
        )
    owner_route = _mapping(dispatch.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    if source_refs:
        refs.append(
            {
                "role": "owner_route_currentness_basis",
                "ref": _text(source_refs.get("supervisor_decision_ref"))
                or _text(source_refs.get("source_ref"))
                or "default_executor_dispatch_request.owner_route.source_refs",
                "exists": True,
                "work_unit_id": _text(source_refs.get("work_unit_id")),
                "work_unit_fingerprint": _text(source_refs.get("work_unit_fingerprint")),
            }
        )
    if not refs:
        refs.append(
            {
                "role": "domain_action_request_materializer_preview",
                "ref": str(_consumer_latest_path_for_source_ref(profile)),
                "exists": False,
            }
        )
    return refs


def _consumer_latest_path_for_source_ref(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / "runtime" / "artifacts" / "supervision" / "consumer" / "latest.json"


def _fingerprint(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["paper_recovery_default_executor_dispatch_tasks"]
