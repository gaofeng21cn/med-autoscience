from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

SURFACE_KIND = "paper_progress_policy_adapter_result"
SCHEMA_VERSION = 1
AUTHORITY = "med_autoscience.paper_progress_policy_adapter"

START_PROVIDER_ATTEMPT = "StartProviderAttempt"
MATERIALIZE_OWNER_ACTION = "MaterializeOwnerAction"
CONSUME_OWNER_RECEIPT = "ConsumeOwnerReceipt"
RECORD_TYPED_BLOCKER = "RecordTypedBlocker"
NON_ADVANCING_APPLY = "NonAdvancingApply"

_PROVIDER_ADMISSION_NEXT_KINDS = {
    "admit_provider_attempt",
    "admit_identity_bound_stage_packet",
    "materialize_successor_owner_action",
}
_OWNER_ACTION_NEXT_KINDS = {
    "run_mas_owner_callable",
    "materialize_provider_admission_or_owner_callable",
    "materialize_successor_owner_gate",
    "resolve_owner_gate_decision",
    "route_back_to_owner_or_repair_materialization",
}


def build_policy_result(payload: Mapping[str, Any], *, source: str = "paper_progress") -> dict[str, Any]:
    current_work_unit = _mapping(payload.get("current_work_unit"))
    current_action = _mapping(payload.get("current_executable_owner_action"))
    recovery = _mapping(payload.get("paper_recovery_state"))
    next_action = _mapping(recovery.get("next_safe_action"))
    policy_kind = _policy_kind(
        payload=payload,
        current_work_unit=current_work_unit,
        current_action=current_action,
        recovery=recovery,
        next_action=next_action,
    )
    if policy_kind is None:
        return {}
    identity = _identity(
        payload=payload,
        current_work_unit=current_work_unit,
        current_action=current_action,
        recovery=recovery,
        next_action=next_action,
    )
    result = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "authority": AUTHORITY,
        "authority_role": "paper_domain_policy_adapter_only",
        "source": source,
        "policy_result_id": _stable_id("paper-policy", [policy_kind, identity]),
        "recommended_opl_transition_kind": policy_kind,
        "study_id": identity.get("study_id"),
        "quest_id": identity.get("quest_id"),
        "owner": identity.get("owner"),
        "action_type": identity.get("action_type"),
        "work_unit_id": identity.get("work_unit_id"),
        "work_unit_fingerprint": identity.get("work_unit_fingerprint"),
        "paper_policy_verdict": _paper_policy_verdict(policy_kind),
        "opl_domain_progress_command": _opl_domain_progress_command(
            policy_kind=policy_kind,
            identity=identity,
        ),
        "authority_boundary": {
            "mas_can_accept_owner_receipt": True,
            "mas_can_create_domain_typed_blocker": True,
            "mas_can_authorize_paper_delta": True,
            "mas_can_authorize_provider_admission": False,
            "mas_can_run_fixed_point_reconciler": False,
            "mas_can_own_event_log_or_outbox": False,
            "opl_owns_transition_runtime": True,
            "provider_completion_is_domain_completion": False,
        },
        "forbidden_writes": [
            "publication_ready_claim_without_mas_gate",
            "paper_artifact_mutation_without_mas_authority",
            "owner_receipt_created_by_opl",
            "typed_blocker_created_by_opl",
            "provider_completion_as_paper_ready",
        ],
    }
    return _clean(result)


def build_non_advancing_policy_blocker(
    payload: Mapping[str, Any],
    *,
    reason: str = "fresh_readback_did_not_advance_same_aggregate",
) -> dict[str, Any]:
    result = build_policy_result(payload, source="paper_progress.non_advancing_apply")
    if not result:
        identity = _identity(
            payload=payload,
            current_work_unit=_mapping(payload.get("current_work_unit")),
            current_action=_mapping(payload.get("current_executable_owner_action")),
            recovery=_mapping(payload.get("paper_recovery_state")),
            next_action=_mapping(_mapping(payload.get("paper_recovery_state")).get("next_safe_action")),
        )
        result = {
            "surface_kind": SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "authority": AUTHORITY,
            "authority_role": "paper_domain_policy_adapter_only",
            "policy_result_id": _stable_id("paper-policy", [NON_ADVANCING_APPLY, identity]),
            "recommended_opl_transition_kind": NON_ADVANCING_APPLY,
            "study_id": identity.get("study_id"),
            "quest_id": identity.get("quest_id"),
            "owner": identity.get("owner"),
            "action_type": identity.get("action_type"),
            "work_unit_id": identity.get("work_unit_id"),
            "work_unit_fingerprint": identity.get("work_unit_fingerprint"),
        }
    result["paper_policy_verdict"] = {
        "verdict": "stable_typed_blocker_required",
        "typed_blocker_type": "non_advancing_apply",
        "reason": reason,
    }
    result["recommended_opl_transition_kind"] = NON_ADVANCING_APPLY
    return _clean(result)


def _policy_kind(
    *,
    payload: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> str | None:
    status = _text(current_work_unit.get("status"))
    phase = _text(recovery.get("phase"))
    next_kind = _text(next_action.get("kind"))
    if status in {"typed_blocker", "blocked_current_work_unit"} or _mapping(payload.get("typed_blocker")):
        return RECORD_TYPED_BLOCKER
    if next_kind in _PROVIDER_ADMISSION_NEXT_KINDS and next_action.get("provider_admission_allowed") is True:
        return START_PROVIDER_ATTEMPT
    if status == "owner_receipt_recorded" or phase == "owner_receipt_recorded":
        return CONSUME_OWNER_RECEIPT
    if next_kind == "consume_owner_receipt":
        return CONSUME_OWNER_RECEIPT
    if status == "executable_owner_action" or current_action:
        if next_action and next_action.get("provider_admission_allowed") is False:
            return MATERIALIZE_OWNER_ACTION
        return START_PROVIDER_ATTEMPT
    if next_kind in _OWNER_ACTION_NEXT_KINDS:
        return MATERIALIZE_OWNER_ACTION
    return None


def _paper_policy_verdict(policy_kind: str) -> dict[str, Any]:
    if policy_kind == START_PROVIDER_ATTEMPT:
        return {
            "verdict": "opl_provider_attempt_allowed_by_domain_policy",
            "provider_completion_is_domain_completion": False,
        }
    if policy_kind == MATERIALIZE_OWNER_ACTION:
        return {
            "verdict": "mas_owner_callable_required",
            "provider_admission_allowed": False,
        }
    if policy_kind == CONSUME_OWNER_RECEIPT:
        return {"verdict": "mas_owner_receipt_consumption_required"}
    if policy_kind == RECORD_TYPED_BLOCKER:
        return {"verdict": "stable_typed_blocker_required"}
    return {"verdict": "non_advancing_apply_requires_typed_blocker"}


def _opl_domain_progress_command(*, policy_kind: str, identity: Mapping[str, Any]) -> dict[str, Any]:
    study_id = _text(identity.get("study_id"))
    work_unit_id = _text(identity.get("work_unit_id"))
    fingerprint = _text(identity.get("work_unit_fingerprint"))
    source_generation = _text(identity.get("source_generation")) or fingerprint
    command = {
        "surface_kind": "opl_domain_progress_transition_command",
        "runtime_owner": "one-person-lab",
        "transition_kind": policy_kind,
        "aggregate_identity": {
            "aggregate_kind": "study_work_unit",
            "aggregate_id": "::".join(item for item in [study_id, work_unit_id] if item),
            "study_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
        "action_type": identity.get("action_type"),
        "next_owner": identity.get("owner"),
        "idempotency_key": _stable_id("paper-policy-command", [policy_kind, identity]),
        "source_generation": source_generation,
        "expected_version": source_generation,
        "postcondition": {
            "kind": _postcondition_kind(policy_kind),
            "outcome_owner": "one-person-lab",
            "domain_state_owner": "med-autoscience",
        },
        "domain_policy_result_ref": _stable_id("paper-policy", [policy_kind, identity]),
    }
    return _clean(command)


def _postcondition_kind(policy_kind: str) -> str:
    if policy_kind == START_PROVIDER_ATTEMPT:
        return "provider_admission_enqueued_or_blocked"
    if policy_kind == MATERIALIZE_OWNER_ACTION:
        return "owner_action_ref"
    if policy_kind == CONSUME_OWNER_RECEIPT:
        return "owner_receipt_consumed"
    if policy_kind == RECORD_TYPED_BLOCKER:
        return "typed_blocker_ref"
    return "non_advancing_apply_typed_blocker_ref"


def _identity(
    *,
    payload: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
    recovery: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    successor = _mapping(next_action.get("successor_owner_action"))
    source_generation = _first_text(
        _mapping(current_work_unit.get("currentness_basis")).get("truth_epoch"),
        _mapping(current_action.get("owner_route_currentness_basis")).get("truth_epoch"),
        _mapping(current_action.get("currentness_basis")).get("truth_epoch"),
        current_action.get("source_eval_id"),
    )
    return _clean(
        {
            "study_id": _first_text(payload.get("study_id"), recovery.get("study_id")),
            "quest_id": _first_text(payload.get("quest_id"), recovery.get("quest_id")),
            "owner": _first_text(
                successor.get("owner"),
                next_action.get("owner"),
                current_action.get("next_owner"),
                current_action.get("owner"),
                current_work_unit.get("owner"),
            ),
            "action_type": _first_text(
                successor.get("action_type"),
                next_action.get("action_type"),
                current_action.get("action_type"),
                current_work_unit.get("action_type"),
            ),
            "work_unit_id": _first_text(
                successor.get("work_unit_id"),
                next_action.get("work_unit_id"),
                current_action.get("work_unit_id"),
                current_work_unit.get("work_unit_id"),
            ),
            "work_unit_fingerprint": _first_text(
                successor.get("work_unit_fingerprint"),
                next_action.get("work_unit_fingerprint"),
                current_action.get("work_unit_fingerprint"),
                current_action.get("action_fingerprint"),
                current_work_unit.get("work_unit_fingerprint"),
                current_work_unit.get("action_fingerprint"),
            ),
            "source_generation": source_generation,
        }
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


def _stable_id(prefix: str, parts: object) -> str:
    digest = hashlib.sha256(
        json.dumps(parts, ensure_ascii=True, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    return f"{prefix}:{digest}"


def _clean(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}
