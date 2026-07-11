from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import opl_domain_progress_transition_contract as transition_contract
from med_autoscience.controllers.opl_transition_readback import (
    required_opl_transition_readback_shape,
)
from med_autoscience.controllers.stage_outcome_authority.owner_route_attempt_policy import normalize_currentness_sources

START_PROVIDER_ATTEMPT = "StartProviderAttempt"
MATERIALIZE_OWNER_ACTION = "MaterializeOwnerAction"
CONSUME_OWNER_RECEIPT = "ConsumeOwnerReceipt"
RECORD_TYPED_BLOCKER = "RecordTypedBlocker"
OPEN_HUMAN_GATE = "OpenHumanGate"
ADOPT_ROUTE_BACK_EVIDENCE = "AdoptRouteBackEvidence"
ADOPT_PAPER_DELTA = "AdoptPaperDelta"
STOP_LOSS = "StopLoss"
NON_ADVANCING_APPLY = "NonAdvancingApply"

FORBIDDEN_RUNTIME_FIELDS = transition_contract.request_forbidden_runtime_fields()


def build_transition_request(
    *,
    study_id: str,
    action_type: str,
    quest_id: str | None = None,
    work_unit_id: str | None = None,
    work_unit_fingerprint: str | None = None,
    next_owner: str | None = None,
    policy_kind: str = MATERIALIZE_OWNER_ACTION,
    source_generation: str | None = None,
    expected_version: str | None = None,
    dispatch_ref: str | None = None,
    dispatch_authority: str | None = None,
    required_output_surface: str | None = None,
    currentness_basis: Mapping[str, Any] | None = None,
    idempotency_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the MAS domain request consumed by the OPL transition runtime."""
    normalized_currentness_basis = normalize_currentness_sources(currentness_basis)
    identity = _clean(
        {
            "study_id": study_id,
            "quest_id": quest_id or study_id,
            "owner": next_owner,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_generation": source_generation or work_unit_fingerprint,
        }
    )
    request = _transition_request(policy_kind=policy_kind, identity=identity)
    if expected_version is not None:
        request["expected_version"] = expected_version
    if idempotency_context:
        request["idempotency_key"] = _stable_id(
            "paper-policy-request",
            [policy_kind, identity, dict(idempotency_context)],
        )
    request.update(
        _clean(
            {
                "dispatch_ref": dispatch_ref,
                "dispatch_authority": dispatch_authority,
                "required_output_surface": required_output_surface,
                "currentness_basis": normalized_currentness_basis,
                "action_fingerprint": work_unit_fingerprint,
            }
        )
    )
    return _clean(request)


def _transition_request(
    *,
    policy_kind: str,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    study_id = _text(identity.get("study_id"))
    work_unit_id = _text(identity.get("work_unit_id"))
    fingerprint = _text(identity.get("work_unit_fingerprint"))
    source_generation = _text(identity.get("source_generation")) or fingerprint
    return _clean(
        {
            "surface_kind": "mas_domain_progress_transition_request",
            "target_runtime_kind": transition_contract.RUNTIME_KIND,
            "target_runtime_owner": transition_contract.RUNTIME_OWNER,
            "request_owner": "med-autoscience",
            "authority_role": "domain_policy_request_only",
            "runtime_contract_ref": transition_contract.CONTRACT_REF,
            "mas_can_create_opl_outbox_record": False,
            "mas_can_create_opl_event": False,
            "mas_can_create_opl_stage_run": False,
            "runtime_kind": transition_contract.RUNTIME_KIND,
            "recommended_transition_kind": policy_kind,
            "aggregate_identity": {
                "aggregate_kind": "study_work_unit",
                "aggregate_id": "::".join(item for item in [study_id, work_unit_id] if item),
                "study_id": study_id,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
            "study_id": study_id,
            "quest_id": identity.get("quest_id"),
            "action_type": identity.get("action_type"),
            "next_owner": identity.get("owner"),
            "idempotency_key": _stable_id("paper-policy-request", [policy_kind, identity]),
            "source_generation": source_generation,
            "expected_version": source_generation,
            "required_postcondition": {
                "kind": _postcondition_kind(policy_kind),
                "outcome_owner": "one-person-lab",
                "domain_state_owner": "med-autoscience",
            },
            "provider_admission_requires_opl_readback_shape": required_opl_transition_readback_shape(),
            "domain_policy_result_ref": _stable_id("paper-policy", [policy_kind, identity]),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "forbidden_runtime_fields": list(FORBIDDEN_RUNTIME_FIELDS),
        }
    )


def _postcondition_kind(policy_kind: str) -> str:
    return {
        START_PROVIDER_ATTEMPT: "provider_admission_enqueued_or_blocked",
        MATERIALIZE_OWNER_ACTION: "owner_action_ref",
        CONSUME_OWNER_RECEIPT: "owner_receipt_consumed",
        RECORD_TYPED_BLOCKER: "typed_blocker_ref",
        OPEN_HUMAN_GATE: "human_gate_ref",
        ADOPT_ROUTE_BACK_EVIDENCE: "route_back_evidence_ref",
        ADOPT_PAPER_DELTA: "paper_delta_refs",
        STOP_LOSS: "stable_stop_loss_typed_blocker_ref",
        NON_ADVANCING_APPLY: "non_advancing_apply_typed_blocker_ref",
    }[policy_kind]


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _stable_id(prefix: str, parts: object) -> str:
    digest = hashlib.sha256(
        json.dumps(parts, ensure_ascii=True, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    return f"{prefix}:{digest}"


def _clean(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}
