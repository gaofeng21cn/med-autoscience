from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.domain_dispatch_evidence_payload import (
    build_domain_dispatch_evidence_record_payload,
)
from med_autoscience.profiles import WorkspaceProfile

from .export_study_projection_common import mapping, text


def opl_supervisor_decision_request_task(
    *,
    resolution_task: Mapping[str, Any],
    current_progress: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> dict[str, Any] | None:
    payload = mapping(resolution_task.get("payload"))
    supervisor_decision = mapping(payload.get("paper_autonomy_supervisor_decision"))
    if text(supervisor_decision.get("decision")) != "opl_supervisor_decision_readback_required":
        return None
    current_work_unit = mapping(payload.get("current_work_unit"))
    typed_blocker = mapping(payload.get("typed_blocker"))
    obligation_identity = _merged_obligation_identity(
        supervisor_decision=supervisor_decision,
        current_work_unit=current_work_unit,
    )
    if not _obligation_identity_complete(obligation_identity):
        return None
    source_fingerprint = _fingerprint(
        {
            "profile": profile.name,
            "study_id": study_id,
            "kind": "opl_supervisor_decision_request",
            "obligation_identity": dict(obligation_identity),
            "typed_blocker": dict(typed_blocker),
        }
    )
    obligation_id = (
        text(supervisor_decision.get("paper_autonomy_obligation_ref"))
        or text(supervisor_decision.get("paper_autonomy_obligation_id"))
        or text(mapping(current_progress.get("paper_recovery_state")).get("recovery_obligation_id"))
        or _obligation_id(
            study_id=study_id,
            obligation_identity=obligation_identity,
        )
    )
    current_identity = _current_identity(
        study_id=study_id,
        obligation_identity=obligation_identity,
        source_fingerprint=source_fingerprint,
        current_work_unit=current_work_unit,
    )
    reason = "opl_supervisor_decision_readback_required"
    source_refs = [
        dict(ref)
        for ref in (resolution_task.get("source_refs") or [])
        if isinstance(ref, Mapping)
    ]
    source_refs.append(
        {
            "role": "opl_supervisor_decision_request",
            "ref": obligation_id,
            "exists": True,
            "decision": "opl_supervisor_decision_readback_required",
        }
    )
    evidence_record_payload = build_domain_dispatch_evidence_record_payload(
        task_kind="paper_autonomy/supervisor-decision",
        study_id=study_id,
        reason=reason,
        evidence_refs=source_refs,
        source_fingerprint=source_fingerprint,
        profile_name=profile.name,
    )
    request = {
        "surface_kind": "mas_opl_paper_autonomy_supervisor_decision_request",
        "schema_version": 1,
        "request_role": "mas_policy_projection_to_opl_supervisor_decision_engine",
        "study_id": study_id,
        "quest_id": text(current_work_unit.get("quest_id")) or study_id,
        "obligation_id": obligation_id,
        "paper_autonomy_obligation_identity": dict(obligation_identity),
        "current_identity": current_identity,
        "requested_decision_readback_shape": "opl_paper_autonomy_supervisor_decision_readback",
        "requested_opl_command": "opl family-runtime paper-autonomy supervisor decide",
        "recommended_decision_evidence": _recommended_decision_evidence(
            typed_blocker=typed_blocker,
            supervisor_decision=supervisor_decision,
            source_refs=source_refs,
        ),
        "authority_boundary": {
            "request_owner": "med-autoscience",
            "decision_engine_owner": "one-person-lab",
            "recovery_obligation_store_owner": "one-person-lab",
            "decision_authority": False,
            "mas_can_run_supervisor_decision_engine": False,
            "mas_can_store_recovery_obligation": False,
            "mas_can_create_opl_command_event_or_outbox": False,
            "opl_can_write_mas_truth": False,
            "opl_can_create_domain_owner_receipt": False,
            "opl_can_create_domain_typed_blocker": False,
        },
    }
    return {
        "domain_id": "medautoscience",
        "task_kind": "paper_autonomy/supervisor-decision",
        "recommended_task_kind": "paper_autonomy/supervisor-decision",
        "priority": 75,
        "source": "mas-domain-handler-export",
        "requires_approval": False,
        "dedupe_key": f"mas:{profile.name}:{study_id}:opl-supervisor-decision:{source_fingerprint}",
        "source_fingerprint": source_fingerprint,
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "dispatch_owner": "one-person-lab",
        "profile_name": profile.name,
        "reason": reason,
        "source_refs": source_refs,
        "domain_dispatch_evidence_record_payload": evidence_record_payload,
        "payload": {
            "profile": str(profile_ref),
            "study_id": study_id,
            "source_fingerprint": source_fingerprint,
            "continuation_reason": reason,
            "paper_autonomy_supervisor_decision_request": request,
            "paper_autonomy_supervisor_decision": dict(supervisor_decision),
            "current_work_unit": dict(current_work_unit),
            "typed_blocker": dict(typed_blocker),
            "authority_boundary": "mas_request_projection_only_opl_supervisor_decision_engine",
        },
    }


def _obligation_identity_from_work_unit(
    *,
    current_work_unit: Mapping[str, Any],
) -> dict[str, Any]:
    fingerprint = text(current_work_unit.get("work_unit_fingerprint")) or text(
        current_work_unit.get("action_fingerprint")
    )
    idempotency_key = (
        text(current_work_unit.get("attempt_idempotency_key"))
        or text(current_work_unit.get("idempotency_key"))
        or (
            f"paper-autonomy-supervisor:{text(current_work_unit.get('study_id'))}:"
            f"{text(current_work_unit.get('action_type'))}:{text(current_work_unit.get('work_unit_id'))}:"
            f"{fingerprint}"
            if text(current_work_unit.get("study_id"))
            and text(current_work_unit.get("action_type"))
            and text(current_work_unit.get("work_unit_id"))
            and fingerprint
            else None
        )
    )
    return {
        key: value
        for key, value in {
            "study_id": text(current_work_unit.get("study_id")),
            "quest_id": text(current_work_unit.get("quest_id")) or text(current_work_unit.get("study_id")),
            "stage_id": text(current_work_unit.get("stage_id")) or "publication_supervision",
            "action_type": text(current_work_unit.get("action_type")),
            "work_unit_id": text(current_work_unit.get("work_unit_id")),
            "work_unit_fingerprint": fingerprint,
            "route_identity_key": text(current_work_unit.get("route_identity_key")) or idempotency_key,
            "attempt_idempotency_key": idempotency_key,
        }.items()
        if value not in (None, "")
    }


def _merged_obligation_identity(
    *,
    supervisor_decision: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
) -> dict[str, Any]:
    fallback = _obligation_identity_from_work_unit(
        current_work_unit=current_work_unit,
    )
    projected = mapping(supervisor_decision.get("paper_autonomy_obligation_identity"))
    return {
        key: projected_value or fallback.get(key)
        for key in (
            "study_id",
            "quest_id",
            "stage_id",
            "action_type",
            "work_unit_id",
            "work_unit_fingerprint",
            "route_identity_key",
            "attempt_idempotency_key",
        )
        if (projected_value := text(projected.get(key))) or fallback.get(key)
    }


def _obligation_identity_complete(identity: Mapping[str, Any]) -> bool:
    return all(
        text(identity.get(key)) is not None
        for key in (
            "study_id",
            "quest_id",
            "stage_id",
            "action_type",
            "work_unit_id",
            "work_unit_fingerprint",
            "route_identity_key",
            "attempt_idempotency_key",
        )
    )


def _obligation_id(
    *,
    study_id: str,
    obligation_identity: Mapping[str, Any],
) -> str:
    return "::".join(
        [
            "paper-autonomy-supervisor-obligation",
            study_id,
            text(obligation_identity.get("action_type")) or "unknown-action",
            text(obligation_identity.get("work_unit_id")) or "unknown-work-unit",
            text(obligation_identity.get("work_unit_fingerprint")) or "unknown-fingerprint",
        ]
    )


def _current_identity(
    *,
    study_id: str,
    obligation_identity: Mapping[str, Any],
    source_fingerprint: str,
    current_work_unit: Mapping[str, Any],
) -> dict[str, Any]:
    action_type = text(obligation_identity.get("action_type")) or "unknown-action"
    work_unit_id = text(obligation_identity.get("work_unit_id")) or "unknown-work-unit"
    work_unit_fingerprint = text(obligation_identity.get("work_unit_fingerprint")) or source_fingerprint
    stage_packet_ref = (
        text(current_work_unit.get("stage_packet_ref"))
        or f"mas://current-work-unit/{study_id}/{work_unit_id}/stage-packet"
    )
    raw_stage_packet_refs = current_work_unit.get("stage_packet_refs")
    stage_packet_refs = [
        ref for ref in raw_stage_packet_refs if isinstance(ref, str)
    ] if isinstance(raw_stage_packet_refs, list) else []
    return {
        "stage_run_id": text(current_work_unit.get("stage_run_id"))
        or f"stage-run:{study_id}:{action_type}:{work_unit_id}",
        "route_identity_key": text(obligation_identity.get("route_identity_key")) or source_fingerprint,
        "attempt_idempotency_key": (
            text(obligation_identity.get("attempt_idempotency_key")) or source_fingerprint
        ),
        "selected_dispatch_ref": text(current_work_unit.get("selected_dispatch_ref"))
        or f"mas://current-work-unit/{study_id}/{work_unit_id}",
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": _dedupe(
            [
                stage_packet_ref,
                *stage_packet_refs,
            ]
        ),
        "provider_attempt_ref": text(current_work_unit.get("provider_attempt_ref"))
        or f"opl://paper-autonomy-supervisor/{study_id}/{source_fingerprint}/provider-attempt",
        "attempt_lease_ref": text(current_work_unit.get("attempt_lease_ref"))
        or f"opl://paper-autonomy-supervisor/{study_id}/{source_fingerprint}/attempt-lease",
        "workflow_ref": text(current_work_unit.get("workflow_ref"))
        or f"opl://paper-autonomy-supervisor/{study_id}/{source_fingerprint}/workflow",
        "source_fingerprint": source_fingerprint,
        "truth_epoch": text(current_work_unit.get("truth_epoch")) or source_fingerprint,
        "runtime_health_epoch": text(current_work_unit.get("runtime_health_epoch")) or source_fingerprint,
        "work_unit_fingerprint": work_unit_fingerprint,
    }


def _recommended_decision_evidence(
    *,
    typed_blocker: Mapping[str, Any],
    supervisor_decision: Mapping[str, Any],
    source_refs: list[Mapping[str, Any]],
) -> dict[str, Any]:
    typed_blocker_ref = (
        text(typed_blocker.get("source_ref"))
        or text(typed_blocker.get("typed_blocker_ref"))
        or text(typed_blocker.get("blocker_id"))
        or "mas://typed-blocker/current-work-unit"
    )
    evidence_refs = _dedupe(
        [
            typed_blocker_ref,
            *[
                ref
                for ref in supervisor_decision.get("evidence_refs") or []
                if isinstance(ref, str)
            ],
            *[
                ref
                for item in source_refs
                if (ref := text(item.get("ref"))) is not None
            ],
        ]
    )
    return {
        "typed_blocker_ref": typed_blocker_ref,
        "budget_or_missing_evidence_ref": "mas://paper-autonomy/supervisor-decision-readback-required",
        "evidence_refs": evidence_refs,
        "observability_refs": [
            "study_progress.paper_recovery_state.supervisor_decision",
            "study_progress.current_work_unit",
        ],
    }


def _fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


__all__ = ["opl_supervisor_decision_request_task"]
