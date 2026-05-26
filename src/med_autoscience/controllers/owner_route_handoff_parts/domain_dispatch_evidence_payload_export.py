from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from med_autoscience.profiles import WorkspaceProfile

from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)


SURFACE_KIND = "mas_domain_dispatch_evidence_payload_export"
PAYLOAD_REASON_CONSUMED_AI_REVIEWER_SUPERSESSION = (
    "stale_return_to_ai_reviewer_dispatch_superseded_by_consumed_ai_reviewer_routeback"
)
PAYLOAD_REASON_AI_REVIEWER_CURRENTNESS_SUPERSESSION = (
    "stale_run_quality_repair_dispatch_superseded_by_ai_reviewer_currentness_route"
)
PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_TYPED_BLOCKER = (
    "stage_attempt_closeout_typed_blocker_observed_for_default_executor_dispatch"
)
TASK_KIND = "domain_owner/default-executor-dispatch"
SUPPORTED_SUPERSEDED_ACTION_TYPE = "return_to_ai_reviewer_workflow"
SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE = "run_quality_repair_batch"
OPL_STAGE_ATTEMPT_ADMISSION_REASON = "opl_stage_attempt_admission_required"
OPL_RUNTIME_OWNER_ROUTE_REASON = "quest_waiting_opl_runtime_owner_route"
WRITE_OWNER = "write"
WRITE_ACTION_TYPE = "run_quality_repair_batch"


def study_id_from_workorder(workorder: Mapping[str, Any]) -> str | None:
    return _text(_mapping(workorder.get("target_identity")).get("study_id"))


def build_dispatch_evidence_payload_export(
    *,
    profile: WorkspaceProfile,
    profile_ref: object,
    workorder: Mapping[str, Any],
    owner_route_scan: Mapping[str, Any],
) -> dict[str, Any]:
    target_identity = _mapping(workorder.get("target_identity"))
    dispatch_identity = _mapping(workorder.get("dispatch_identity_fields"))
    study_id = _text(target_identity.get("study_id"))
    if study_id is None:
        return _blocked(
            profile=profile,
            profile_ref=profile_ref,
            workorder=workorder,
            blocked_reason="workorder_target_study_id_missing",
        )
    action_type = _text(dispatch_identity.get("action_type"))
    if action_type not in {
        SUPPORTED_SUPERSEDED_ACTION_TYPE,
        SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE,
    }:
        return _blocked(
            profile=profile,
            profile_ref=profile_ref,
            workorder=workorder,
            blocked_reason="unsupported_dispatch_supersession_payload",
        )
    study_scan = _study_scan(owner_route_scan, study_id=study_id)
    if study_scan is None:
        return _blocked(
            profile=profile,
            profile_ref=profile_ref,
            workorder=workorder,
            blocked_reason="owner_route_scan_study_missing",
        )
    payload_reason = _payload_reason_for_superseded_dispatch(
        action_type=action_type,
        study_scan=study_scan,
    )
    closeout_evidence = _stage_attempt_closeout_typed_blocker_evidence(
        profile=profile,
        study_id=study_id,
        target_identity=target_identity,
        dispatch_identity=dispatch_identity,
        action_type=action_type,
    )
    if payload_reason is None and closeout_evidence is not None:
        payload_reason = PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_TYPED_BLOCKER
    if payload_reason is None:
        return _blocked(
            profile=profile,
            profile_ref=profile_ref,
            workorder=workorder,
            blocked_reason=_blocked_reason_for_action_type(action_type),
        )

    domain_transition = _mapping(study_scan.get("domain_transition"))
    completion = _mapping(domain_transition.get("completion_receipt_consumption"))
    owner_route = _mapping(study_scan.get("owner_route"))
    typed_blocker_refs: Sequence[object] = ()
    if closeout_evidence is not None and payload_reason == PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_TYPED_BLOCKER:
        evidence_refs = _closeout_evidence_refs(closeout_evidence)
        typed_blocker_refs = _sequence(closeout_evidence.get("typed_blocker_refs"))
    else:
        evidence_refs = _evidence_refs(
            dispatch_identity=dispatch_identity,
            domain_transition=domain_transition,
            completion=completion,
            owner_route=owner_route,
            study_scan=study_scan,
        )
    stage_attempt_source_fingerprint = _text(target_identity.get("source_fingerprint"))
    domain_source_fingerprint = _text(target_identity.get("domain_source_fingerprint"))
    evidence_payload = build_domain_dispatch_evidence_record_payload(
        task_kind=_text(target_identity.get("task_kind")) or TASK_KIND,
        study_id=study_id,
        stage_id=_text(target_identity.get("stage_id")),
        reason=payload_reason,
        evidence_refs=evidence_refs,
        typed_blocker_refs=typed_blocker_refs,
        source_fingerprint=domain_source_fingerprint,
        stage_attempt_source_fingerprint=stage_attempt_source_fingerprint,
        profile_name=_text(target_identity.get("profile_name")) or profile.name,
    )
    return {
        "surface_kind": SURFACE_KIND,
        "status": "typed_blocker_payload_ready",
        "profile": str(profile_ref),
        "profile_name": profile.name,
        "study_id": study_id,
        "workorder_action_id": _text(workorder.get("action_id")),
        "stage_attempt_id": _text(target_identity.get("stage_attempt_id")),
        "payload_reason": payload_reason,
        "target_identity": dict(target_identity),
        "dispatch_identity_fields": dict(dispatch_identity),
        "domain_transition_receipt_consumption": dict(completion),
        "owner_route_next_owner": _text(owner_route.get("next_owner")),
        "owner_route_owner_reason": _text(owner_route.get("owner_reason")),
        "domain_dispatch_evidence_record_payload": evidence_payload,
        "opl_runtime_action_execute_payload": evidence_payload["opl_runtime_action_execute_payload"],
        "authority_boundary": _authority_boundary(),
    }


def _blocked(
    *,
    profile: WorkspaceProfile,
    profile_ref: object,
    workorder: Mapping[str, Any],
    blocked_reason: str,
) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "status": "blocked",
        "blocked_reason": blocked_reason,
        "profile": str(profile_ref),
        "profile_name": profile.name,
        "study_id": study_id_from_workorder(workorder),
        "workorder_action_id": _text(workorder.get("action_id")),
        "target_identity": dict(_mapping(workorder.get("target_identity"))),
        "dispatch_identity_fields": dict(_mapping(workorder.get("dispatch_identity_fields"))),
        "authority_boundary": _authority_boundary(),
    }


def _consumed_ai_reviewer_routeback_observed(study_scan: Mapping[str, Any]) -> bool:
    domain_transition = _mapping(study_scan.get("domain_transition"))
    completion = _mapping(domain_transition.get("completion_receipt_consumption"))
    owner_route = _mapping(study_scan.get("owner_route"))
    return (
        _text(completion.get("status")) == "consumed"
        and _text(completion.get("receipt_kind")) == "ai_reviewer_publication_eval"
        and _text(domain_transition.get("route_target")) == "write"
        and _text(domain_transition.get("owner")) == "write"
        and _text(domain_transition.get("controller_action")) == "request_opl_stage_attempt"
        and (
            _opl_stage_admission_observed(study_scan=study_scan, owner_route=owner_route)
            or _registered_write_routeback_transport_wait_observed(
                study_scan=study_scan,
                owner_route=owner_route,
            )
        )
    )


def _opl_stage_admission_observed(
    *,
    study_scan: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    return (
        _text(owner_route.get("next_owner")) == "one-person-lab"
        and (
            _text(study_scan.get("blocked_reason")) == OPL_STAGE_ATTEMPT_ADMISSION_REASON
            or _text(owner_route.get("owner_reason")) == OPL_STAGE_ATTEMPT_ADMISSION_REASON
        )
    )


def _registered_write_routeback_transport_wait_observed(
    *,
    study_scan: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    owner_reason_contract = _mapping(owner_route.get("owner_reason_contract"))
    currentness_contract = _mapping(owner_route.get("currentness_contract"))
    attempt_protocol = _mapping(owner_route.get("owner_route_attempt_protocol"))
    return (
        _text(owner_route.get("next_owner")) == "external_supervisor"
        and (
            _text(study_scan.get("blocked_reason")) == OPL_RUNTIME_OWNER_ROUTE_REASON
            or _text(owner_route.get("owner_reason")) == OPL_RUNTIME_OWNER_ROUTE_REASON
        )
        and owner_reason_contract.get("registered") is True
        and _text(owner_reason_contract.get("owner")) == WRITE_OWNER
        and WRITE_ACTION_TYPE in set(_texts(_sequence(owner_reason_contract.get("allowed_actions"))))
        and currentness_contract.get("missing_required_fields") == []
        and attempt_protocol.get("dispatchable") is False
    )


def _ai_reviewer_currentness_supersession_observed(study_scan: Mapping[str, Any]) -> bool:
    domain_transition = _mapping(study_scan.get("domain_transition"))
    completion = _mapping(domain_transition.get("completion_receipt_consumption"))
    owner_route = _mapping(study_scan.get("owner_route"))
    blocked_reason = _text(study_scan.get("blocked_reason")) or _text(owner_route.get("owner_reason"))
    return (
        _text(completion.get("status")) == "consumed"
        and _text(completion.get("receipt_kind")) == "ai_reviewer_publication_eval"
        and _text(domain_transition.get("controller_action")) == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and _text(domain_transition.get("owner")) == "ai_reviewer"
        and _text(owner_route.get("next_owner")) == "ai_reviewer"
        and blocked_reason == "ai_reviewer_record_stale_after_current_manuscript"
    )


def _payload_reason_for_superseded_dispatch(
    *,
    action_type: str | None,
    study_scan: Mapping[str, Any],
) -> str | None:
    if (
        action_type == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and _consumed_ai_reviewer_routeback_observed(study_scan)
    ):
        return PAYLOAD_REASON_CONSUMED_AI_REVIEWER_SUPERSESSION
    if (
        action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE
        and _ai_reviewer_currentness_supersession_observed(study_scan)
    ):
        return PAYLOAD_REASON_AI_REVIEWER_CURRENTNESS_SUPERSESSION
    return None


def _blocked_reason_for_action_type(action_type: str | None) -> str:
    if action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE:
        return "ai_reviewer_currentness_supersession_not_observed"
    return "consumed_ai_reviewer_routeback_not_observed"


def _stage_attempt_closeout_typed_blocker_evidence(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    target_identity: Mapping[str, Any],
    dispatch_identity: Mapping[str, Any],
    action_type: str | None,
) -> dict[str, Any] | None:
    stage_attempt_id = _text(target_identity.get("stage_attempt_id"))
    if stage_attempt_id is None or action_type is None:
        return None
    closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / f"{stage_attempt_id}.closeout.json"
    )
    closeout = _read_json_object(closeout_path)
    if closeout is None:
        return None
    domain_blocker = _mapping(closeout.get("domain_blocker"))
    typed_blocker_ref = _text(closeout.get("typed_blocker_ref"))
    if (
        _text(closeout.get("surface_kind")) != "stage_attempt_closeout_packet"
        or _text(closeout.get("stage_attempt_id")) != stage_attempt_id
        or _text(closeout.get("stage_id")) != _text(target_identity.get("stage_id"))
        or _text(closeout.get("study_id")) != study_id
        or _text(closeout.get("action_type")) != action_type
        or _text(closeout.get("status")) != "blocked"
        or _text(closeout.get("blocked_reason")) is None
        or _text(domain_blocker.get("surface_kind")) != "mas_domain_typed_blocker"
        or typed_blocker_ref is None
        or closeout.get("provider_completion_is_domain_completion") is not False
    ):
        return None
    return {
        "closeout_ref": _relative_stage_attempt_closeout_ref(
            study_id=study_id,
            stage_attempt_id=stage_attempt_id,
        ),
        "closeout_refs": _sequence(closeout.get("closeout_refs")),
        "typed_blocker_refs": [typed_blocker_ref],
        "dispatch_ref": _text(dispatch_identity.get("dispatch_ref")),
        "blocked_reason": _text(closeout.get("blocked_reason")),
        "domain_blocker_reason": _text(domain_blocker.get("reason")),
        "domain_blocker_next_owner": _text(domain_blocker.get("next_owner")),
        "execution_blocked_reason": _text(_mapping(closeout.get("execution_observation")).get("blocked_reason")),
    }


def _closeout_evidence_refs(closeout_evidence: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    refs.extend(
        _texts(
            [
                closeout_evidence.get("dispatch_ref"),
                closeout_evidence.get("closeout_ref"),
            ]
        )
    )
    refs.extend(_texts(_sequence(closeout_evidence.get("closeout_refs"))))
    refs.extend(_texts(_sequence(closeout_evidence.get("typed_blocker_refs"))))
    refs.extend(
        _texts(
            [
                f"stage-attempt-closeout:blocked_reason={_text(closeout_evidence.get('blocked_reason'))}",
                (
                    "stage-attempt-closeout:domain_blocker_reason="
                    f"{_text(closeout_evidence.get('domain_blocker_reason'))}"
                ),
                (
                    "stage-attempt-closeout:domain_blocker_next_owner="
                    f"{_text(closeout_evidence.get('domain_blocker_next_owner'))}"
                ),
                (
                    "stage-attempt-closeout:execution_blocked_reason="
                    f"{_text(closeout_evidence.get('execution_blocked_reason'))}"
                ),
            ]
        )
    )
    return _unique(refs)


def _relative_stage_attempt_closeout_ref(*, study_id: str, stage_attempt_id: str) -> str:
    return (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_execution/"
        f"{stage_attempt_id}.closeout.json"
    )


def _read_json_object(path: object) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))  # type: ignore[attr-defined]
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _evidence_refs(
    *,
    dispatch_identity: Mapping[str, Any],
    domain_transition: Mapping[str, Any],
    completion: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    study_scan: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    refs.extend(
        _texts(
            [
                dispatch_identity.get("dispatch_ref"),
                completion.get("receipt_ref"),
                completion.get("reviewer_trace_ref"),
            ]
        )
    )
    refs.extend(_texts(_sequence(domain_transition.get("source_refs"))))
    refs.extend(_texts(_sequence(_mapping(owner_route.get("source_refs")).values())))
    refs.extend(
        _texts(
            [
                "owner-route-reconcile:completion_receipt_consumption=consumed",
                f"owner-route-reconcile:route_target={_text(domain_transition.get('route_target'))}",
                f"owner-route-reconcile:controller_action={_text(domain_transition.get('controller_action'))}",
                f"owner-route-reconcile:blocked_reason={_text(study_scan.get('blocked_reason')) or _text(owner_route.get('owner_reason'))}",
                f"owner-route-reconcile:owner_route_next_owner={_text(owner_route.get('next_owner'))}",
            ]
        )
    )
    return _unique(refs)


def _study_scan(owner_route_scan: Mapping[str, Any], *, study_id: str) -> Mapping[str, Any] | None:
    for study in _sequence(owner_route_scan.get("studies")):
        if isinstance(study, Mapping) and _text(study.get("study_id")) == study_id:
            return study
    return None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else ()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _texts(values: Sequence[object]) -> list[str]:
    return [text for value in values if (text := _text(value)) is not None]


def _unique(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _authority_boundary() -> dict[str, object]:
    return {
        "owner": "med-autoscience",
        "payload_kind": "refs_only_domain_owned_typed_blocker_payload",
        "opl_records_refs_only": True,
        "writes_mas_truth": False,
        "creates_owner_receipt": False,
        "claims_domain_ready": False,
        "claims_publication_ready": False,
        "claims_production_ready": False,
        "reads_or_writes_artifact_body": False,
        "reads_or_writes_memory_body": False,
    }


__all__ = [
    "PAYLOAD_REASON_CONSUMED_AI_REVIEWER_SUPERSESSION",
    "build_dispatch_evidence_payload_export",
    "study_id_from_workorder",
]
