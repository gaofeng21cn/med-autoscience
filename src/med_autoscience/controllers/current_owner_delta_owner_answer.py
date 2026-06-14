from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

from med_autoscience.controllers.guarded_apply_owner_delta_contract import (
    GUARDED_APPLY_DESIRED_DELTA,
    GUARDED_APPLY_STAGE_ID,
    guarded_apply_current_owner_delta_validation,
    guarded_apply_identity_typed_blocker,
    normalize_guarded_apply_current_owner_delta,
)


def materialize_current_owner_delta_owner_answer(
    current_owner_delta: Mapping[str, Any] | None,
) -> dict[str, Any]:
    validation = guarded_apply_current_owner_delta_validation(current_owner_delta)
    if validation.get("valid") is not True:
        return _blocked_result(current_owner_delta, validation=validation)

    delta = _mapping(current_owner_delta)
    normalized = normalize_guarded_apply_current_owner_delta(delta)
    domain_id = _text(delta.get("domain_id")) or _text(delta.get("domain")) or "medautoscience"
    current_owner = _text(normalized.get("current_owner")) or _text(normalized.get("owner")) or "med-autoscience"
    stage_id = _text(normalized.get("stage_id")) or GUARDED_APPLY_STAGE_ID
    delta_id = _text(delta.get("delta_id")) or _fallback_delta_id(domain_id=domain_id, stage_id=stage_id)
    task_or_study_ref = _text(delta.get("task_or_study_ref")) or "medautoscience:unknown-study"
    study_id = _study_id(task_or_study_ref)
    lineage_ref = _text(normalized.get("lineage_ref")) or "unknown-stage-attempt"
    source_fingerprint = _text(delta.get("source_fingerprint")) or lineage_ref
    generation = _generation(delta.get("generation"))
    stage_run_id = _stage_run_id(domain_id=domain_id, stage_id=stage_id)
    current_pointer_ref = f"opl://current-pointers/{stage_run_id}:g{generation}"
    stage_manifest_ref = f"mas://stage-manifests/{study_id}/{_slug(stage_id)}"
    idempotency_key = delta_id
    typed_blocker = _typed_blocker(
        current_owner=current_owner,
        delta_id=delta_id,
        domain_id=domain_id,
        stage_id=stage_id,
        task_or_study_ref=task_or_study_ref,
        study_id=study_id,
        lineage_ref=lineage_ref,
        source_fingerprint=source_fingerprint,
        stage_run_id=stage_run_id,
        generation=generation,
        current_pointer_ref=current_pointer_ref,
        stage_manifest_ref=stage_manifest_ref,
        idempotency_key=idempotency_key,
    )
    target_identity = _target_identity(
        current_owner=current_owner,
        delta_id=delta_id,
        domain_id=domain_id,
        stage_id=stage_id,
        task_or_study_ref=task_or_study_ref,
        lineage_ref=lineage_ref,
        source_fingerprint=source_fingerprint,
    )
    domain_owner_payload_summary_record = _domain_owner_payload_summary_record(
        target_identity=target_identity,
        typed_blocker=typed_blocker,
    )
    stage_run_authorization_record = _stage_run_authorization_record(
        typed_blocker=typed_blocker,
        delta_id=delta_id,
        domain_id=domain_id,
        study_id=study_id,
        stage_id=stage_id,
        generation=generation,
        stage_run_id=stage_run_id,
        lineage_ref=lineage_ref,
        source_fingerprint=source_fingerprint,
        task_or_study_ref=task_or_study_ref,
        current_pointer_ref=current_pointer_ref,
        stage_manifest_ref=stage_manifest_ref,
        idempotency_key=idempotency_key,
    )
    return {
        "surface_kind": "mas_current_owner_delta_owner_answer_materialization",
        "schema_version": 1,
        "status": "materialized",
        "write_permitted": False,
        "current_owner_delta_validation": validation,
        "target_identity": target_identity,
        "typed_blocker": typed_blocker,
        "domain_owner_payload_summary_record": domain_owner_payload_summary_record,
        "stage_run_authorization_record": stage_run_authorization_record,
        "authority_boundary": _authority_boundary(mas_created_typed_blocker=True),
    }


def _blocked_result(
    current_owner_delta: Mapping[str, Any] | None,
    *,
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    blocker = guarded_apply_identity_typed_blocker(current_owner_delta) or {
        "blocker_id": "current_owner_delta_identity_missing_or_invalid",
        "owner": "med-autoscience",
        "reason": "current_owner_delta identity is missing or invalid.",
    }
    return {
        "surface_kind": "mas_current_owner_delta_owner_answer_materialization",
        "schema_version": 1,
        "status": "blocked",
        "write_permitted": False,
        "typed_blocker": {
            **blocker,
            "blocker_type": "current_owner_delta_identity_missing_or_invalid",
            "latest_owner_answer_kind": "typed_blocker",
            "missing_required_fields": list(validation.get("missing_required_fields") or []),
            "domain_ready": False,
            "production_ready": False,
        },
        "current_owner_delta_validation": dict(validation),
        "authority_boundary": _authority_boundary(mas_created_typed_blocker=False),
    }


def _typed_blocker(
    *,
    current_owner: str,
    delta_id: str,
    domain_id: str,
    stage_id: str,
    task_or_study_ref: str,
    study_id: str,
    lineage_ref: str,
    source_fingerprint: str,
    stage_run_id: str,
    generation: int,
    current_pointer_ref: str,
    stage_manifest_ref: str,
    idempotency_key: str,
) -> dict[str, Any]:
    typed_blocker_ref = (
        f"mas-stage-typed-blocker:{domain_id}:{delta_id}:{study_id}:{lineage_ref}:"
        f"{_stage_ref_part(stage_id)}:owner-answer-required"
    )
    source_ref = f"mas://current-owner-delta-owner-answer/{_quote_ref(delta_id)}/{study_id}/{lineage_ref}"
    return {
        "surface_kind": "mas_current_owner_delta_owner_answer_typed_blocker",
        "schema_version": 1,
        "blocker_id": "current_owner_delta_owner_answer_required",
        "blocker_type": "owner_answer_required_current_pointer_bound_typed_blocker",
        "reason": "MAS owner answer is required before OPL can close current_owner_delta current pointer.",
        "owner": current_owner,
        "domain_id": domain_id,
        "stage_id": stage_id,
        "task_or_study_ref": task_or_study_ref,
        "study_id": study_id,
        "lineage_ref": lineage_ref,
        "current_owner_delta_id": delta_id,
        "source_fingerprint": source_fingerprint,
        "source_ref": source_ref,
        "typed_blocker_ref": typed_blocker_ref,
        "latest_owner_answer_ref": typed_blocker_ref,
        "latest_owner_answer_kind": "typed_blocker",
        "stage_run_id": stage_run_id,
        "generation": generation,
        "stage_manifest_ref": stage_manifest_ref,
        "current_pointer_ref": current_pointer_ref,
        "idempotency_key": idempotency_key,
        "domain_ready": False,
        "publication_ready": False,
        "quality_or_export_ready": False,
        "production_ready": False,
        "write_permitted": False,
        "authority_boundary": _authority_boundary(mas_created_typed_blocker=True),
    }


def _target_identity(
    *,
    current_owner: str,
    delta_id: str,
    domain_id: str,
    stage_id: str,
    task_or_study_ref: str,
    lineage_ref: str,
    source_fingerprint: str,
) -> dict[str, Any]:
    target_key = "/".join(
        [
            domain_id,
            "current_owner_delta_bridge",
            "owner_payload_item",
            delta_id,
            task_or_study_ref,
            lineage_ref,
            source_fingerprint,
        ]
    )
    return {
        "target_key": target_key,
        "domain_id": domain_id,
        "current_owner": current_owner,
        "source_surface": "current_owner_delta_bridge",
        "summary_kind": "owner_payload_item",
        "item_id": delta_id,
        "stage_id": stage_id,
        "task_or_study_ref": task_or_study_ref,
        "lineage_ref": lineage_ref,
        "current_owner_delta_id": delta_id,
        "source_fingerprint": source_fingerprint,
        "payload_kind": "domain_owner_receipt_or_typed_blocker_refs",
        "current_owner_delta_ref": "/framework_readiness/attention_first_payload/current_owner_delta",
    }


def _domain_owner_payload_summary_record(
    *,
    target_identity: Mapping[str, Any],
    typed_blocker: Mapping[str, Any],
) -> dict[str, Any]:
    target_key = _text(target_identity.get("target_key")) or "current-owner-delta"
    payload = {
        "source_ref": _text(typed_blocker.get("source_ref")),
        "typed_blocker_refs": [_text(typed_blocker.get("typed_blocker_ref"))],
        "receipt_ref": f"opl://domain-owner-payload-summary/{_quote_ref(target_key)}",
    }
    return {
        "surface_kind": "mas_opl_domain_owner_payload_summary_record_payload",
        "command": "opl runtime domain-owner-payload-summary record --target-identity <json> --payload <json>",
        "target_identity": dict(target_identity),
        "payload": payload,
        "authority_boundary": _opl_refs_only_record_boundary(),
    }


def _stage_run_authorization_record(
    *,
    typed_blocker: Mapping[str, Any],
    delta_id: str,
    domain_id: str,
    study_id: str,
    stage_id: str,
    generation: int,
    stage_run_id: str,
    lineage_ref: str,
    source_fingerprint: str,
    task_or_study_ref: str,
    current_pointer_ref: str,
    stage_manifest_ref: str,
    idempotency_key: str,
) -> dict[str, Any]:
    stage_attempt_id = lineage_ref
    typed_blocker_ref = _text(typed_blocker.get("typed_blocker_ref"))
    execution_authorization_decision_ref = (
        f"opl://stage-attempts/{stage_attempt_id}/execution-authorization/"
        "current-owner-delta-owner-answer"
    )
    payload = {
        "stage_run_id": stage_run_id,
        "domain_id": domain_id,
        "study_id": study_id,
        "domain_context": {
            "domain_id": domain_id,
            "study_id": study_id,
            "stage_id": stage_id,
        },
        "stage_id": stage_id,
        "generation": generation,
        "phase": "closeout",
        "selected_executor": "codex_cli",
        "provider_attempt_ref": f"opl://stage-attempts/{stage_attempt_id}",
        "stage_attempt_id": stage_attempt_id,
        "attempt_lease_ref": f"opl://stage-attempts/{stage_attempt_id}/leases/current",
        "attempt_lease_status": "active",
        "action_type": stage_id,
        "work_unit_id": GUARDED_APPLY_DESIRED_DELTA,
        "work_unit_fingerprint": source_fingerprint,
        "decision": "typed_blocker",
        "reason": "mas_owner_answer_required_current_pointer_bound_typed_blocker",
        "operator": "med-autoscience",
        "execution_authorization_decision_ref": execution_authorization_decision_ref,
        "workspace_scope_ref": task_or_study_ref,
        "artifact_scope_ref": lineage_ref,
        "source_fingerprint": source_fingerprint,
        "idempotency_key": idempotency_key,
        "current_pointer_ref": current_pointer_ref,
        "stage_manifest_ref": stage_manifest_ref,
        "owner_answer_ref": typed_blocker_ref,
        "owner_answer_kind": "typed_blocker",
        "owner_answer_stage_run_id": stage_run_id,
        "owner_answer_generation": generation,
        "owner_answer_manifest_ref": stage_manifest_ref,
        "owner_answer_current_pointer_ref": current_pointer_ref,
        "owner_answer_source_fingerprint": source_fingerprint,
        "owner_answer_idempotency_key": idempotency_key,
        "receipt_ref": (
            "opl://stage-run-execution-authorization/"
            f"{_quote_ref(stage_run_id)}/{_quote_ref(execution_authorization_decision_ref)}"
        ),
        "closeout_refs": [typed_blocker_ref],
        "authority_boundary": _opl_refs_only_record_boundary(),
    }
    return {
        "surface_kind": "mas_opl_stage_run_authorization_record_payload",
        "command": "opl runtime stage-run-authorization record --payload <json>",
        "payload": payload,
        "source_current_owner_delta_id": delta_id,
        "authority_boundary": _opl_refs_only_record_boundary(),
    }


def _authority_boundary(*, mas_created_typed_blocker: bool) -> dict[str, bool | str]:
    return {
        "owner": "med-autoscience",
        "refs_only_payloads": True,
        "mas_created_typed_blocker": mas_created_typed_blocker,
        "can_write_study_truth": False,
        "can_write_publication_eval": False,
        "can_write_current_package": False,
        "can_create_owner_receipt": False,
        "can_authorize_quality_or_export": False,
        "can_claim_domain_ready": False,
        "can_claim_production_ready": False,
    }


def _opl_refs_only_record_boundary() -> dict[str, bool | str]:
    return {
        "owner": "one-person-lab",
        "refs_only": True,
        "can_write_domain_truth": False,
        "can_create_owner_receipt": False,
        "can_create_typed_blocker": False,
        "can_close_domain_ready": False,
        "can_claim_domain_ready": False,
        "can_claim_production_ready": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _study_id(task_or_study_ref: str) -> str:
    text = task_or_study_ref.strip()
    if ":" in text:
        return text.rsplit(":", 1)[-1]
    if "/" in text:
        return text.rstrip("/").rsplit("/", 1)[-1]
    return text


def _stage_run_id(*, domain_id: str, stage_id: str) -> str:
    return ":".join(["app-stage-run", _slug(domain_id), _slug(stage_id)])


def _stage_ref_part(stage_id: str) -> str:
    return stage_id.replace("/", "-")


def _slug(value: str) -> str:
    result = []
    previous_dash = False
    for char in value.lower():
        if char.isalnum():
            result.append(char)
            previous_dash = False
            continue
        if not previous_dash:
            result.append("-")
            previous_dash = True
    return "".join(result).strip("-") or "unknown"


def _quote_ref(value: str) -> str:
    return quote(value, safe="-_.!~*'()")


def _generation(value: object) -> int:
    return int(value) if isinstance(value, int) and value >= 0 else 0


def _fallback_delta_id(*, domain_id: str, stage_id: str) -> str:
    return f"current-owner-delta:{domain_id}:{_slug(stage_id)}:owner-answer-or-typed-blocker"


__all__ = ["materialize_current_owner_delta_owner_answer"]
