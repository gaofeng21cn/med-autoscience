from __future__ import annotations

from typing import Any, Mapping, Sequence

from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)
from med_autoscience.controllers.stable_blocker_classes import (
    blocker_details,
    blocker_explanation,
    source_refs_from_payloads,
    stable_blocker_class,
)
from med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export_parts.closeout_evidence import (
    closeout_evidence_refs,
    owner_receipt_closeout_evidence_refs,
    stage_attempt_closeout_owner_receipt_evidence,
    stage_attempt_closeout_typed_blocker_evidence,
)
from med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export_parts.route_reasons import (
    blocked_reason_for_action_type,
    payload_reason_for_superseded_dispatch,
)
from med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export_parts.shared import (
    PAYLOAD_REASON_CONSUMED_AI_REVIEWER_SUPERSESSION,
    PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_OWNER_RECEIPT,
    PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_TYPED_BLOCKER,
    SUPPORTED_SUPERSEDED_ACTION_TYPE,
    SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE,
    SURFACE_KIND,
    TASK_KIND,
    authority_boundary,
    mapping,
    sequence,
    text,
    texts,
    unique,
)


def study_id_from_workorder(workorder: Mapping[str, Any]) -> str | None:
    return text(mapping(workorder.get("target_identity")).get("study_id"))


def build_dispatch_evidence_payload_export(
    *,
    profile: Any,
    profile_ref: object,
    workorder: Mapping[str, Any],
    owner_route_scan: Mapping[str, Any],
) -> dict[str, Any]:
    target_identity = mapping(workorder.get("target_identity"))
    dispatch_identity = mapping(workorder.get("dispatch_identity_fields"))
    study_id = text(target_identity.get("study_id"))
    if study_id is None:
        return _blocked(
            profile=profile,
            profile_ref=profile_ref,
            workorder=workorder,
            blocked_reason="workorder_target_study_id_missing",
        )
    action_type = text(dispatch_identity.get("action_type"))
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
    payload_detail_reason = payload_reason_for_superseded_dispatch(
        action_type=action_type,
        study_scan=study_scan,
    )
    closeout_evidence = stage_attempt_closeout_typed_blocker_evidence(
        profile=profile,
        study_id=study_id,
        target_identity=target_identity,
        dispatch_identity=dispatch_identity,
        action_type=action_type,
    )
    owner_receipt_closeout = stage_attempt_closeout_owner_receipt_evidence(
        profile=profile,
        study_id=study_id,
        target_identity=target_identity,
        dispatch_identity=dispatch_identity,
        action_type=action_type,
    )
    if payload_detail_reason is None and owner_receipt_closeout is not None:
        payload_detail_reason = PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_OWNER_RECEIPT
    if payload_detail_reason is None and closeout_evidence is not None:
        payload_detail_reason = PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_TYPED_BLOCKER
    if payload_detail_reason is None:
        return _blocked(
            profile=profile,
            profile_ref=profile_ref,
            workorder=workorder,
            blocked_reason=blocked_reason_for_action_type(action_type),
        )

    domain_transition = mapping(study_scan.get("domain_transition"))
    completion = mapping(domain_transition.get("completion_receipt_consumption"))
    owner_route = mapping(study_scan.get("owner_route"))
    domain_authority_handoff = mapping(study_scan.get("domain_authority_handoff"))
    typed_blocker_refs: Sequence[object] = ()
    domain_owner_receipt_refs: Sequence[object] = ()
    no_regression_evidence_refs: Sequence[object] = ()
    if (
        owner_receipt_closeout is not None
        and payload_detail_reason == PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_OWNER_RECEIPT
    ):
        evidence_refs = owner_receipt_closeout_evidence_refs(owner_receipt_closeout)
        domain_owner_receipt_refs = sequence(owner_receipt_closeout.get("owner_receipt_refs"))
        no_regression_evidence_refs = [
            (
                "mas-no-forbidden-write-proof:medautoscience:"
                f"{text(target_identity.get('stage_attempt_id'))}:"
                "refs-only-owner-receipt-closeout"
            )
        ]
    elif closeout_evidence is not None and payload_detail_reason == PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_TYPED_BLOCKER:
        evidence_refs = closeout_evidence_refs(closeout_evidence)
        typed_blocker_refs = sequence(closeout_evidence.get("typed_blocker_refs"))
    else:
        evidence_refs = _evidence_refs(
            dispatch_identity=dispatch_identity,
            domain_transition=domain_transition,
            completion=completion,
            owner_route=owner_route,
            study_scan=study_scan,
            domain_authority_handoff=domain_authority_handoff,
        )
    payload_blocker_class = stable_blocker_class(payload_detail_reason) or payload_detail_reason
    payload_reason = payload_blocker_class
    reason_source_refs = source_refs_from_payloads(
        owner_route,
        domain_transition,
        completion,
        domain_authority_handoff,
        extra_refs=evidence_refs,
    )
    reason_details = blocker_details(
        blocker_class=payload_blocker_class,
        detail_reason=payload_detail_reason,
        action_type=action_type,
        owner_route=owner_route,
        domain_transition=domain_transition,
        blocked_reason=text(study_scan.get("blocked_reason")),
    )
    if (
        owner_receipt_closeout is not None
        and payload_detail_reason == PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_OWNER_RECEIPT
    ):
        reason_details = {
            **reason_details,
            **_owner_receipt_research_evidence_details(
                stage_attempt_id=text(target_identity.get("stage_attempt_id")),
                evidence_refs=evidence_refs,
                domain_owner_receipt_refs=domain_owner_receipt_refs,
                no_regression_evidence_refs=no_regression_evidence_refs,
            ),
        }
    explanation = blocker_explanation(payload_blocker_class)
    stage_attempt_source_fingerprint = text(target_identity.get("source_fingerprint"))
    domain_source_fingerprint = text(target_identity.get("domain_source_fingerprint"))
    evidence_payload = build_domain_dispatch_evidence_record_payload(
        task_kind=text(target_identity.get("task_kind")) or TASK_KIND,
        study_id=study_id,
        stage_id=text(target_identity.get("stage_id")),
        reason=payload_reason,
        evidence_refs=evidence_refs,
        domain_owner_receipt_refs=domain_owner_receipt_refs,
        typed_blocker_refs=typed_blocker_refs,
        no_regression_evidence_refs=no_regression_evidence_refs,
        reason_details=reason_details,
        reason_source_refs=reason_source_refs,
        explanation=explanation,
        source_fingerprint=domain_source_fingerprint,
        stage_attempt_source_fingerprint=stage_attempt_source_fingerprint,
        profile_name=text(target_identity.get("profile_name")) or profile.name,
    )
    return {
        "surface_kind": SURFACE_KIND,
        "status": (
            "owner_receipt_payload_ready"
            if payload_detail_reason == PAYLOAD_REASON_STAGE_ATTEMPT_CLOSEOUT_OWNER_RECEIPT
            else "typed_blocker_payload_ready"
        ),
        "profile": str(profile_ref),
        "profile_name": profile.name,
        "study_id": study_id,
        "workorder_action_id": text(workorder.get("action_id")),
        "stage_attempt_id": text(target_identity.get("stage_attempt_id")),
        "payload_reason": payload_reason,
        "payload_detail_reason": payload_detail_reason,
        "payload_blocker_class": payload_blocker_class,
        "details": reason_details,
        "source_refs": reason_source_refs,
        **({"explanation": explanation} if explanation is not None else {}),
        "target_identity": dict(target_identity),
        "dispatch_identity_fields": dict(dispatch_identity),
        "domain_transition_receipt_consumption": dict(completion),
        "owner_route_next_owner": text(owner_route.get("next_owner")),
        "owner_route_owner_reason": text(owner_route.get("owner_reason")),
        "domain_dispatch_evidence_record_payload": evidence_payload,
        "opl_runtime_action_execute_payload": evidence_payload["opl_runtime_action_execute_payload"],
        "authority_boundary": authority_boundary(),
    }


def _blocked(
    *,
    profile: Any,
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
        "workorder_action_id": text(workorder.get("action_id")),
        "target_identity": dict(mapping(workorder.get("target_identity"))),
        "dispatch_identity_fields": dict(mapping(workorder.get("dispatch_identity_fields"))),
        "authority_boundary": authority_boundary(),
    }


def _evidence_refs(
    *,
    dispatch_identity: Mapping[str, Any],
    domain_transition: Mapping[str, Any],
    completion: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    study_scan: Mapping[str, Any],
    domain_authority_handoff: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    refs.extend(
        texts(
            [
                dispatch_identity.get("dispatch_ref"),
                completion.get("receipt_ref"),
                completion.get("reviewer_trace_ref"),
            ]
        )
    )
    refs.extend(texts(sequence(domain_transition.get("source_refs"))))
    refs.extend(texts(sequence(mapping(owner_route.get("source_refs")).values())))
    blocked_reason = text(study_scan.get("blocked_reason")) or text(owner_route.get("owner_reason"))
    refs.extend(
        texts(
            [
                (
                    "owner-route-reconcile:completion_receipt_consumption=consumed"
                    if text(completion.get("status")) == "consumed"
                    else None
                ),
                _label_ref("owner-route-reconcile:route_target", domain_transition.get("route_target")),
                _label_ref(
                    "owner-route-reconcile:controller_action",
                    domain_transition.get("controller_action"),
                ),
                _label_ref("owner-route-reconcile:blocked_reason", blocked_reason),
                f"owner-route-reconcile:owner_route_next_owner={text(owner_route.get('next_owner'))}",
                _label_ref(
                    "opl-provider-attempt:active_stage_attempt_id",
                    study_scan.get("active_stage_attempt_id"),
                ),
                (
                    "opl-provider-attempt:running_provider_attempt=true"
                    if study_scan.get("running_provider_attempt") is True
                    else None
                ),
            ]
        )
    )
    typed_blocker = mapping(domain_authority_handoff.get("typed_blocker"))
    if text(domain_authority_handoff.get("status")) == "typed_blocker":
        attempt_protocol = mapping(owner_route.get("owner_route_attempt_protocol"))
        refs.extend(
            texts(
                [
                    "domain-authority-handoff:status=typed_blocker",
                    (
                        "domain-authority-handoff:typed_blocker_reason="
                        f"{text(typed_blocker.get('reason'))}"
                    ),
                    (
                        "domain-authority-handoff:owner_route_attempt_dispatchable="
                        f"{str(attempt_protocol.get('dispatchable')).lower()}"
                    ),
                    text(typed_blocker.get("idempotency_key")),
                    text(typed_blocker.get("source_fingerprint")),
                ]
            )
        )
    return unique(refs)


def _label_ref(label: str, value: object) -> str | None:
    if (ref_value := text(value)) is None:
        return None
    return f"{label}={ref_value}"


def _owner_receipt_research_evidence_details(
    *,
    stage_attempt_id: str | None,
    evidence_refs: Sequence[object],
    domain_owner_receipt_refs: Sequence[object],
    no_regression_evidence_refs: Sequence[object],
) -> dict[str, list[str]]:
    scope = text(stage_attempt_id) or "unknown-stage-attempt"
    return {
        "negative_failed_path_refs": [
            f"mas-negative-failed-path-ledger:medautoscience:domain-dispatch-owner-receipt:{scope}",
        ],
        "decision_trace_refs": unique(
            [
                *texts(domain_owner_receipt_refs),
                *texts(evidence_refs),
            ]
        ),
        "artifact_lineage_refs": unique(texts(evidence_refs)),
        "reproducibility_refs": unique(
            [
                *texts(no_regression_evidence_refs),
                *texts(domain_owner_receipt_refs),
            ]
        ),
    }


def _study_scan(owner_route_scan: Mapping[str, Any], *, study_id: str) -> Mapping[str, Any] | None:
    for study in sequence(owner_route_scan.get("studies")):
        if isinstance(study, Mapping) and text(study.get("study_id")) == study_id:
            return study
    return None


__all__ = [
    "PAYLOAD_REASON_CONSUMED_AI_REVIEWER_SUPERSESSION",
    "build_dispatch_evidence_payload_export",
    "study_id_from_workorder",
]
